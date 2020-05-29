import pandas as pd
from flask import session

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
        message="Could not find data for this App in your current session. Session has been reset."
        return message
    elif session["app"] == app :
        return None
    else:
        appName=[ s for s in apps if s["link"] == session["app"] ][0]["name"]
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
    del(session_["APPS"])
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
    del(session_["APPS"])
    for k in list(session_.keys()):
        session[k]=session_[k]
    plot_arguments=session["plot_arguments"]
    msg="Session file successfully read."
    return msg, plot_arguments, False