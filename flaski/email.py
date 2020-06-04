from threading import Thread
from flask import render_template
from flaski import app
from flask_mail import Message
from flaski import mail

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body, reply_to):
    msg = Message(subject, sender=sender, recipients=recipients, reply_to = reply_to)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[Flaski] Reset Your Password',
               sender=app.config['MAIL_USERNAME'],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token),\
               reply_to=app.config['MAIL_USERNAME'] )

def send_validate_email(user):
    token = user.get_email_validation_token()
    send_email('Welcome to Flaski!',
               sender=app.config['MAIL_USERNAME'],
               recipients=[user.email],
               text_body=render_template('email/validate_email.txt',
                                         user=user, token=token),
               html_body=render_template('email/validate_email.html',
                                         user=user, token=token),\
               reply_to=app.config['MAIL_USERNAME'] )

    send_email('[Flaski] New user registration',
            sender=app.config['MAIL_USERNAME'],
            recipients=app.config['ADMINS'],
            text_body=render_template('email/new_user.txt',
                                        user=user),
            html_body=render_template('email/new_user.html',
                                        user=user),\
            reply_to=app.config['MAIL_USERNAME'] )


def send_files_deletion_email(user,files):
    with app.app_context():
        send_email('[Flaski] Files deletion warning',
                sender=app.config['MAIL_USERNAME'],
                recipients=[user.email],
                text_body=render_template('email/files_deletion.txt',
                                            user=user, files=files),
                html_body=render_template('email/files_deletion.html',
                                            user=user, files=files),\
               reply_to=app.config['MAIL_USERNAME'] )

def send_exception_email(user,eapp,emsg,etime):
    with app.app_context():
        emsg_html=emsg.split("\n")
        send_email('[Flaski] exception: %s ' %eapp,
                sender=app.config['MAIL_USERNAME'],
                recipients=app.config['ADMINS'],
                text_body=render_template('email/app_exception.txt',
                                            user=user, eapp=eapp, emsg=emsg, etime=etime),
                html_body=render_template('email/app_exception.html',
                                            user=user, eapp=eapp, emsg=emsg_html, etime=etime),\
                reply_to=user.email )

def send_help_email(user,eapp,emsg,etime,session_file):
    with app.app_context():
        emsg_html=emsg.split("\n")
        send_email('[Flaski] help needed: %s ' %eapp,
                sender=app.config['MAIL_USERNAME'],
                recipients=app.config['ADMINS'],
                text_body=render_template('email/app_help.txt',
                                            user=user, eapp=eapp, emsg=emsg, etime=etime, session_file=session_file),
                html_body=render_template('email/app_help.html',
                                            user=user, eapp=eapp, emsg=emsg_html, etime=etime, session_file=session_file),\
                reply_to=user.email )                                   
