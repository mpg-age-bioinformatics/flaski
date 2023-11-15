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


path_to_files="/flaski_private/cbioportal/"

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

    groups=pd.DataFrame( {"Hugo_Symbol":genes }, index=genes )
    groups["group"]=groups["Hugo_Symbol"].apply(lambda x: grouping(x,mrna, lowp, highp) )

    groups=groups.dropna()
    
    return groups


def read_study_meta(path_to_files=path_to_files, dataset=None):
    if dataset:
        with open (path_to_files+dataset+"/meta_study.txt", "r") as md:
            meta_data=md.read()
            meta_data=meta_data.split("\n")
            meta_data=[s for s in meta_data if s != ""]

            return meta_data
    

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
        mrna.index=mrna["Hugo_Symbol"]
        mrna=mrna.drop(["Hugo_Symbol","Entrez_Gene_Id"], axis=1)
        # mrna["Entrez_Gene_Id"]=mrna["Entrez_Gene_Id"].apply(lambda x: fix_id(x) )
        # mrna.index=mrna["Hugo_Symbol"]+"_"+mrna["Entrez_Gene_Id"]
        # mrna=mrna.drop(["Hugo_Symbol","Entrez_Gene_Id"], axis=1)
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

    title=read_study_meta(dataset=dataset)
    title=[s.split("short_name:")[1] for s in title if "short_name" in s][0]
    # print(title)

    ### Sending data to the lifespan app
    pa=defaults_lifespan()

    pa['xvals'] =  "time"
    pa['yvals'] = "dead"
    pa['title'] = title+" - "+gene
    pa['xlabel'] = "Months"
    pa['ylabel'] = "Survival"
    pa['groups_value'] = "group"
    pa["list_of_groups"] = list(set(clinical["group"].tolist()))

    COLORS=["blue","green","red","black"]
    groups=pa["list_of_groups"]

    colors_dict=dict(zip(pa["list_of_groups"], COLORS[:len(groups)]))
    # print(colors_dict)

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


def read_results_files(cache, path_to_files=path_to_files):  #cache
    @cache.memoize(60*60*2) # 2 hours
    def _read_results_files(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"all.datasets.gene.names.cleaned.csv",sep="\t", dtype=str)
        return df.to_json(orient='records', default_handler=str )
    return pd.read_json(_read_results_files(), dtype=str)


def read_meta_files(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2) # 2 hours
    def _read_meta_files(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"all.metaData.formatted.csv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_meta_files())


def nFormat(x):
    if float(x) == 0:
        return str(x)
    elif ( float(x) < 0.01 ) & ( float(x) > -0.01 ) :
        return str('{:.3e}'.format(float(x)))
    else:
        return str('{:.3f}'.format(float(x)))


def filter_data(cache, datasets=None, genes=None):
    @cache.memoize(60*60*2) # 2 hours
    def _filter_data(cache, datasets=None, genes=None):
        results_files=read_results_files(cache)

        if datasets:
            results_files=results_files[ results_files['Dataset'].isin( datasets ) ]

        if genes:
            results_files=results_files[ results_files['Hugo Symbol'].isin( genes ) ]

        if datasets and genes:
            results_files=results_files[ results_files['Dataset'].isin( datasets ) & (results_files['Hugo Symbol'].isin( genes )) ]

        return results_files
    return _filter_data(cache, datasets, genes) 



def convert_html_links_to_markdown(html_text):
    start_idx = 0
    markdown_text = ""
    
    while True:
        # Find the start and end positions of the <a> tag
        start_tag_idx = html_text.lower().find("<a", start_idx)
        
        if start_tag_idx == -1:
            # No more <a> tags found, append the remaining text and break
            markdown_text += html_text[start_idx:]
            break
        
        end_tag_idx = html_text.lower().find("</a>", start_tag_idx)
        
        if end_tag_idx == -1:
            # If there's no matching </a> tag, append the remaining text and break
            markdown_text += html_text[start_idx:]
            break
        
        # Extract the link text and href attribute
        link_start_idx = html_text.find(">", start_tag_idx) + 1
        link_text = html_text[link_start_idx:end_tag_idx]
        href_start_idx = html_text.lower().find('href="', start_tag_idx) + 6
        href_end_idx = html_text.find('"', href_start_idx)
        href = html_text[href_start_idx:href_end_idx]
        
        # Convert the link to Dash Markdown format and append it
        markdown_text += f"{html_text[start_idx:start_tag_idx]}[{link_text}]({href})"
        
        # Update the start index for the next iteration
        start_idx = end_tag_idx + 4
    
    return markdown_text


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
