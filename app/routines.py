def session_to_file(session,file_type):
    session_={}
    for k in list(session.keys()):
        if k not in ['_permanent','fileread','_flashes',"width","height","csrf_token","user_id","_fresh","available_disk_space","_id"]:
            session_[k]=session[k]
    if file_type=="ses":
        session_["ftype"]="arguments"
    elif file_type=="arg":
        session_["ftype"]="session"
        del(session_["df"])
    return session_
