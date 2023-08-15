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
    activity = RadioField("Activity", validators=[DataRequired()])
    other_activity = StringField("Other Activity", validators=[Optional()])
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

class NASATLXForm(FlaskForm):
    """Survey for the NASA TLX"""
    # scale from 1 to 21
    choices = [
        ('1', 'Very Low: 1'), 
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
        ('13', '13'),
        ('14', '14'),
        ('15', '15'),
        ('16', '16'),
        ('17', '17'),
        ('18', '18'),
        ('19', '19'),
        ('20', '20'),
        ('21', 'Very High: 21')
    ]
    mental_demand = RadioField("Mental Demand", choices=choices, validators=[DataRequired()])
    physical_demand = RadioField("Physical Demand", choices=choices, validators=[DataRequired()])
    temporal_demand = RadioField("Temporal Demand", choices=choices, validators=[DataRequired()])
    performance = RadioField("Performance", choices=choices, validators=[DataRequired()])
    effort = RadioField("Effort", choices=choices, validators=[DataRequired()])
    frustration = RadioField("Frustration", choices=choices, validators=[DataRequired()])
    submit = SubmitField("Submit")
