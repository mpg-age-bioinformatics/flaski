from matplotlib.pyplot import plot
import pandas as pd
# from flaski.routines import fuzzy_search
from pyflaski.lifespan import make_figure as survival_ls
from pyflaski.lifespan import figure_defaults as defaults_lifespan

import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import *
import plotly.graph_objs as go

import numpy as np
import re
import os

from functools import reduce


path_to_files="/flaski_private/cbioportal_data/"

def fix_id(x):
    try:
        x=int(x)
    except:
        x=str(x)
    x=str(x)
    return x

def grouping(g, mrna, low_percentile, hi_percentile):
    mrna_=mrna[[g]].dropna()
    mrna_=mrna_[mrna_[g]>0]
    if len(mrna_.columns.tolist()) > 1 :
        return np.nan

    values=mrna_[g].tolist()
    if not values:
        return np.nan
    
    l=np.percentile(values,float(low_percentile))
    h=np.percentile(values,float(hi_percentile))

    l=mrna_[mrna_[g]<=l].index.tolist()
    h=mrna_[mrna_[g]>=h].index.tolist()
    
    if ( len(l) < 2 ) or ( len(h) < 2 ) :
        return np.nan

    l=",".join(l)
    h=",".join(h)

    return f"{l} | {h}"


def get_groups(genes, mrna, lowp, highp):
    """
    define high and low expression groups
    based on 25 and 75 percentiles
    """

    mrna=mrna.transpose()

    #genes=list(set(mrna.columns.tolist()))
    print(len(genes))

    groups=pd.DataFrame( {"Hugo_Symbol":genes }, index=genes )
    groups["group"]=groups["Hugo_Symbol"].apply(lambda x: grouping(x,mrna, lowp, highp) )

    groups=groups.dropna()
    
    return groups
    

