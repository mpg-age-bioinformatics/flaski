""" Flaski companion package"""

import os
os.environ["PYFLASKI"] = "1"

import pyflaski.__init__
import pyflaski.circularbarplots
import pyflaski.david
import pyflaski.heatmap
import pyflaski.histogram
import pyflaski.icellplot
import pyflaski.idendrogram
import pyflaski.iheatmap
import pyflaski.ihistogram
# import pyflaski.iscatterplot.bokeh
import pyflaski.iscatterplot
import pyflaski.iviolinplot
import pyflaski.kegg
import pyflaski.lifespan
import pyflaski.mds
import pyflaski.pca
import pyflaski.routines
import pyflaski.scatterplot
# import pyflaski.submissions
import pyflaski.tsne
import pyflaski.venndiagram
import pyflaski.violinplot

import json


def read_session(session_file, app):
    session={}
    if session_file.rsplit('.', 1)[1].lower() != "ses"  :
        error_msg="The file you have uploaded is not a session file. Please make sure you upload a session file with the correct `ses` extension."
        return None, error_msg

    with open(session_file, "r") as f:
        session_=json.load(f)
    if session_["ftype"]!="session":
        error_msg="The file you have uploaded is not a session file. Please make sure you upload a session file."
        return None, error_msg

    if session_["app"]!=app:
        error_msg="The file was not load as it is associated with the '%s' and not with this app." %session_["app"]
        return None, error_msg

    #del(session_["ftype"])
    #del(session_["COMMIT"])
    for k in list(session_.keys()):
        session[k]=session_[k]
    return session, None
