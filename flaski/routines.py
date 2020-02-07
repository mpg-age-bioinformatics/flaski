def session_to_file(session,file_type):
    session_={}
    for k in list(session.keys()):
        if k not in ['_permanent','fileread','_flashes',"width","height","csrf_token","user_id","_fresh","available_disk_space","_id","private_apps"]:
            session_[k]=session[k]
    if file_type=="ses":
        session_["ftype"]="session"
    elif file_type=="arg":
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
