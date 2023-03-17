from myapp import app, db
from datetime import datetime
import jwt
from time import time

# print("\n\n\n--------------_MODELS\n\n\n")
class FTPSubmissions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name=db.Column(db.String(128), index=True, unique=True)
    user_id=db.Column(db.Integer)
    date_time = db.Column(db.DateTime, default=datetime.utcnow )
    ftp_user = db.Column(db.String(128), index=True) #, unique=True)

    def __init__(self, **kwargs):
        super(FTPSubmissions, self).__init__(**kwargs)

    # 14 days * 24 hours * 60 minutes * 60 seconds
    def get_submission_validation_token(self, expires_in=1290600):
        return jwt.encode(
            {'file': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256') #.decode('utf-8')

    @staticmethod
    def verify_submission_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['file']
        except:
            return None
        # file_name=FTPSubmissions.query.get(id)
        return id
