import pandas as pd
import io
from werkzeug.utils import secure_filename
import re


def check_rnaseq(EXC):
  if "samples" not in EXC.sheet_names:
    status=False
    msg="Could not find sample information - 'samples' sheet - in the submission file."
    return status, msg
  metadata=EXC.parse("RNAseq")
  email=metadata[  metadata["Field"] == "email"][ "Value" ].values[0]
  email=str(email).rstrip().lstrip()
  email=email.split(",")
  email=[ re.search("([^@|\s]+@[^@]+\.[^@|\s]+)",e,re.I) for e in email ]
  email=[ e.group(1) for e in email if e ]
  if not email :
    status=False
    msg="Contact email is not a valid email. Please provide a valid email in the 'email' field of your submission file."
    return status, msg
  nas=metadata[metadata["Value"].isna()]["Field"].tolist()
  if nas:
    status=False
    msg="The following fields require a valid value: {fields} ".format(fields=", ".join(nas) )
    return status, msg
  
  status="RNAseq"
  msg="Submission successuful. Please check for email confirmation."
  return status, msg

def submission_check(inputfile):
  valid_submissions=["RNAseq"]

  filename = secure_filename(inputfile.filename)
  fileread = inputfile.read()
  filestream=io.BytesIO(fileread)
  extension=filename.rsplit('.', 1)[1].lower()
  if extension != "xlsx":
    status=False
    msg="Wrong file extension detected."
    return status, msg

  EXC=pd.ExcelFile(filestream)
  sheets=EXC.sheet_names
  submission_type=[ s for s in sheets if s in valid_submissions ]
  if len(submission_type) > 1 :
    status=False
    msg="More than one submission type detected."
    return status, msg

  elif len(submission_type) == 0 :
    status=False
    msg="This submission file did not contain a valid submission sheet. Make sure you do not change the sheet names when editing the submission file."
    return status, msg

  if submission_type[0]=="RNAseq":
    status, msg=check_rnaseq(EXC)
  else:
    status=False
    msg="Submission failed."

  return status, msg