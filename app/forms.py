from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()], render_kw={'class': 'form-control form-control-user', "placeholder": "Enter Email Address..." })
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'class': 'form-control form-control-user' , "placeholder": "Password"})
    remember_me = BooleanField('Remember Me', render_kw={'class': "custom-control-input" })
    submit = SubmitField('Sign In', render_kw={'class':"btn btn-primary btn-user btn-block"})