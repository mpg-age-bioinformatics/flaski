import hashlib
from matplotlib.pyplot import plot
import pandas as pd
# from flaski.routines import fuzzy_search
from pyflaski.violinplot import figure_defaults as default_violin
from pyflaski.violinplot import make_figure as make_violin
from pyflaski.scatterplot import make_figure as make_scatter
from pyflaski.scatterplot import figure_defaults as defaults_scatter
from pyflaski.pca import make_figure as make_pca
from pyflaski.pca import figure_defaults as defaults_pca
import plotly.express as px
import plotly.graph_objects as go

import numpy as np
import re

path_to_files="/flaski_private/aaprotlake/"
file_path = f"{path_to_files}all_merged.csv"
meta_file_path = f"{path_to_files}all_merged_meta.csv"
latent_file_path = f"{path_to_files}latent_embedding_June2025.csv"


def read_meta_file(cache):
    @cache.memoize(60*60*2) # 2 hours
    def _load_h5():
        agg_df = pd.read_csv(meta_file_path, header=0, index_col=0)
        agg_df = agg_df.sort_index()
        agg_df = agg_df[~agg_df.index.duplicated(keep='first')]
        return agg_df
    return _load_h5()



def read_merged_file(cache):
    @cache.memoize(60*60*2) # 2 hours
    def _load_h5():
        agg_df = pd.read_csv(file_path, header=0, index_col=0)
        agg_df = agg_df.sort_index()
        agg_df = agg_df[~agg_df.index.duplicated(keep='first')]
        return agg_df
    return _load_h5()


def read_genes(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2)
    def _read_genes():
        agg_df = pd.read_csv(file_path, header=0, index_col=0)
        wormbaseID = agg_df.columns[:-5]
        df = pd.DataFrame(wormbaseID)
        df.columns = ["gene_id"]
        return df.to_json()
    return pd.read_json(_read_genes())

def read_gene_expression(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2)
    # currently failing to read gene_expression with caching
    def _read_gene_expression(path_to_files=path_to_files):
        df = read_merged_file(cache)
        df = df.sort_index()
        gedf = df.iloc[:,:-5].T
        return gedf
    return (_read_gene_expression())


"""
def read_significant_genes(cache, path_to_files=path_to_files):
    @cache.memoize(60*60*2)
    def _read_significant_genes(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"significant.genes.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_significant_genes())
"""

def nFormat(x):
    if float(x) == 0:
        return str(x)
    elif ( float(x) < 0.01 ) & ( float(x) > -0.01 ) :
        return str('{:.3e}'.format(float(x)))
    else:
        return str('{:.3f}'.format(float(x)))

def filter_samples(datasets=None, genotype=None, condition=None, cache=None):
    results_files=read_merged_file(cache)

    if datasets:
        results_files=results_files[ results_files['study'].isin( datasets ) ]

    if genotype:
        results_files=results_files[ results_files['genotype'].isin( genotype ) ]

    if condition:
        results_files=results_files[ results_files['condition'].isin( condition ) ]

    results_files["Labels"]=results_files["study"]

    results_files['IDs'] = results_files.index
    ids2labels=results_files[["IDs","Labels"]].drop_duplicates()
    ids2labels.index=ids2labels["IDs"].tolist()
    ids2labels=ids2labels[["Labels"]].to_dict()["Labels"]

    return results_files, ids2labels

def filter_genes(selected_gene_ids, cache):
    selected_genes=read_genes(cache)
    if selected_gene_ids:
        selected_genes=selected_genes[ selected_genes["gene_id"].isin(selected_gene_ids) ].values
    return selected_genes


# TODO: clean the code
def filter_gene_expression(ids2labels, selected_gene_ids, cache):
    #@cache.memoize(60*60*2)
    def _filter_gene_expression(ids2labels, selected_gene_ids):
        gedf=read_gene_expression(cache)
        gedf[pd.isnull(gedf)] = 0.0

        selected_genes = filter_genes(selected_gene_ids, cache)
        if (selected_genes.shape[0]) > 1:
            selected_genes = selected_genes.squeeze()
        else:
            selected_genes = selected_genes[0]
        
        selected_ge = gedf[list(ids2labels.keys())]
        selected_ge = selected_ge.filter(selected_genes, axis=0)
        selected_ge = selected_ge.astype(float)
        cols = selected_ge.columns.tolist()
        #selected_ge["sum"] = selected_ge.sum(axis=1)
        #selected_ge = selected_ge[selected_ge["sum"]>0]
        #selected_ge = selected_ge.drop(["sum"],axis=1)
        #selected_ge['gene_id'] = selected_ge.index
        #selected_ge=pd.merge(selected_genes, selected_ge, left_on=["gene_id"], right_index=True, how="left")
        selected_ge=selected_ge.dropna(subset=cols,how="all",axis=0)
        selected_ge=selected_ge.dropna(how="all",axis=1)
        if 'gene_id' in selected_ge.columns:
            selected_ge=selected_ge.drop(["gene_id"],axis=1)
        #selected_ge.reset_index(inplace=True,drop=True)
        #selected_ge.rename(columns=ids2labels,inplace=True)

        selected_ge =selected_ge.round(3)
        #for c in selected_ge.columns.tolist()[:]:
        #    selected_ge[c]=selected_ge[c].apply(lambda x: nFormat(x) )
        #rename=selected_ge.columns.tolist()[2:]
        #rename=[ s.replace("_", " ")  for s in rename ]
        #rename=selected_ge.columns.tolist()[:2]+rename
        #selected_ge.columns=rename

        return selected_ge
    return _filter_gene_expression(ids2labels, selected_gene_ids)

