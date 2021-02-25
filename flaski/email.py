from threading import Thread
from flask import render_template
from flaski import app
from flask_mail import Message
from flaski import mail
from werkzeug.utils import secure_filename
import io

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body, reply_to, attachment=None, attachment_path=None, attachment_type=None, open_type="rb"):
    msg = Message(subject, sender=sender, recipients=recipients, reply_to = reply_to)
    msg.body = text_body
    msg.html = html_body
    if attachment:
        with open(attachment_path, open_type) as f: 
            msg.attach(
                secure_filename(attachment.filename),
                attachment_type,
                f.read() )
        
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

# def send_submission_email(user,submission_type,submission_file):
#     with app.app_context():
#         send_email('[Flaski][Automation][{submission_type}] Files have been submited for analysis.'.format(submission_type=submission_type),
#                 sender=app.config['MAIL_USERNAME'],
#                 recipients=[user.email, 'jboucas@age.mpg.de' ], 
#                 text_body=render_template('email/submissions.txt',
#                                             user=user, submission_type=submission_type),
#                 html_body=render_template('email/submissions.html',
#                                             user=user, submission_type=submission_type),\
#                 reply_to='bioinformatics@age.mpg.de',\
#                 attatchment=submission_file   )


def send_submission_email(user,submission_type,submission_file, attachment_path,open_type="rb",attachment_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
    with app.app_context():
        send_email('[Flaski][Automation][{submission_type}] Files have been submited for analysis.'.format(submission_type=submission_type),
                sender=app.config['MAIL_USERNAME'],
                recipients=[user.email, 'automation@age.mpg.de' ], 
                text_body=render_template('email/submissions.txt',
                                            user=user, submission_type=submission_type, attachment_path=attachment_path),
                html_body=render_template('email/submissions.html',
                                            user=user, submission_type=submission_type, attachment_path=attachment_path),\
                reply_to='bioinformatics@age.mpg.de',\
                attachment=submission_file ,
                attachment_path=attachment_path ,\
                open_type=open_type,\
                attachment_type=attachment_type)