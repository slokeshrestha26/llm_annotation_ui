import torch
from PIL import Image
import time
import os
import numpy as np


from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2


from lavis.models import load_model_and_preprocess

from transformers import YolosForObjectDetection, YolosImageProcessor
import openai
import tiktoken

os.environ["CUDA_VISIBLE_DEVICES"] = "1"
openai.api_key = "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"

DISP_RPM = False

class VLM():
    """Class that encasulates the vision and language that communicates with each other to get inferred activity from egocentric images
    """
    def __init__(self) -> None:
        self.device = torch.device("cuda:1") if torch.cuda.is_available() else "cpu"
        self.model = None
        self.model_name = None


    def get_activity(self):
        pass

class BLIP2(VLM):
    """BLIP-2 wrapper to get activity from an image"""
    
    def __init__(self, device = "cuda:0") -> None:
        super().__init__()
        print("Loading BLIP-2 model...", end = " ")
        self.model_name = "blip2"
        # loads BLIP-2 pre-trained model
        self.model, self.vis_processors, _ = load_model_and_preprocess(name="blip2_opt", model_type="pretrain_opt2.7b", is_eval=True, device= self.device)
        print("done!")

    def get_activity(self, im_dat = None,
                    question = "What is the person doing?"):
        # prepare the image
        image = self.vis_processors["eval"](im_dat).unsqueeze(0).to(self.device)
        # generate the activity
        activity = self.model.generate({"image": image, "prompt": "{} Answer:".format(question)},  min_length = 2, num_captions = 5) # changing parameters here

        return activity
    
