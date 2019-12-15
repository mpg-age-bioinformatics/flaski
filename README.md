# flask_dashboard

starting redis:

```
redis-server redis.conf
```

##################

def download():
    file = open('damlevels.csv','r')
    returnfile = file.read().encode('latin-1')
    file.close()
    return Response(returnfile,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=damlevels.csv"})

@app.route('/item/<int:appitemid>/')
@app.route('/item/<int:appitemid>/<path:anythingcanbehere>')
def show_item(appitemid, anythingcanbehere=None):

##################

@api.route("/files/<path:path>")
def get_file(path):
    """Download a file."""
    return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=True)

##################

@app.route('/return-files/')
def return_files_tut():
	try:
		return send_file('/var/www/PythonProgramming/PythonProgramming/static/images/python.jpg', attachment_filename='python.jpg')
	except Exception as e:
		return str(e)

###################

https://stackoverflow.com/questions/24577349/flask-download-a-file