from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flaski.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()], render_kw={'class': 'form-control form-control-user', "placeholder": "Enter Email Address..." })
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'class': 'form-control form-control-user' , "placeholder": "Password"})
    remember_me = BooleanField('Remember Me', render_kw={'class': "custom-control-input" })
    submit = SubmitField('Sign In', render_kw={'class':"btn btn-primary btn-user btn-block"})

class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()],  render_kw={'class':"form-control form-control-user" ,'placeholder':"First Name"})
    lastname = StringField('Last Name', validators=[DataRequired()], render_kw={'class':"form-control form-control-user" ,'placeholder':"Last Name"})
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={'class':"form-control form-control-user" ,'placeholder':"Email Address"})
    organization = StringField('Organization', validators=[DataRequired()], render_kw={'class':"form-control form-control-user" ,'placeholder':"Organization"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'class':"form-control form-control-user" ,'placeholder':"Password"})
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')],render_kw={'class':"form-control form-control-user" ,'placeholder':"Repeat Password"})
    submit = SubmitField('Register Account',render_kw={'class':"btn btn-primary btn-user btn-block"})

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
    
class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={'class':"form-control form-control-user" ,'placeholder':"Enter Email Address..."})
    submit = SubmitField('Request Password Reset',render_kw={'class':"btn btn-primary btn-user btn-block"})

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'class':"form-control form-control-user" ,'placeholder':"Password"})
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')],\
            render_kw={'class':"form-control form-control-user" ,'placeholder':"Password"})
    submit = SubmitField('Reset Password',render_kw={'class':"btn btn-primary btn-user btn-block"})