from flask import Flask, make_response, request, session, render_template, send_file, Response, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from flask.views import MethodView
from werkzeug import secure_filename
from datetime import datetime
import humanize
import os
import re
import stat
import json
import mimetypes
import sys
from pathlib2 import Path
from copy import copy
import shutil
import io
from flaski.routes import FREEAPPS


from flaski.routines import session_to_file
from flaski import app, sess

# root = "/tmp/"

def cleanP(p):
    p=str(p)
    if len(p) > 0:
        bads=["..","\\","*","?","&","$","#","%"]
        for bad in bads:
            if bad in p:
                p=p.replace(bad,"")
        while p[0] in ["/","."]:
            p=p[1:]
    return p

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


def UserFolder(u):
    if u.is_authenticated:
        root = app.config['USERS_DATA']+str(u.id)
        if not os.path.isdir(root):
            os.makedirs(root)
    else:
        root=None
    return root

key = app.config["SECRET_KEY"]

ignored = ['.bzr', '$RECYCLE.BIN', '.DAV', '.DS_Store', '.git', '.hg', '.htaccess', '.htpasswd', '.Spotlight-V100', '.svn', '__MACOSX', 'ehthumbs.db', 'robots.txt', 'Thumbs.db', 'thumbs.tps']
datatypes = {'audio': 'm4a,mp3,oga,ogg,webma,wav', 'archive': '7z,zip,rar,gz,tar', 'image': 'gif,ico,jpe,jpeg,jpg,png,svg,webp', 'pdf': 'pdf', 'quicktime': '3g2,3gp,3gp2,3gpp,mov,qt', 'source': 'atom,bat,bash,c,cmd,coffee,css,hml,js,json,arg,ses,java,less,markdown,md,php,pl,py,rb,rss,sass,scpt,swift,scss,sh,xml,yml,plist', 'text': 'txt', 'video': 'mp4,m4v,ogv,webm', 'website': 'htm,html,mhtm,mhtml,xhtm,xhtml'}
icontypes = {'fa-music': 'm4a,mp3,oga,ogg,webma,wav', 'fa-archive': '7z,zip,rar,gz,tar', 'fa-picture-o': 'gif,ico,jpe,jpeg,jpg,png,svg,webp', 'fa-file-text': 'pdf', 'fa-film': '3g2,3gp,3gp2,3gpp,mov,qt', 'fa-code': 'atom,plist,bat,bash,c,cmd,coffee,css,hml,js,json,arg,ses,java,less,markdown,md,php,pl,py,rb,rss,sass,scpt,swift,scss,sh,xml,yml', 'fa-file-text-o': 'txt', 'fa-film': 'mp4,m4v,ogv,webm', 'fa-globe': 'htm,html,mhtm,mhtml,xhtm,xhtml'}

@app.template_filter('size_fmt')
@login_required
def size_fmt(size):
    return humanize.naturalsize(size)

@app.template_filter('time_fmt')
@login_required
def time_desc(timestamp):
    mdate = datetime.fromtimestamp(timestamp)
    str = mdate.strftime('%Y-%m-%d %H:%M:%S')
    return str

@app.template_filter('data_fmt')
@login_required
def data_fmt(filename):
    t = 'unknown'
    for type, exts in datatypes.items():
        if filename.split('.')[-1] in exts:
            t = type
    return t

@app.template_filter('icon_fmt')
@login_required
def icon_fmt(filename):
    i = 'fa-file-o'
    for icon, exts in icontypes.items():
        if filename.split('.')[-1] in exts:
            i = icon
    return i

@app.template_filter('humanize')
@login_required
def time_humanize(timestamp):
    mdate = datetime.utcfromtimestamp(timestamp)
    return humanize.naturaltime(mdate)

@login_required
def get_type(mode):
    if stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
        type = 'dir'
    else:
        type = 'file'
    return type

@login_required
def partial_response(path, start, end=None):
    file_size = os.path.getsize(path)

    if end is None:
        end = file_size - start - 1
    end = min(end, file_size - 1)
    length = end - start + 1

    with open(path, 'rb') as fd:
        fd.seek(start)
        bytes = fd.read(length)
    assert len(bytes) == length

    response = Response(
        bytes,
        206,
        mimetype=mimetypes.guess_type(path)[0],
        direct_passthrough=True,
    )
    response.headers.add(
        'Content-Range', 'bytes {0}-{1}/{2}'.format(
            start, end, file_size,
        ),
    )
    response.headers.add(
        'Accept-Ranges', 'bytes'
    )
    return response

