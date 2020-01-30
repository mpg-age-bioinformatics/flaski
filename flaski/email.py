from threading import Thread
from flask import render_template
from flaski import app
from flask_mail import Message
from flaski import mail

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[Flaski] Reset Your Password',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))

def send_validate_email(user):
    token = user.get_email_validation_token()
    send_email('Welcome to Flaski!',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/validate_email.txt',
                                         user=user, token=token),
               html_body=render_template('email/validate_email.html',
                                         user=user, token=token))