def read_latent(cache):
    @cache.memoize(60*60*2) # 2 hours
    def _read_metadata(path_to_files=path_to_files):
        df=pd.read_csv(latent_file_path, index_col=0, header=0)
        return df.to_json()
    return pd.read_json(_read_metadata())



# TODO: Clean
# this is for visualization of PseudoAge latent embedding
def make_pca_plot(study, genotype, condition, cache):
    df_ = read_latent(cache)
    
    if study is not None and len(study) > 0:
        df_ = df_[df_['group'].isin(study)]
    if genotype is not None and len(genotype) > 0:
        df_ = df_[df_['genotype'].isin(genotype)]
    if condition is not None and len(condition) > 0:
        df_ = df_[df_['condition'].isin(condition)]

    """
    df_['gene_id'] = df_.index
    pa=defaults_pca()
    pa["xvals"]="gene_id"
    pa["yvals"]=df_.columns.tolist()[1:-5]
    pa["scale_value"]="feature"
    pa["percvar"]="20"
    projected, features=make_pca(df_,pa)

    cols=projected.columns.tolist()

    def fix_comp(c):
        label=c.split(" - ")[0]
        c=c.split(" ")[-1].split("%")[0]
        c=nFormat(c)
        c=label+" - "+c+"%"
        return c
    
    cols=[ cols[0], fix_comp( cols[1] ),  fix_comp( cols[2] )]
    projected.columns=cols

    samples=projected[cols[0]].tolist()
    groups=[ s[:-2] for s in samples ]
    projected["Group"]=groups
    """
    groups=list(set(df_['condition']))

    COLORS=["blue","green","red","black", "yellow", "purple"]
    MARKERS_1=["circle", "square", "diamond", \
        "triangle-up"] 
    MARKERS_2=["triangle-down", "triangle-left", "triangle-right",\
        "star", "asterisk", "hash", "y-up", "y-down" ,"y-left", "y-right" ]

    color_markers=[]
    for m in MARKERS_1 :
        for c in COLORS:
            color_markers.append([c,m])

    for m in MARKERS_2 :
        for c in COLORS:
            color_markers.append([c,m])

    groups=dict(zip(groups, color_markers[:len(groups)]))

    pa=defaults_scatter()
    pa["fig_width"] = "1000"
    pa["xvals"]='z'
    pa["yvals"]='y'
    pa["title"]='PsudoAge latent space'
    pa["markerc_col"]="sig"
    pa["xlabel"]='z'
    pa["ylabel"]='y'
    pa["marker_alpha"]="1"
    pa["labels_col_value"]='condition'
    pa["groups_value"]="condition"
    pa["list_of_groups"]=list(groups.keys())

    groups_settings=[]

    for g in list(groups.keys()):
        group_dic={"name":g,\
            "markers":"7",\
            "markersizes_col":"select a column..",\
            "markerc":groups[g][0],\
            "markerc_col":"select a column..",\
            "markerc_write":pa["markerc_write"],\
            "edge_linewidth":pa["edge_linewidth"],\
            "edge_linewidth_col":"select a column..",\
            "edgecolor":pa["edgecolor"],\
            "edgecolor_col":"select a column..",\
            "edgecolor_write":"",\
            "marker":groups[g][1],\
            "markerstyles_col":"select a column..",\
            "marker_alpha":pa["marker_alpha"],\
            "markeralpha_col_value":"select a column.."}

        groups_settings.append(group_dic)

    pa["groups_settings"]=groups_settings

    fig=make_scatter(df_,pa)
    return fig, pa, df_


def make_annotated_col(x,annotate_genes):
    if x in annotate_genes:
        return x
    else:
        return ""

def plot_height(sets):
    if len(sets) <= 14:
        minheight = 700
    else:
        minheight=len(sets)
        minheight=minheight * 45

    if minheight > 945:
        minheight=945
    
    return minheight

