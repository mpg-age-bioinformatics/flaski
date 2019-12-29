# flask_dashboard

### redis

starting redis:

```
redis-server redis.conf
```

### Databases

```
rm -rf app.db migrations
flask db init
flask db migrate -m "users table"
flask db upgrade 
```

alternative
```
flask db migrate -m "new fields in user model"
flask db upgrade
```

### Logging

There are two approaches to test email logging. The easiest one is to use the SMTP debugging server from Python. 
This is a fake email server that accepts emails, but instead of sending them, it prints them to the console. 
To run this server, open a second terminal session and run the following command on it:
```
python -m smtpd -n -c DebuggingServer localhost:8025 
```
and 
```
export MAIL_SERVER=localhost
export MAIL_PORT=8025
```
before running your app.

A second testing approach for this feature is to configure a real email server. 
Below is the configuration to use your Gmail account's email server:
```
export MAIL_SERVER=smtp.googlemail.com
export MAIL_PORT=587
export MAIL_USE_TLS=1
export MAIL_USERNAME=<your-gmail-username>
export MAIL_PASSWORD=<your-gmail-password>
```




                                {% if path == "" %}
                                <td class="text-xs-left " style="padding-left:0px;padding-right:0px;" data-sort-value="dir-{{entry.name | lower}}"><i class="fa fa-fw fa-folder " aria-hidden="true"></i>&nbsp;<a href="{{entry.name}}" ><strong>{{entry.name}}</strong></a></td>
                                {% else %}
                                <td class="text-xs-left " style="padding-left:0px;padding-right:0px;" data-sort-value="dir-{{entry.name | lower}}"><i class="fa fa-fw fa-folder " aria-hidden="true"></i>&nbsp;<a href="{{path}}{% '/' if path != '' else '' %}{{entry.name}}" ><strong>{{entry.name}}</strong></a></td>
                                {% endif %}



  <script src="https://kit.fontawesome.com/609ed3ec10.js" crossorigin="anonymous"></script>

  <!-- Custom fonts for this template-->
  <link rel="stylesheet" href="{{ url_for('static', filename='vendor/fontawesome-free/css/all.min.css') }}" type="text/css">
  <link href="https://fonts.googleapis.com/css?family=Nunito:200,200i,300,300i,400,400i,600,600i,700,700i,800,800i,900,900i" rel="stylesheet">

  <!-- Custom styles for this template-->
  <link rel="stylesheet" href="{{ url_for('static', filename='css/sb-admin-2.min.css') }}" type="text/css">









    <!-- Bootstrap core JavaScript-->
    <script src="{{ url_for('static', filename='vendor/jquery/jquery.min.js') }}"></script>
    <script src="{{ url_for('static', filename='vendor/bootstrap/js/bootstrap.bundle.min.js') }}"></script>

    <!-- Core plugin JavaScript-->
    <script src="{{ url_for('static', filename='vendor/jquery-easing/jquery.easing.min.js') }}"></script>

    <!-- Custom scripts for all pages-->
    <script src="{{ url_for('static', filename='js/sb-admin-2.min.js') }}"></script>

    <!-- Page level plugins -->
    <script src="{{ url_for('static', filename='vendor/chart.js/Chart.min.js') }}"></script>

    <!-- Page level custom scripts -->
    <script src="{{ url_for('static', filename='js/demo/chart-area-demo.js') }}"></script>
    <script src="{{ url_for('static', filename='js/demo/chart-pie-demo.js') }}"></script>