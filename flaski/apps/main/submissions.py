def check_rnaseq(df):
  status=True
  msg=None
  return status, msg

def submission_check(df, submission_type="RNAseq"):
  if submission_type=="RNAseq":
    status, msg=check_rnaseq(df)
  return status, msg