@login_required
def get_range(request):
    range = request.headers.get('Range')
    m = re.match('bytes=(?P<start>\d+)-(?P<end>\d+)?', range)
    if m:
        start = m.group('start')
        end = m.group('end')
        start = int(start)
        if end is not None:
            end = int(end)
        return start, end
    else:
        return 0, None

@app.route('/delete/<path:p>')
@login_required
def delete(p):
    p=cleanP(p)
    p="/"+p
    path = UserFolder(current_user) + p 
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)
    p=p.rsplit("/",1)[0]
    return redirect( '/storage'+p )

@app.route('/makedir/',methods=['GET', 'POST'])
@app.route('/makedir/<path:p>',methods=['GET', 'POST'])
@login_required
def makedir(p=""):
    p=cleanP(p)
    new_folders=request.form["folder_name"]
    path = UserFolder(current_user) + "/"+p +"/"+ new_folders
    if not os.path.isdir(path):
        os.makedirs(path)
        flash("`%s` created. " %new_folders,'info')
    else:
        flash("`%s` could not be created. %s already exists." %(new_folders,new_folders),'info')
    return redirect( '/storage/'+p )

@app.route('/save/',methods=['GET', 'POST'])
@app.route('/save/<path:p>',methods=['GET', 'POST'])
@app.route('/save/<path:p>/<string:s>',methods=['GET', 'POST'])
@login_required
def save(p="",s="save_as"):
    # print(p,s)
    # sys.stdout.flush()
    p=cleanP(p)
    if s == "save_as":
        filename=secure_filename(request.form["file_name"])
        ext=request.form['action']
        session_=session_to_file(session,ext)
        path = UserFolder(current_user) + "/"+p +"/"+ filename+"."+ext
        if ext == "ses":
            session["session_file"]=path
    elif "session_file" not in list(session.keys()):
        return redirect( '/storage/' )
    else:
        ext="ses"
        session_=session_to_file(session,ext)
        path=session["session_file"]

    session_file = io.BytesIO()
    session_file.write(json.dumps(session_).encode())
    session_file.seek(0,os.SEEK_END)
    session_file=session_file.tell()           
    if session_file > session["available_disk_space"]:
        flash("'%s': you do not have enough space to save this file." %(filename+"."+ext),'error')
        return redirect( '/storage/'+p )
    with open(path,"w") as fout:
        json.dump(session_, fout)
    
    if s == "save_as":
        return redirect( '/storage/'+p )
    elif s == "save":
        app_redirect=session["app"]
        flash("`%s` saved." %os.path.basename(path),'info')
        return redirect(url_for(app_redirect))

@app.route('/load/<path:p>')
@login_required
def load(p):
    p=cleanP(p)
    path = UserFolder(current_user) + "/" + p
    with open(path,"r") as json_in:
        session_=json.load(json_in)
    del(session_["ftype"])
    del(session_["COMMIT"])
    for k in list(session_.keys()):
        session[k]=session_[k]
    plot_arguments=session["plot_arguments"]
    app_redirect=session["app"]
    if path[:-3] == "ses":
        session["session_file"]=path
    flash("`%s` loaded. Press `Submit` to see results." %os.path.basename(path),'info')
    return redirect(url_for(app_redirect))

@app.route('/getfile/<path:p>')
@login_required
def getfile(p):
    p=cleanP(p)
    path = UserFolder(current_user) + "/" + p
    res = send_file(path)
    res.headers.add('Content-Disposition', 'attachment')
    return res

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size

