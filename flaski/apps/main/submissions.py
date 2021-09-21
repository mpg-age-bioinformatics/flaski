import pandas as pd
import io
from werkzeug.utils import secure_filename
import re
import tempfile
import os
from datetime import datetime

def timestamp():
  now = datetime.now()
  dt_string = now.strftime("%Y%m%d.%H%M%S.")
  return dt_string

def make_submission_file(suffix):
  dt_string=timestamp()
  new_file, filename = tempfile.mkstemp(suffix=suffix, prefix=dt_string )
  os.close(new_file)
  filename="/submissions/"+os.path.basename(filename)
  return filename


def check_pipelines(EXC, TAG):
  status=False
  attachment_path=None
  # dictionary of expected sheet names per TAG
  expected_sheets={ 'riboseq' : ['riboseq', 'samples', 'matching'],\
    'GSEA' : ['GSEA', 'samples', 'ExpMatrix', 'GeneSets'],\
    'motif_enrichment' : ['motif_enrichment', 'samples']}

  # 'RNAseq': ['RNAseq', 'samples'],\
  # 'intronRet' : ['intronRet', 'samples'],\
  # 'alternativeSplicing' : ['alternativeSplicing', 'samples'],\
  # 'circRNA' : ['circRNA', 'samples'],\
  # 'miRNAseq' : ['miRNAseq', 'samples'],\
  # '16S' : ['16S', 'samples'],\
  # 'IRfinder':['IRfinder', 'samples']
  # 'ATAC_seq' : ['ATAC_seq', 'samples', 'input'],\
  # 'variantCalling' : ['variantCalling', 'samples'],\



  # loop over all expected sheets and check if they are present, if not, send email
  for sheet in expected_sheets[TAG]:
    if sheet not in EXC.sheet_names:
      status=False
      msg="Could not find '%s' sheet in the submission file." %(sheet)
      return status, msg, attachment_path 
  metadata=EXC.parse(TAG)
  email=metadata[  metadata["Field"] == "email"][ "Value" ].values[0]
  email=str(email).rstrip().lstrip()
  email=email.split(",")
  email=[ re.search("([^@|\s]+@[^@]+\.[^@|\s]+)",e,re.I) for e in email ]
  email=[ e.group(1) for e in email if e ]
  if not email :
    msg="Contact email is not a valid email. Please provide a valid email in the 'email' field of your submission file."
    return status, msg, attachment_path
  nas=metadata[metadata["Value"].isna()]["Field"].tolist()
  if nas:
    msg="The following fields require a valid value: {fields} ".format(fields=", ".join(nas) )
    return status, msg, attachment_path
  
  status=TAG
  msg="Submission successuful. Please check for email confirmation."

  filename=make_submission_file(".%s.xlsx" %(TAG))

  EXCout=pd.ExcelWriter(filename)
  # write out all expected sheets
  for sheet in expected_sheets[TAG]:
    df=EXC.parse(sheet)
    df.to_excel(EXCout,sheet,index=None)
  EXCout.save()

  return status, msg, filename


def submission_check(inputfile):
  status=False
  attachment_path=None

  valid_submissions=["RNAseq", "intronRet", "variantCalling", "alternativeSplicing" , 'ATAC_seq', 'circRNA', 'riboseq', 'miRNAseq', '16S', 'GSEA', 'motif_enrichment', 'IRfinder']

  filename = secure_filename(inputfile.filename)
  fileread = inputfile.read()
  filestream=io.BytesIO(fileread)
  extension=filename.rsplit('.', 1)[1].lower()
  if extension != "xlsx":
    msg="Wrong file extension detected."
    return status, msg, attachment_path

  EXC=pd.ExcelFile(filestream)
  sheets=EXC.sheet_names
  submission_type=[ s for s in sheets if s in valid_submissions ]
  if len(submission_type) > 1 :
    msg="More than one submission type detected."
    return status, msg, attachment_path

  elif len(submission_type) == 0 :
    msg="This submission file did not contain a valid submission sheet. Make sure you do not change the sheet names when editing the submission file."
    return status, msg, attachment_path

  # test submission sheets, variable pipelines.
  status, msg, attachment_path=check_pipelines(EXC, submission_type[0])
  
  return status, msg, attachment_path