def plot_gene(gene_list, dataset, lp, hp):
    """
    plot a KaplanMeierFitter gene from a specific dataset
    read gene expression and clinical data as above
    """
    gene=gene_list[0]

    mrnafile=[s for s in os.listdir(path_to_files+dataset) if "mrna" in s][0]
    

    mrna=pd.read_csv(path_to_files+dataset+"/"+mrnafile ,sep="\t")
    cols=mrna.columns.tolist()

    if ( "Hugo_Symbol" in cols ) and ( "Entrez_Gene_Id" in cols ) :
        mrna["Entrez_Gene_Id"]=mrna["Entrez_Gene_Id"].apply(lambda x: fix_id(x) )
        mrna.index=mrna["Hugo_Symbol"]+"_"+mrna["Entrez_Gene_Id"]
        mrna=mrna.drop(["Hugo_Symbol","Entrez_Gene_Id"], axis=1)
    elif ( "Hugo_Symbol" in cols ) :
        mrna.index=mrna["Hugo_Symbol"]
        mrna=mrna.drop(["Hugo_Symbol"], axis=1)
    elif ( "Entrez_Gene_Id" in cols ) :
        mrna["Entrez_Gene_Id"]=mrna["Entrez_Gene_Id"].apply(lambda x: fix_id(x) )
        mrna.index=mrna["Entrez_Gene_Id"]
        mrna=mrna.drop(["Entrez_Gene_Id"], axis=1)

    mrna=mrna.astype(float)
 
    sample=pd.read_csv(path_to_files+dataset+"/data_clinical_sample.txt" ,sep="\t" )
    sample.columns=sample.loc[3,]
    sample=sample[4:]

    clinical=pd.read_csv(path_to_files+dataset+"/data_clinical_patient.txt" ,sep="\t" )
    clinical.columns=clinical.loc[3,]
    clinical=clinical[4:]

    clinical.loc[ clinical["OS_STATUS"] == "1:DECEASED", "dead" ] = 1 
    clinical.loc[ clinical["OS_STATUS"] == "0:LIVING" , "dead"] = 0

    clinical["time"]=clinical["OS_MONTHS"].tolist()

    def fix_float(x):
        try:
            x=float(x)
            return x
        except:
            return np.nan

    clinical["time"]=clinical["time"].apply(lambda x: fix_float(x) )

    ### Subset to patients that have a clinical record
    clinical_=clinical[["PATIENT_ID", "time", "dead" ]].dropna()
    clinical_=clinical_["PATIENT_ID"].tolist()

    clinical_=sample[sample["PATIENT_ID"].isin(clinical_)]["SAMPLE_ID"].tolist()

    # subset mrna samples to samples with clinical data
    mrna_=mrna.columns.tolist()
    mrna_=[ s for s in mrna_ if s in clinical_ ]
    mrna=mrna[mrna_]

    # define the high and low expression groups for the each gene
    groups=get_groups(gene_list, mrna, lp, hp)

    grps=groups[groups.index==gene]["group"].tolist()[0].split(" | ")
    h=grps[1].split(",")
    l=grps[0].split(",")    

    h=sample[sample["SAMPLE_ID"].isin(h)]["PATIENT_ID"].tolist()
    l=sample[sample["SAMPLE_ID"].isin(l)]["PATIENT_ID"].tolist()

    clinical.loc[ clinical["PATIENT_ID"].isin(h), "group" ] = "high"
    clinical.loc[ clinical["PATIENT_ID"].isin(l) , "group"] = "low"

    clinical=clinical[["group","time", "dead" ]].dropna()
    clinical=clinical.reset_index(drop=True)

    ### Sending data to the lifespan app
    pa=defaults_lifespan()

    pa['xvals'] =  "time"
    pa['yvals'] = "dead"
    pa['title'] = dataset+" - "+gene
    pa['xlabel'] = "Months"
    pa['ylabel'] = "Survival"
    pa['groups_value'] = "group"
    pa["list_of_groups"] = list(set(clinical["group"].tolist()))

    COLORS=["blue","green","red","black"]
    groups=pa["list_of_groups"]

    colors_dict=dict(zip(pa["list_of_groups"], COLORS[:len(groups)]))
    print(colors_dict)

    groups_settings=[]

    #["Conf_Interval", "ci_legend", "show_censors"]

    for g in pa["list_of_groups"]:
        group_dic={"name":g,\
            "linewidth_write" : "1.5",\
            "linestyle_value" : "solid",\
            "line_color_value" : colors_dict[g],\
            "linecolor_write" : "",\
            "model_settings" : ["Conf_Interval", "ci_legend"] ,\
            "ci_linewidth_write" : "1.0",\
            "ci_linestyle_value" : "solid",\
            "ci_line_color_value" : colors_dict[g],\
            "ci_linecolor_write" : "",\
            "ci_alpha" : "0.2",\
            "censor_marker_value" : "x",\
            "censor_marker_size_val" : "4",\
            "markerc" : "black",\
            "markerc_write" : "",\
            "edge_linewidth" : "1",\
            "edgecolor" : "black",\
            "edgecolor_write" : "",\
            "marker_alpha" : "1"}
        
        groups_settings.append(group_dic)

    pa["groups_settings"]=groups_settings

    df, fig, cph_coeff, cph_stats, input_df=survival_ls(clinical,pa)


    return df, fig, cph_coeff, cph_stats,pa, input_df


def read_results_files(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2) # 2 hours
    def _read_results_files(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"all.datasets.csv",sep="\t")
        #df=df.loc[ ~ df["dataset"].isin(['pcpg_tcga', 'meso_tcga']) ]
        return df.to_json()
    return pd.read_json(_read_results_files())

# def read_results_files(cache, path_to_files=path_to_files):
#     df=read_results_files_all(cache, path_to_files)
#     df=df.loc[ ~ df["dataset"].isin(['pcpg_tcga', 'meso_tcga']) ]  
#     return df 


def nFormat(x):
    if float(x) == 0:
        return str(x)
    elif ( float(x) < 0.01 ) & ( float(x) > -0.01 ) :
        return str('{:.3e}'.format(float(x)))
    else:
        return str('{:.3f}'.format(float(x)))


def filter_data(datasets=None, genes=None, cache=None):
    results_files=read_results_files(cache)
    # print(datasets)
    # import sys
    # sys.stdout.flush()
    if datasets:
        results_files=results_files[ results_files['dataset'].isin( datasets ) ]

    if genes:
        results_files=results_files[ results_files['Hugo_Symbol'].isin( genes ) ]

    if datasets and genes:
        results_files=results_files[ results_files['dataset'].isin( datasets ) & (results_files['Hugo_Symbol'].isin( genes )) ]


    return results_files






# def make_annotated_col(x,annotate_genes):
#     if x in annotate_genes:
#         return x
#     else:
#         return ""

# def plot_height(sets):
#     if len(sets) <= 14:
#         minheight = 700
#     else:
#         minheight=len(sets)
#         minheight=minheight * 45

#     if minheight > 945:
#         minheight=945
    
#     return minheight
