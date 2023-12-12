import pandas as pd

def get_inference(p_id, frame_num, model_name):
    inf_data = pd.read_csv("llm_app/static/inference.csv", low_memory=False)
    sub_sample = inf_data.loc[(inf_data["Video UUID"] == p_id) & (inf_data["Timestamp_frame"] == frame_num)]
    return_list = []

    i = 1
    if model_name.lower() == "blip2":
        col_name_fn = lambda i: f'Predicted activity {i} from blip2 for activity_recognition'
        i = 0
    elif model_name.lower() == "clarifai_gpt":
        col_name_fn = lambda i: f'Predicted activity {i} from clarifai-llm for activity_recognition'
    elif model_name.lower() == "clarifai":
        col_name_fn = lambda i: f"Predicted activity {i} from clarifai-llm for object_detection"

    while col_name_fn(i) in inf_data.columns:
        # if len(sub_sample[col_name_fn(i)].values) == 0: import pdb; pdb.set_trace()
        activity_name = sub_sample[col_name_fn(i)].values[0]
        if str(activity_name) != "nan" and str(activity_name) != "":
            return_list.append(activity_name)
        i += 1
    
    return return_list