class YOLOS_LLM(VLM):
    """Wrapper to interface YOLOS object detector and an LLM to get activity from an image"""
    prompt = lambda x: """You are a picture annotator. A list of picture concepts that can be seen in a picture is given as a python list. You will list top five guesses for what a person might be doing in the picture based on the list of concepts.
                            Be sure to list activities in lemmatized form. List the activities as a python list.

                            Follow the examples below:  
                                                        
                            list of concepts = ["people", "food", "tableware", "flatware", "cutlery", "indoors", "furniture", "knife", "container", "cook", "serve food", ]
                            activities = ["eat", "prepare food", "serve food", "cook", "]

                            list of concepts = ["car", "drive", "automotive", "vehicle", "dashboard", "car", "drive"]
                            activities = ["drive", "commute", "steer", "run errand", "joyride"]

                            list of concepts = {}
                            activities = 

                            """.format(x)
    
    def __init__(self) -> None:
        super().__init__()
        self.model_name = "yolos-llm"
        self.model = YolosForObjectDetection.from_pretrained('hustvl/yolos-tiny')
        self.image_processor = YolosImageProcessor.from_pretrained("hustvl/yolos-tiny")

        # tell the LLM to give the list as a list in python


    def get_completion(self,prompt, model = "gpt-3.5-turbo"):
        """Get completion from the model"""
        messages = [{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
            )
        return response.choices[0].message["content"]

    def get_activity(self, raw_image):
        """NOTE: prompt must be a function with one argument that returns a string"""
        # get list of objects
        objects = self.get_objects_list(raw_image)
        obj_str = objects.__str__().replace("'", '"') # replace single quotes with double quotes in the list str

        prompt = YOLOS_LLM.prompt(obj_str)

        # get the completion from the LLM
        while True:
            activities = None
            try:
                activities =  self.get_completion(prompt)
            except Exception as e:
                # sleep for 5 seconds and try again
                print("Error: {}".format(e))
                print("Sleeping for 5 seconds and trying again...")
                time.sleep(5)
            if activities:
                break

        if ", " not in activities: Warning(" ', ' not found in the LLM's completion. LLM's output: {}".format(activities))
        try:
            activities =  eval(activities)
        except:
            Warning("LLM couldn't predict the activity. The LLMS's output: ```{}```".format(activity))
            activities = []
        return activities



    
    def get_objects_list(self, raw_image):
        """Get list of objects from an image using YOLOS object detector
        raw_image = PIL.Image object"""

        inputs = self.image_processor(images=raw_image, return_tensors="pt")
        outputs = self.model(**inputs)
        target_sizes = torch.tensor([raw_image.size[::-1]])
        results = self.image_processor.post_process_object_detection(outputs, threshold=0.8, target_sizes=target_sizes)[0]

        id2labelfunc = lambda x: self.model.config.id2label[x]
        objects = np.vectorize(id2labelfunc)(results["labels"])

        return objects

class Clarifai_LLM(YOLOS_LLM):
    def __init__(self) -> None:

        self.__PAT = '03a38005bb28406a8245069231660b47'
        # Specify the correct user_id/app_id pairings
        # Since you're making inferences outside your app's scope
        self.__USER_ID = 'cx6c5sx3rjm1'
        self.__APP_ID = 'my-first-application'
        # Change these to whatever model and image URL you want to use
        self.__MODEL_ID = 'general-image-recognition'
        self.__MODEL_VERSION_ID = 'aa7f35c01e0642fda5cf400f543e7c40' 
        self.confidence_threshold = 0.90
        self.model_name = "clarifai-llm"
        self.counter = 0

        self.start_time = time.time()

        self.call_count_object_list = 0
        self.call_count_gpt3 = 0

    def get_image_obj(self, im_path):
        """Returns image as bytes"""
        with open(im_path, "rb") as f:
            file_bytes = f.read()
        
        return file_bytes

    def get_objects_list(self, raw_image):
        while True:
            try:
                return self.get_objects_list_util(raw_image)
            except Exception as e:
                print("Error: {}".format(e))
                print("Sleeping for 5 seconds and trying again...")
                time.sleep(5)    

    def get_objects_list_util(self, file_bytes):
        """Return the list of ojbects returned from Clarifai's object detector. The confidence score threshold is set to 0.90"""


        channel = ClarifaiChannel.get_grpc_channel()
        stub = service_pb2_grpc.V2Stub(channel)

        metadata = (('authorization', 'Key ' + self.__PAT),)

        userDataObject = resources_pb2.UserAppIDSet(user_id=self.__USER_ID, app_id=self.__APP_ID)

        post_model_outputs_response = stub.PostModelOutputs(
            service_pb2.PostModelOutputsRequest(
                user_app_id=userDataObject,  # The userDataObject is created in the overview and is required when using a PAT
                model_id=self.__MODEL_ID,
                version_id=self.__MODEL_VERSION_ID,  # This is optional. Defaults to the latest model version
                inputs=[
                    resources_pb2.Input(
                        data=resources_pb2.Data(
                            image=resources_pb2.Image(
                                base64=file_bytes
                            )
                        )
                    )
                ]
            ),
            metadata=metadata
        )
        if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
            print(post_model_outputs_response.status)
            raise Exception("Post model outputs failed, status: " + post_model_outputs_response.status.description)

        # Since we have one input, one output will exist here
        output = post_model_outputs_response.outputs[0]
        output = output.data.concepts

        self.call_count_object_list += 1
        elapsed_time = time.time() - self.start_time

        # Calculate the rate per minute
        rate_per_minute = self.call_count_object_list / (elapsed_time / 60)
        if DISP_RPM: print("Clarifai rpm: ", rate_per_minute)

        return [x.name for x in output if x.value >= self.confidence_threshold]
    
    def get_activity(self, im_path = None, object_list = None):
        """NOTE: prompt must be a function with one argument that returns a string"""
        assert im_path != object_list, "Either im_path or object_list must be provided"
        # get object list if not provided
        if im_path and object_list == None:
            im_bytes = self.get_image_obj(im_path)
            object_list = self.get_objects_list(im_bytes)

        obj_str = object_list.__str__().replace("'", '"') # replace single quotes with double quotes in the list str

        prompt = YOLOS_LLM.prompt(obj_str)

        while True:
            activities = None
            try:
                activities =  self.get_completion(prompt)
            except Exception as e:
                # sleep for 5 seconds and try again
                print("Error: {}".format(e))
                print("Sleeping for 15 seconds and trying again...")
                time.sleep(15)
            if activities:
                break

        if ", " not in activities: Warning(" ', ' not found in the LLM's completion. LLM's output: {}".format(activities))
        try:
            activities =  eval(activities)
        except:
            Warning("LLM couldn't predict the activity. The LLMS's output: ```{}```".format(activities))
            activities = []

        self.call_count_gpt3 += 1
        elapsed_time = time.time() - self.start_time

        # Calculate the rate per minute
        rate_per_minute = self.call_count_gpt3 / (elapsed_time / 60)
        if DISP_RPM: print("GPT3 rpm: ", rate_per_minute)

        return activities


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
  """Returns the number of tokens used by a list of messages."""
  try:
      encoding = tiktoken.encoding_for_model(model)
  except KeyError:
      encoding = tiktoken.get_encoding("cl100k_base")
  if model == "gpt-3.5-turbo-0613":  # note: future models may deviate from this
      num_tokens = 0
      for message in messages:
          num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
          for key, value in message.items():
              num_tokens += len(encoding.encode(value))
              if key == "name":  # if there's a name, the role is omitted
                  num_tokens += -1  # role is always required and always 1 token
      num_tokens += 2  # every reply is primed with <im_start>assistant
      return num_tokens
  else:
      raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
  See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    
def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens