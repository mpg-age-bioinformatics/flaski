import pandas as pd
from flask import session
import json
from werkzeug.utils import secure_filename
from fuzzywuzzy import process
import io
from flaski import db
from flask_login import current_user
from flaski.models import UserLogging



def fuzzy_search(query_value,available_values):
    x=query_value.split(",")
    x=" ".join(x)
    x=x.split(" ")
    x=[s for s in x if len(s) > 0 ]
    x.sort()
    found_values=[ s for s in x if s in available_values ]
    not_found_values=[ s for s in x if s not in found_values ]
    best_matches={}
    for not_found in not_found_values:
        if "*" in not_found:
            not_found_=not_found.split("*")[0]
            best_match=[ s for s in available_values if s.startswith(not_found_) ]
            found_values=found_values+best_match
        else:
            #best_match=process.extractOne(gene_name,available_gene_names)[0]
            best_match=process.extract(not_found,available_values)
            if not_found.lower() == best_match[0][0].lower():
                found_values.append(best_match[0][0])
            else:
                best_match=best_match[:3]
                best_match=[ s[0] for s in best_match ]
                best_matches[not_found]=", ".join(best_match)
    if len(list(best_matches.keys())) > 0:
        emsg="The folowing values could not be found. Please consider the respective options: "
        for missing in list(best_matches.keys()):
            emsg=emsg+missing+": "+best_matches[missing]+"; "
        emsg=emsg[:-2]+"."
    else:
        emsg=None
    return found_values, emsg

ALLOWED_EXTENSIONS=["xlsx","tsv","csv"]
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_tables(inputfile,session_key="df", file_field="filename"):
    filename=secure_filename(inputfile.filename)
    session[file_field]=filename
    fileread = inputfile.read()
    filestream=io.BytesIO(fileread)
    extension=filename.rsplit('.', 1)[1].lower()
    if extension == "xlsx":
        df=pd.read_excel(filestream)
    elif extension == "csv":
        df=pd.read_csv(filestream)
    elif extension == "tsv":
        df=pd.read_csv(filestream,sep="\t")

    df=df.astype(str)
    session[session_key]=df.to_json()

    return df

def read_request(request):
    plot_arguments=session["plot_arguments"]
    checkboxes=[ s for s in list(plot_arguments.keys()) if plot_arguments[s] in [".on",".off","on","off" ] ]
    for a in list(plot_arguments.keys()):
        if a in list(request.form.keys()):
            if type(plot_arguments[a]) == list :
                plot_arguments[a]=request.form.getlist(a)
            elif a in checkboxes:
                plot_arguments[a]="on"
            else:
                plot_arguments[a]=request.form[a]
        elif a in checkboxes:
            if plot_arguments[a]==".on":
                plot_arguments[a]="on"
            else:
                plot_arguments[a]="off"

    session["plot_arguments"]=plot_arguments
    return plot_arguments

def handle_exception(e, user, eapp, session):
    import traceback
    from flaski.email import send_exception_email
    from datetime import datetime
    tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
    send_exception_email( user=user, eapp=eapp, emsg=tb_str, etime=str(datetime.now()) )
    session["traceback"]=tb_str
    tb_str=text2html(tb_str)
    return tb_str

def text2html(s):
    h=s.replace("\n","<br>").replace("    ","&emsp;").replace(" ","&nbsp;")
    return h  

def reset_all(session):
    MINIMAL=['_permanent', '_fresh', 'csrf_token', 'user_id', '_id', 'PRIVATE_APPS']
    for k in list(session.keys()):
        if k not in MINIMAL:
            del(session[k])

