from flaski import app, db
from flaski.models import User, UserLogging
import sys

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

if __name__ == "__main__":
    from flaski import app
    import os, datetime
    from flaski.email import send_files_deletion_email

    def clean():
        print("Looking for old files.")
        sys.stdout.flush()
        data_folder=app.config['USERS_DATA']
        users=os.listdir(data_folder)
        users=[ s for s in users if "tmp" not in s  ]
        today=datetime.datetime.now()

        for userid in users:
            user=User.query.filter_by(id=int(userid)).first()
            mailed=user.mailed_files
            start_path=data_folder+userid+"/"

            if mailed:
                for f in list(mailed.keys()):
                    if not os.path.isfile(start_path+f):
                        del(mailed[f])
            else:
                mailed={}
            
            newmail=[]
            for dirpath, dirnames, filenames in os.walk(start_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    stat = os.stat(fp)
                    ts=os.path.getmtime(fp)
                    ts=datetime.datetime.fromtimestamp(ts)
                    delta=today-ts
                    days=delta.days
                    short=fp.split(start_path)[-1]
                
                    if days >= 31 :
                        if short in list(mailed.keys()):
                            mailed_date=mailed[short]
                            delta_mail=today-mailed_date
                            delta_mail=delta_mail.days
                            if delta_mail >= 31:
                                os.remove(fp)
                                del(mailed[short])
                        else:
                            mailed[short]=today
                            newmail.append(short)
            if len(newmail) > 0 :
                send_files_deletion_email(user,newmail)
            user.mailed_files = mailed
            db.session.add(user)
            db.session.commit()
        print("Done looking for old files.")
        sys.stdout.flush()

    clean()