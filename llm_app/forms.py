from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, RadioField
from wtforms.validators import DataRequired, Length, Email, NumberRange, ValidationError, Optional
from llm_app.db_models import User


class RegistrationForm(FlaskForm):
    pid = StringField('PID', validators=[DataRequired(),
                                       Length(min=2, max=5)])
    
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    pid = StringField('PID', validators=[DataRequired(),
                                       Length(min=2, max=5)])
    
    submit = SubmitField('Login')


class XOR(object):
    def __init__(self, field2_name, message = None):
        self.message = message
        self.field2_name = field2_name

    def __call__(self, form, field):
        field2 = form[self.field2_name]
        if not self.is_valid(field.data, field2.data):
            raise ValidationError(self.message or 'Validation failed')
        
    def is_valid(self, data1, data2):
        return bool(data1) ^ bool(data2)
    
class AnnotationForm(FlaskForm):
    """Form for annotation of one image"""
    activity = RadioField("Activity", validators = [XOR("other_activity"), Optional()])
    other_activity = StringField("Other Activity", validators = [XOR("activity"), Optional()])
    submit = SubmitField("Submit")

    # Custom validator to make sure one of the activity or other_activity is filled
    def validate_activity(self, activity):
        bool_activity = bool(self.activity.data)
        bool_other_activity = bool(self.other_activity.data)
        print(bool_activity, bool_other_activity)
        if not (bool_activity ^ bool_other_activity):
            raise ValidationError("Please choose one of the options or fill in the Other Activity field.")

    @staticmethod
    def convert_to_choices(choices_list):
        """Converts a list of strings to a list of tuples for use in a RadioField"""
        return [(choice, choice) for choice in choices_list]
    