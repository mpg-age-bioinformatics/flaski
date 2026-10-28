import hashlib
from pathlib import Path
from matplotlib.pyplot import plot
import pandas as pd
# from flaski.routines import fuzzy_search
from pyflaski.scatterplot import make_figure as make_scatter
from pyflaski.scatterplot import figure_defaults as defaults_scatter
from pyflaski.pca import make_figure as make_pca
from pyflaski.pca import figure_defaults as defaults_pca
import plotly.express as px
import plotly.graph_objects as go

import numpy as np
import re

path_to_files="/flaski_private/aaprotlake/"
meta_file_path = f"{path_to_files}metadata.csv"


def _read_data_file(cache, filename, header_only=False):
    filename = str(filename)
    stat = Path(filename).stat()

    @cache.memoize(60*60*2) # 2 hours
    def _read_csv(filename, modified_ns, size_bytes, header_only):
        return pd.read_csv(filename, index_col=0, nrows=0 if header_only else None)

    # Separate cache entries per file; replacing data invalidates its cached copy.
    return _read_csv(filename, stat.st_mtime_ns, stat.st_size, header_only)


def read_meta_file(cache):
    return _read_data_file(cache, meta_file_path).sort_index().copy()


def read_genes(cache,path_to_files=path_to_files):
    files = _read_data_file(cache, Path(path_to_files) / "file_index.csv")
    header = _read_data_file(cache, Path(path_to_files) / files.index[0], header_only=True)
    return pd.DataFrame({"gene_id": [c for c in header.columns if c.startswith("WBGene")]})


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
    results_files=read_meta_file(cache)

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


def filter_gene_expression(ids2labels, selected_gene_ids, cache):
    sample_ids = list(ids2labels)
    genes = read_genes(cache)["gene_id"].tolist()
    if selected_gene_ids:
        selected_gene_ids = set(selected_gene_ids)
        genes = [gene for gene in genes if gene in selected_gene_ids]
    if not sample_ids or not genes:
        return pd.DataFrame(index=genes, columns=sample_ids, dtype=float)

    metadata = read_meta_file(cache).loc[sample_ids]
    frames = []
    for source_file, samples in metadata.groupby("source_file", sort=False):
        study = _read_data_file(cache, Path(path_to_files) / source_file)
        frames.append(study.loc[samples.index, genes])

    # Subset each study before combining; preserve the requested sample order.
    expression = pd.concat(frames).loc[sample_ids, genes].T
    expression.index.name = None
    expression.columns.name = None
    return expression.astype(float).fillna(0.0).round(3)

def make_pca_plot(expression, metadata):
    # Samples are observations and genes are features; retain the selected sample order.
    values = expression.T.astype(float)
    message = None
    if len(values) < 2:
        message = "PCA requires at least two selected samples."
    elif not np.isfinite(values.to_numpy()).all():
        message = "PCA is unavailable because the selected expression contains non-finite values."
    else:
        values = values.loc[:, values.var(ddof=0) > 0]
        if values.shape[1] < 2:
            message = "PCA requires at least two genes with varying expression."

    if message:
        fig = go.Figure()
        fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig, None, pd.DataFrame()

    # Use the same calculation as Flaski's PCA app, with explicit settings.
    pca_input = values.T.copy()
    pca_input.insert(0, "gene_id", pca_input.index)
    pca_pa = defaults_pca()
    pca_pa["xvals"] = "gene_id"
    pca_pa["yvals"] = values.index.tolist()
    pca_pa["ncomponents"] = "2"
    pca_pa["percvar"] = "100"
    pca_pa["scale_value"] = "feature"
    projected, _ = make_pca(pca_input, pca_pa)
    axes = projected.columns.tolist()[1:3]
    df_ = projected.set_index(projected.columns[0]).loc[values.index, axes].copy()
    df_["sample_id"] = df_.index
    df_["study"] = metadata.loc[df_.index, "study"]
    df_["condition"] = metadata.loc[df_.index, "condition"]
    groups=sorted(df_["condition"].unique())

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

    groups={group: color_markers[i % len(color_markers)] for i, group in enumerate(groups)}

    pa=defaults_scatter()
    pa["fig_width"] = "1000"
    pa["xvals"]=axes[0]
    pa["yvals"]=axes[1]
    pa["title"]="PCA (gene-wise scaled expression)"
    pa["markerc_col"]="select a column.."
    pa["xlabel"]=axes[0]
    pa["ylabel"]=axes[1]
    pa["marker_alpha"]="1"
    pa["labels_col_value"]="sample_id"
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