def make_violin_plot(study, genotype, condition, cache):
    df_ = read_meta_file(cache)
    
    if study is not None and len(study) > 0:
        df_ = df_[df_['study'].isin(study)]
    if genotype is not None and len(genotype) > 0:
        df_ = df_[df_['genotype'].isin(genotype)]
    if condition is not None and len(condition) > 0:
        df_ = df_[df_['condition'].isin(condition)]

    _meta_condition = condition.copy()
    _meta_condition = sorted(_meta_condition)

    height_=plot_height(set(_meta_condition))
    
    if len(list(set(df_["condition"].tolist() ))) ==1:
        width_bar=0.15
    elif len(list(set(df_["condition"].tolist() ))) == 2:
        width_bar=0.25
    else:
        width_bar=0.5

    if len(set(df_['study'])) > 1:
        df_['plot_x'] = df_['study'] + '__' + df_['condition']
    else:
        df_['plot_x'] = df_['condition']
    
    fig = go.Figure()
    fig = px.box(df_,x='plot_x', y='PseudoAge', color="condition", height=height_)
    fig.update_traces(width=width_bar)
    fig.update_xaxes(categoryorder='array', categoryarray= sorted(df_['plot_x']))
    fig.update_layout(
        yaxis = dict(
            title_text = "Biological Age (1.0 = mean life span)",
        ),
        title={
            'text': 'PseudoAge prediction (Jun2025 ver)',
            'xanchor': 'left',
            'yanchor': 'top' }
            # "font": {"size": float(pa["titles"]), "color":"black"  } } 
    )



    return fig


def make_bar_plot(df, meta_study, meta_condition, label): 
    bar_df=df.copy()
    bar_df = bar_df.T
    bar_df.columns = ['value']
    _meta_study = meta_study.copy()
    _meta_study = _meta_study.sort_index()
    _meta_condition = meta_condition.copy()
    _meta_condition = _meta_condition.sort_index()

    bar_df['Dataset'] = _meta_study
    bar_df['Condition'] = meta_condition.T

    #bar_df = bar_df.T
    #bar_df=pd.melt(bar_df)

    height_=plot_height(set(_meta_condition))
    
    def format_df(x1,x2):
        v=x1.split(x2)[1].split(".Rep")[0]
        return v

    if len(set(bar_df['Dataset'])) == 1 :
        #bar_df["Dataset"]=sets_[0]
        #bar_df["Group"]=['_'.join(s.split("_")[:-1]) for s in bar_df["variable"].tolist()]
        bar_df=bar_df.groupby(["Dataset","Condition"], as_index=False).agg({'value':['mean','std']})

        bar_df["Sample"]=bar_df["Dataset"]+"__"+bar_df["Condition"]
        bar_df.columns=["Dataset", "Condition", "mean", "std", "Sample"]

        if len(list(set( bar_df["Condition"].tolist() ))) ==1:
            width_bar=0.15
        elif len(list(set( bar_df["Condition"].tolist() ))) == 2:
            width_bar=0.25
        else:
            width_bar=0.5

        fig = go.Figure()
        fig = px.bar(bar_df, x='Sample', y='mean', color="Condition", labels={'mean':label}, height=height_)
        fig.update_traces(error_y={"type":"data", "array":np.array(bar_df["std"]), "symmetric":True, "color":'rgba(0,0,0,0.5)',"thickness":2, "width":5})
        fig.update_traces(width=width_bar)
        fig.update_layout(
            yaxis = dict(
                title_text = "LFQ intensities",
            ),
            title={
                'text': label,
                'xanchor': 'left',
                'yanchor': 'top' }
                # "font": {"size": float(pa["titles"]), "color":"black"  } } 
        )

        # for data in fig.data:
        #     data["width"] = 0.5
    else:
        #baar_df['Dataset'] = bar_df['variable'].apply(lambda x: [s for s in sets_ if s in x][0])       
        #bar_df['Condition'] = bar_df.apply(lambda x: format_df(x.variable, x.Dataset), axis=1)
        bar_df=bar_df.groupby(["Dataset","Condition"], as_index=False).agg({'value':['mean','std']})
    
        bar_df["Sample"]=bar_df["Dataset"]+"__"+bar_df["Condition"]
        bar_df.columns=["Dataset", "Condition", "mean", "std", "Sample"]

        fig = go.Figure()
        fig = px.bar(bar_df, x='Sample', y='mean', color="Dataset", labels={'mean':label}, height=height_)
        fig.update_traces(error_y={"type":"data", "array":np.array(bar_df["std"]), "symmetric":True, "color":'rgba(0,0,0,0.5)',"thickness":1.5, "width":2}) # width=2000
    
    #fig.show()
    return fig