def check_session_app(session,app,apps):
    if "app" not in list(session.keys()):
        eventlog = UserLogging(email=current_user.email, action="visit %s" %app)
        db.session.add(eventlog)
        db.session.commit()
        if "session_file" in list(session.keys()):
            del(session["session_file"])
        message="Could not find data for this App in your current session. Session has been reset."
        return message
    elif session["app"] == app :
        return None
    else:
        appName=[ s for s in apps if s["link"] == session["app"] ][0]["name"]
        eventlog = UserLogging(email=current_user.email, action="visit %s" %app)
        db.session.add(eventlog)
        db.session.commit()
        if "session_file" in list(session.keys()):
            del(session["session_file"])
        message="Returning from '%s'. Your '%s' session has been reset."  %(appName,appName)
            #Flaski is not yet made for working with multiple Apps nor data simultaneously on one single browser. \
            #If you wish to use multiple Apps or data simultaneously please use one App/data per web browser eg. Safari + Chrome. \
            #Your %s session has been reset."
        reset_all(session)
        return message

def session_to_file(session,file_type):
    session_={}
    for k in list(session.keys()):
        if k not in ['_permanent','fileread','_flashes',"width","height","csrf_token","user_id","_fresh","available_disk_space","_id","private_apps"]:
            session_[k]=session[k]
    if file_type=="ses":
        session_["ftype"]="session"
    elif file_type=="arg":
        if session_["app"] == "david":
            for k in ["ids","ids_bg"]:
                del(session_["plot_arguments"][k])
            for k in ["david_df","report_stats"]:
                del(session_[k])
        session_["ftype"]="arguments"
        if "df" in list(session_.keys()):
            del(session_["df"])
    return session_

def read_private_apps(useremail,app):
    PRIVATE_APPS=[]
    if app.config['PRIVATE_APPS']:
        df=pd.read_csv(app.config['PRIVATE_APPS'],index_col="app",sep="\t")
        df=df.transpose()
        dic=df.to_dict()
        for entry in list(dic.keys()):
            private_app=dic[entry]
            allowed=private_app["allowed"].split(",")
            if "all" in allowed:
                del(private_app["allowed"])
                PRIVATE_APPS.append(private_app)
            elif useremail in allowed:
                del(private_app["allowed"])
                PRIVATE_APPS.append(private_app)
            elif len([ s for s in allowed if s[0] == "#" ]) > 0 :
                for domain in [ s for s in allowed if s[0] == "#" ]:
                    if domain[1:] in useremail:
                        del(private_app["allowed"])
                        PRIVATE_APPS.append(private_app)
                        break
    return PRIVATE_APPS

def read_argument_file(inputargumentsfile,appName):
    if inputargumentsfile.filename.rsplit('.', 1)[1].lower() != "arg"  :
        error_msg="The file you have uploaded is not a arguments file. Please make sure you upload a session file with the correct `arg` extension."
        return error_msg, session["plot_arguments"], True

    session_=json.load(inputargumentsfile)
    if session_["ftype"]!="arguments":
        error_msg="The file you have uploaded is not an arguments file. Please make sure you upload an arguments file."
        return error_msg, session["plot_arguments"], True

    if session_["app"]!=appName:
        error_msg="The file was not loaded as it is associated with the '%s' and not with this app." %session_["app"]
        return error_msg, session["plot_arguments"], True

    del(session_["ftype"])
    del(session_["COMMIT"])
    for k in list(session_.keys()):
        session[k]=session_[k]
    plot_arguments=session["plot_arguments"]
    msg='Arguments file successfully read.'
    return msg, plot_arguments, False


def read_session_file(inputsessionfile,appName):
    if inputsessionfile.filename.rsplit('.', 1)[1].lower() != "ses"  :
        error_msg="The file you have uploaded is not a session file. Please make sure you upload a session file with the correct `ses` extension."
        return error_msg, session["plot_arguments"], True

    session_=json.load(inputsessionfile)
    if session_["ftype"]!="session":
        error_msg="The file you have uploaded is not a session file. Please make sure you upload a session file."
        return error_msg, session["plot_arguments"], True

    if session_["app"]!=appName:
        error_msg="The file was not load as it is associated with the '%s' and not with this app." %session_["app"]
        return error_msg, session["plot_arguments"], True

    del(session_["ftype"])
    del(session_["COMMIT"])
    for k in list(session_.keys()):
        session[k]=session_[k]
    plot_arguments=session["plot_arguments"]
    msg="Session file successfully read."
    return msg, plot_arguments, False
