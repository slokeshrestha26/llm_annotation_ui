from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, ValidationError, Optional
from llm_app.db_models import User


class RegistrationForm(FlaskForm):
    name = StringField('Name',
                           validators=[DataRequired(),
                                       Length(min=2, max=20)])


    email = StringField('Email',
                        validators=[DataRequired(),
                                    Email()])

    age = IntegerField("Age",
                       validators=[DataRequired(),
                                   NumberRange(min=18)])

    
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(f"User name, {email.data}, is already taken. Please choose a different one.")

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(),
                                    Email()])
    age = IntegerField("Age",
                        validators=[DataRequired(),
                                    NumberRange(min=18)])
    submit = SubmitField('Login')



class AnnotationForm(FlaskForm):
    """Form for annotation of one image"""
    # Choices for the radio buttons
    activity_choices = [
        ('option1', 'Option 1'),
        ('option2', 'Option 2'),
        ('option3', 'Option 3'),
        ('None', 'None of the above')
    ]

    activity = RadioField("Activity", choices=activity_choices, validators=[DataRequired()])
    other_activity = StringField("Other Activity", validators=[Optional()])
    image_name = StringField("Image Name", validators=[Optional()])
    submit = SubmitField("Submit")

    # Custom validator to make sure one of the activity or other_activity is filled
    def validate_activity(self, activity):
        if activity.data == "None":
            bool_activity = False
        else:
            bool_activity = bool(self.activity.data)
        bool_other_activity = bool(self.other_activity.data)
        if bool_activity == bool_other_activity:
            raise ValidationError("Please choose one of the options or fill in the Other Activity field.")

    def validate_other_activity(self, other_activity):
        if self.activity.data == "None":
            bool_activity = False
        else:
            bool_activity = bool(self.activity.data)
        bool_other_activity = bool(self.other_activity.data)
        if bool_activity == bool_other_activity:
            raise ValidationError("Please choose one of the options or fill in the Other Activity field.")

    @staticmethod
    def convert_to_choices(choices_list):
        """Converts a list of strings to a list of tuples for use in a RadioField"""
        return [(choice, choice) for choice in choices_list]