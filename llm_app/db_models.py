from llm_app import db, login_manager
from datetime import datetime
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable = False)
    age = db.Column(db.Integer, nullable = False)
    email = db.Column(db.String(120), unique=True, nullable = False)
    annotations = db.relationship("Annotation", backref= "annotator", lazy = True)

    def __repr__(self):
        return f"User('{self.name}') # 'numb of annotations done: {len(self.annotations)}"

class Annotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable = False)
    dataset_name = db.Column(db.String(20), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    images = db.relationship("Image", backref= "annotation_container", lazy = True)

    def __repr__(self):
        return f"Annotation('{self.name}') # 'numb of images annotated: {len(self.images)})"

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable = False) # path of the image
    start_time = db.Column(db.Float, nullable = False)
    end_time = db.Column(db.Float, nullable = False)
    activity = db.Column(db.String(20), nullable = False, default = "")
    text_in_other_box = db.Column(db.String(20), default = "") # is true if the user does not choose any option given by the VLM
    annotation_id = db.Column(db.Integer, db.ForeignKey("annotation.id"), nullable = False)  