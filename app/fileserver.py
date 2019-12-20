from flask import Flask, make_response, request, session, render_template, send_file, Response
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

from app import app, sess

# root = "/tmp/"

def UserFolder(u):
    if u.is_authenticated:
        root = os.path.normpath("/Users/jboucas/Desktop/flaski_user_space/%s" %str(u.id))
        if not os.path.isdir(root):
            os.makedirs(root)
    else:
        root=None
    return root


key = app.config["SECRET_KEY"]

ignored = ['.bzr', '$RECYCLE.BIN', '.DAV', '.DS_Store', '.git', '.hg', '.htaccess', '.htpasswd', '.Spotlight-V100', '.svn', '__MACOSX', 'ehthumbs.db', 'robots.txt', 'Thumbs.db', 'thumbs.tps']
datatypes = {'audio': 'm4a,mp3,oga,ogg,webma,wav', 'archive': '7z,zip,rar,gz,tar', 'image': 'gif,ico,jpe,jpeg,jpg,png,svg,webp', 'pdf': 'pdf', 'quicktime': '3g2,3gp,3gp2,3gpp,mov,qt', 'source': 'atom,bat,bash,c,cmd,coffee,css,hml,js,json,java,less,markdown,md,php,pl,py,rb,rss,sass,scpt,swift,scss,sh,xml,yml,plist', 'text': 'txt', 'video': 'mp4,m4v,ogv,webm', 'website': 'htm,html,mhtm,mhtml,xhtm,xhtml'}
icontypes = {'fa-music': 'm4a,mp3,oga,ogg,webma,wav', 'fa-archive': '7z,zip,rar,gz,tar', 'fa-picture-o': 'gif,ico,jpe,jpeg,jpg,png,svg,webp', 'fa-file-text': 'pdf', 'fa-film': '3g2,3gp,3gp2,3gpp,mov,qt', 'fa-code': 'atom,plist,bat,bash,c,cmd,coffee,css,hml,js,json,java,less,markdown,md,php,pl,py,rb,rss,sass,scpt,swift,scss,sh,xml,yml', 'fa-file-text-o': 'txt', 'fa-film': 'mp4,m4v,ogv,webm', 'fa-globe': 'htm,html,mhtm,mhtml,xhtm,xhtml'}

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

class PathView(MethodView):
    @login_required
    def get(self, p=''):
        """
        downloading files
        """
        
        hide_dotfile = request.args.get('hide-dotfile', request.cookies.get('hide-dotfile', 'no'))

        path = os.path.join(UserFolder(current_user), p)
        

        if os.path.isdir(path):
            contents = []
            total = {'size': 0, 'dir': 0, 'file': 0}
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
                contents.append(info)

            if len(p) > 0 and p[-1] == "/":
                p=p[:-1]
            if len(p) > 0:
                p="/"+p

            page = render_template('fileserver.html', path=p, contents=contents, total=total, hide_dotfile=hide_dotfile)
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
            res = make_response('Not found', 404)
        return res

    @login_required
    def post(self, p=''):
        """
        uploading files
        """
        print(p)

        p="/"+p

        #s = requests.Session()
        #print(request.cookies["session"])
        #print(app)
        #print(key,request.cookies.get('auth_cookie'))

        #if request.cookies.get('auth_cookie') == key:
        
        path = UserFolder(current_user)+ p
        #print(p, path, UserFolder(current_user))

        Path(path).mkdir(parents=True, exist_ok=True)

        info = {}
        info["msg"]=[]
        if os.path.isdir(path):
            files = request.files.getlist('files[]')
            for f in files:
                if f.filename.rsplit('.', 1)[1].lower() not in ["ses","arg"]:
                    info["msg"].append("%s: This file was not uploaded as it is neither a session nor arguments file." %f.filename)
                else:    
                    session_=json.load(f) 
                    print(session_)
                    if session_["ftype"] not in ["arguments","session"]: 
                        info["msg"].append("%s: This file was not uploaded as it is neither a session nor arguments file." %f.filename)
                    else:
                        try:
                            filename = secure_filename(f.filename)
                            f.save(os.path.join(path, filename))
                            info['status'] = 'success'
                            info["msg"].append("%s: File Saved" %f.filename)
                        except Exception as e:
                            info['status'] = 'error'
                            info["msg"].append("%s: %s" %(f.filename,str(e)))
        else:
            info['status'] = 'error'
            info['msg'] = 'Invalid Operation'
        res = make_response(json.JSONEncoder().encode(info), 200)
        res.headers.add('Content-type', 'application/json')
        #else:
        #    info = {} 
        #    info['status'] = 'error'
        #    info['msg'] = 'Authentication failed'
        #    res = make_response(json.JSONEncoder().encode(info), 401)
        #    res.headers.add('Content-type', 'application/json')

        # change fileserver to files
        # return url_for('fileserver')
        # add messaging on the right of the buttoms 
        # on the download screen add send as input dataframe, parameters, or session
        # restrict to sessions and parameters only
        # change extensions to par and ses
        # simplify routines
        # simplify tokes

        return res

path_view = PathView.as_view('path_view')
app.add_url_rule('/fileserver/', view_func=path_view)

app.add_url_rule('/fileserver/<path:p>', view_func=path_view)