class PathView(MethodView):
    @login_required
    def get(self, p=''):
        apps=current_user.user_apps
        """
        downloading files
        """

        p=cleanP(p)
        
        hide_dotfile = request.args.get('hide-dotfile', request.cookies.get('hide-dotfile', 'yes'))

        path = os.path.join(UserFolder(current_user), p)

        quota_used=get_size(UserFolder(current_user))        

        if os.path.isdir(path):
            contents = []
            total = {'size': get_size(path), 'dir': 0, 'file': 0}
            for filename in os.listdir(path):
                if filename in ignored:
                    continue
                if hide_dotfile == 'yes' and filename[0] == '.':
                    continue
                filepath = os.path.join(path, filename)
                stat_res = os.stat(filepath)
                info = {}
                info['name'] = filename
                info['mtime'] = stat_res.st_mtime
                ft = get_type(stat_res.st_mode)
                info['type'] = ft
                total[ft] += 1
                sz = stat_res.st_size
                info['size'] = sz
                total['size'] += sz
                if p =="":
                    info["path"] = filename
                else:
                    info["path"] = p+"/"+filename
                contents.append(info)

            if len(p) > 0 and p[-1] == "/":
                p=p[:-1]
            #if len(p) > 0:
            #    p="/"+p

            percent_used=int(quota_used/current_user.disk_quota*100)
            available_disk_space=current_user.disk_quota-quota_used
            session["available_disk_space"]=available_disk_space
            if percent_used > 95:
                progress_bar_background="bg-danger"
            elif percent_used > 75:
                progress_bar_background="bg-warning"
            else:
                progress_bar_background="bg-success"

            page = render_template('storage.html', path=p, contents=contents, percent_used=percent_used , progress_bar_background=progress_bar_background, total=total, hide_dotfile=hide_dotfile, apps=apps)
            res = make_response(page, 200)
            res.set_cookie('hide-dotfile', hide_dotfile, max_age=16070400)
        elif os.path.isfile(path):
            if 'Range' in request.headers:
                start, end = get_range(request)
                res = partial_response(path, start, end)
            else:
                res = send_file(path)
                res.headers.add('Content-Disposition', 'attachment')
        else:
            return make_response('Not found', 404)
        return res

    @login_required
    def post(self, p=''):
        """
        uploading files
        """
        root=UserFolder(current_user)

        #p="/"+p

        p=cleanP(p)

        path = UserFolder(current_user)+ "/"+p
        #print(p, path, UserFolder(current_user))

        Path(path).mkdir(parents=True, exist_ok=True)

        info = {}
        info["msg"]=[]
        if os.path.isdir(path):
            files = request.files.getlist('files[]')
            files = [ s for s in files if s ]
            for uploadfile in files:
                # check file size
                pos = uploadfile.tell()
                uploadfile.seek(0, os.SEEK_END)  #seek to end
                file_length = uploadfile.tell()
                uploadfile.seek(pos)  # back to original position
                if session["available_disk_space"] < file_length:
                    msg="%s: You do not have enough free space to upload this file." %uploadfile.filename
                    flash(msg,'error')
                    return redirect('/storage/'+p)
                try:
                    session_=json.load(uploadfile)
                except:
                    msg="%s: This file was not uploaded as it is not properly formated." %uploadfile.filename
                    flash(msg,'error')
                    return redirect('/storage/'+p)
                if session_["ftype"] not in ["arguments","session"]:
                    msg="%s: This file was not uploaded as it is neither a session nor an arguments file." %uploadfile.filename
                    flash(msg,'error')
                    info["msg"].append(msg)
                else:
                    try:
                        filename = secure_filename(uploadfile.filename)
                        #session_["COMMIT"]=app.config['COMMIT']
                        with open(os.path.join(path, filename), "w") as write_file:
                            write_file.write(json.dumps(session_))
                        #uploadfile.save(os.path.join(path, filename))
                        #uploadfile.close()
                        session["available_disk_space"]=session["available_disk_space"]-file_length
                        info['status'] = 'success'
                        msg="%s: File Uploaded" %uploadfile.filename
                        flash(msg,'info')
                        info["msg"].append(msg)
                    except Exception as e:
                        info['status'] = 'error'
                        msg="%s: %s" %(uploadfile.filename,str(e))
                        flash(msg,'error')
                        info["msg"].append(msg)
                    # else:
                    #     info['status'] = 'success'
                    #     msg="%s: File Uploaded" %uploadfile.filename
                    #     flash(msg,'info')
                    #     info["msg"].append(msg)
        else:
            info['status'] = 'error'
            info['msg'] = 'Invalid Operation'
            msg="Could not save file(s) to %s. %s is not a directory." %(path,path)
            flash(msg,'error')
            info["msg"].append(msg)
        res = make_response(json.JSONEncoder().encode(info), 200)
        res.headers.add('Content-type', 'application/json')
        return redirect('/storage/'+p)

path_view = PathView.as_view('path_view')
app.add_url_rule('/storage/', view_func=path_view)
app.add_url_rule('/storage/<path:p>', view_func=path_view)