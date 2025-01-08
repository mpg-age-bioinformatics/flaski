#!/usr/bin/env python3

from myapp import app, db
from myapp.models import User, UserLogging
import sys, os, datetime
import pandas as pd

@app.shell_context_processor
def make_shell_context():
  return {'db': db, 'User': User}

def stats(outfolder="/flaski_private"):
  entries=UserLogging.query.filter_by()
  df=[ [ e.id, e.email, e.action, e.date_time ] for e in entries ]
  df=pd.DataFrame(df, columns=["id","email","action", "date_time"])
  outname=str(datetime.datetime.now()).split(".")[0].replace(" ","_").replace(":",".")
  if not os.path.isdir(outfolder):
      os.makedirs(outfolder)
  outname=outfolder+"/"+outname+".stats.tsv"
  df.to_csv(outname, sep="\t", index=None)
  print("Done collecting usage stats.\n%s" %outname)
  sys.stdout.flush()


if __name__ == "__main__":
  with app.app_context():
    stats()

# pod=$(kubectl --kubeconfig ~/admin.conf -n flaski-prod get pods  | grep server | head -n 1 | awk '{print $1}')
# kubectl --kubeconfig ~/admin.conf -n flaski-prod cp stats.py ${pod}:/myapp/stats.py
# kubectl --kubeconfig ~/admin.conf -n flaski-prod exec -it ${pod} -- /bin/bash
# ./stats.py
# kubectl --kubeconfig ~/admin.conf -n flaski-prod cp ${pod}:/flaski_private/2023-08-31_09.17.51.stats.tsv ~/2023-08-31_09.17.51.stats.tsv
