from flask import render_template, url_for, flash, redirect, session, request
from llm_app.db_models import User, Annotation, Image
from llm_app.forms import RegistrationForm, AnnotationForm, LoginForm, NASATLXForm
from llm_app import app, db
from flask_login import login_user, current_user, logout_user, login_required
from time import time
from llm_app.ml_models import get_inference

import random
import os

@app.route("/")
@app.route("/registration", methods=["GET", "POST"])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for("redirect_to_annotator"))
    form = RegistrationForm()
    if request.method == "POST" and form.validate_on_submit():
        # create a new user
        user = User(name = form.name.data,
                    age = form.age.data,
                    email = form.email.data)

        db.session.add(user)
        db.session.commit()

        flash(f"Account created for {form.name.data}!", "success")
        return redirect(url_for("login"))
    return render_template("register.html", title="Registration", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated: 
        return redirect(url_for("redirect_to_annotator"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and user.age == form.age.data:
            login_user(user)

            # vlm pages and dataset data associated with current user session
            vlm_pages_list = ["no_help", "clarifai", "clarifai_gpt", "blip2"]
            dataset_list = ["dataset1", "dataset2", "dataset3", "dataset4"]
            random.shuffle(vlm_pages_list)
            random.shuffle(dataset_list)

            session["vlm_pages_list"] = vlm_pages_list
            session["dataset_list"] = dataset_list
            session["vlm_index"] = 0
            session["dataset_index"] = 0

            flash("You have been logged in!", "success")
            return redirect(url_for("welcome"))
        else:
            flash("Login unsuccessful. Please check email and age.", "danger")
    return render_template("login.html", title="Login", form=form)

@app.route("/welcome", methods = ["GET", "POST"])
def welcome():
    if request.method == "POST":
        return redirect(url_for("redirect_to_annotator"))
    return render_template("welcome.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/finished")
@login_required
def finished():
    return render_template("finished.html")

@app.route("/nasa_tlx", methods=["GET", "POST"])
@login_required
def nasa_tlx():
    form = NASATLXForm()
    if request.method == "POST":
        if form.validate_on_submit():
            annotation_id = session.get("current_annotation_id")

            Annotation.query.filter_by(id = annotation_id).update({"mental_demand": form.mental_demand.data,
                        "physical_demand": form.physical_demand.data,
                        "temporal_demand": form.temporal_demand.data,
                        "performance": form.performance.data,
                        "effort": form.effort.data,
                        "frustration": form.frustration.data})

            db.session.commit()
            return redirect(url_for("redirect_to_annotator"))
    return render_template("nasa_tlx.html", form = form)


@app.route("/redirect_to_annotator")
@login_required
def redirect_to_annotator():

    vlm_pages_list = session.get("vlm_pages_list")
    dataset_list = session.get("dataset_list")

    if session.get("vlm_index") >= len(vlm_pages_list):
        return redirect(url_for("finished"))

    # choose the vlm and dataset for this annotation
    vlm_page = vlm_pages_list[session.get("vlm_index")]
    dataset = dataset_list[session.get("dataset_index")]

    # increment the vlm and dataset index
    session["vlm_index"] = session.get("vlm_index") + 1 
    session["dataset_index"] = session.get("dataset_index") + 1 

    # add the annotation entity to the database
    annotation = Annotation(name = vlm_page,
                            dataset_name = dataset,
                            user_id = current_user.id)
    db.session.add(annotation)
    db.session.commit()

    session["image_counter"] = 0
    session["current_annotation_id"] = annotation.id
    return redirect(url_for("annotation_page", vlm_page = vlm_page))

@app.route("/annotation_page/<vlm_page>", methods=["GET", "POST"])
@login_required
def annotation_page(vlm_page):
    n_images = 100 # number of images

    # get data from current annotation
    current_annotation_id = session.get("current_annotation_id")
    dataset_name = Annotation.query.with_entities(Annotation.dataset_name).filter_by(id = current_annotation_id).scalar()

    test_dir_name = "test_images" #CHANGE THIS TO TOGGLE BETWEEN TEST AND ACTUAL DATASET
    image_dir = f"./llm_app/static/{test_dir_name}/{dataset_name}/"
    p_id_fname_list = []# string with p_id/fname
    for root, _, files in os.walk(image_dir):
        for f in files:
            p_id_fname_list.append(os.path.join(root[-4:], f)) # [-4:] gets just the p_id

    if session.get("image_counter") < len(p_id_fname_list):
        
        p_id_fname = p_id_fname_list[session.get("image_counter")]
        p_id, frame_num = p_id_fname.split("/")
        frame_num = frame_num.split(".")[0] # remove the extension
        form = AnnotationForm()
        image_file = url_for("static", filename = f"{test_dir_name}/{dataset_name}/{p_id_fname}")
        
        # suggestions from the vlm
        suggestions = ["None"]

        if vlm_page != "no_help":
            suggestions.extend(get_inference(p_id, int(frame_num), vlm_page))


        form.activity.choices = AnnotationForm.convert_to_choices(suggestions)

        if request.method == "POST":
            if form.validate_on_submit():
                session["end_time"] = time()
                activity = form.activity.data if form.activity.data else ""
                image_annotation = Image(name = p_id_fname,
                                    start_time = session.get("start_time"),
                                    end_time = session.get("end_time"),
                                    activity = form.activity.data,
                                    text_in_other_box = form.other_activity.data,
                                    annotation_id = current_annotation_id)

                db.session.add(image_annotation)
                db.session.commit()
                flash(f"Image annotation submitted for {p_id_fname}!", "success")
                session["image_counter"] = session.get("image_counter") + 1 # increment image index to get new image
            else:
                flash("Please either select from the options or type in the other box. Do not leave both empty or both filled.", "danger")
        
        session["start_time"] = time()
        return render_template(f"annotation_page.html", 
                            title = f"Annotation with {vlm_page}", 
                            image_file = image_file,
                            suggestions = suggestions,
                            num = session.get("vlm_index"),
                            form = form)

    return redirect(url_for("nasa_tlx"))
