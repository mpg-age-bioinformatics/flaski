# from scipy import stats
import math
import numpy as np
import pandas as pd
from sklearn import preprocessing
from sklearn.manifold import TSNE

def make_figure(df,pa):
    df_tsne=df.copy()
    df_tsne.index=df_tsne[pa["xvals"]].tolist()
    df_tsne=df_tsne[pa["yvals"]]

    if float( pa["percvar"].replace(",",".") ) < 100 :
        df_tsne["__std__"]=df_tsne.std(axis=1)
        df_tsne=df_tsne.sort_values( by=["__std__"],ascending=False )
        nrows=round(len(df_tsne)*float( pa["percvar"].replace(",",".") )/100)
        df_tsne=df_tsne[:nrows] 
        df_tsne=df_tsne.drop(["__std__"],axis=1)

    df_tsne=df_tsne.T

    tsne = TSNE(n_components=int(pa["ncomponents"]), perplexity=int(pa["perplexity"]), early_exaggeration=12.0,random_state=None)
    if pa["scale_value"] == "feature":
        axis=0
    elif pa["scale_value"] == "sample":
        axis=1
    df_tsne_scaled = preprocessing.scale(df_tsne,axis=axis)
    
    projected=tsne.fit_transform(df_tsne_scaled)

    projected=pd.DataFrame(projected)
    cols=projected.columns.tolist()
    cols=[ "Component"+str(c+1) for c in cols ]
    projected.columns=cols
    projected.index=df_tsne.index.tolist()
    projected.reset_index(inplace=True, drop=False)
    projected.columns=["row"]+cols

    return projected

def figure_defaults():
    """Generates default figure arguments.

    Returns:
        dict: A dictionary of the style { "argument":"value"}
    """
    plot_arguments={
        "xcols":[],\
        "xvals":"",\
        "ycols":[],\
        "yvals":"",\
        "ncomponents":"2",\
        "percvar":"100",\
        "scale":["feature","sample"],\
        "scale_value":"sample",\
        "perplexity":"30", \
        "download_format":["tsv","xlsx"],\
        "downloadf":"xlsx",\
        "downloadn":"tSNE",\
        "session_downloadn":"MySession.tSNE",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.tSNE",\
        "inputargumentsfile":"Select file.."}

        #"scale":".on",\


    return plot_arguments