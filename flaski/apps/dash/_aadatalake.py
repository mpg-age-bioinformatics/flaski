import pandas as pd
# from flaski.routines import fuzzy_search
from flaski.apps.main.iscatterplot import make_figure as make_scatter
from flaski.apps.main.iscatterplot import figure_defaults as defaults_scatter
from flaski.apps.main.pca import make_figure as make_pca
from flaski.apps.main.pca import figure_defaults as defaults_pca

import numpy as np
import re

path_to_files="/flaski_private/aarnaseqlake/"

def read_results_files(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2) # 2 hours
    def _read_results_files(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"files2ids.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_results_files())

def read_gene_expression(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2)
    def _read_gene_expression(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"gene_expression.tsv",sep="\t",index_col=[0])
        return df.to_json()
    return pd.read_json(_read_gene_expression())

def read_genes(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2)
    def _read_genes(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"genes.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_genes())

def read_significant_genes(cache, path_to_files=path_to_files):
    @cache.memoize(60*60*2)
    def _read_significant_genes(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"significant.genes.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_significant_genes())


def nFormat(x):
    if float(x) == 0:
        return str(x)
    elif ( float(x) < 0.01 ) & ( float(x) > -0.01 ) :
        return str('{:.3e}'.format(float(x)))
    else:
        return str('{:.3f}'.format(float(x)))

def filter_samples(datasets=None, reps=None, groups=None, cache=None):
    results_files=read_results_files(cache)

    # print(datasets)
    # import sys
    # sys.stdout.flush()

    if datasets:
        results_files=results_files[ results_files['Set'].isin( datasets ) ]

    if reps:
        results_files=results_files[ results_files['Reps'].isin( reps ) ]

    if groups:
        results_files=results_files[ results_files['Group'].isin( groups ) ]

    nsets=len(list(set(results_files['Set'])))
    if nsets > 1: 
        results_files["Labels"]=results_files["Set"]+"_"+results_files["Reps"]
    else:
        results_files["Labels"]=results_files["Reps"]

    ids2labels=results_files[["IDs","Labels"]].drop_duplicates()
    ids2labels.index=ids2labels["IDs"].tolist()
    ids2labels=ids2labels[["Labels"]].to_dict()["Labels"]

    return results_files, ids2labels

def filter_genes(selected_gene_names, selected_gene_ids, cache):
    selected_genes=read_genes(cache)
    if selected_gene_names:
        selected_genes=selected_genes[ selected_genes["gene_name"].isin(selected_gene_names) ]
    if selected_gene_ids:
        selected_genes=selected_genes[ selected_genes["gene_id"].isin(selected_gene_ids) ]
    return selected_genes

def filter_gene_expression(ids2labels, selected_gene_names, selected_gene_ids, cache):
    @cache.memoize(60*60*2)
    def _filter_gene_expression(ids2labels, selected_gene_names, selected_gene_ids):
        gedf=read_gene_expression(cache)
        selected_genes=filter_genes(selected_gene_names, selected_gene_ids, cache)
        selected_ge=gedf[list(ids2labels.keys())]
        selected_ge=selected_ge.astype(float)
        cols=selected_ge.columns.tolist()
        selected_ge["sum"]=selected_ge.sum(axis=1)
        selected_ge=selected_ge[selected_ge["sum"]>0]
        selected_ge=selected_ge.drop(["sum"],axis=1)
        selected_ge=pd.merge(selected_genes, selected_ge, left_on=["name_id"], right_index=True,how="left")
        selected_ge=selected_ge.dropna(subset=cols,how="all")
        selected_ge=selected_ge.drop(["name_id"],axis=1)
        selected_ge.reset_index(inplace=True,drop=True)
        selected_ge.rename(columns=ids2labels,inplace=True)
        for c in selected_ge.columns.tolist()[2:]:
            selected_ge[c]=selected_ge[c].apply(lambda x: nFormat(x) )
        rename=selected_ge.columns.tolist()[2:]
        rename=[ s.replace("_", " ")  for s in rename ]
        rename=selected_ge.columns.tolist()[:2]+rename
        selected_ge.columns=rename
        return selected_ge.to_json()
    return pd.read_json(_filter_gene_expression(ids2labels, selected_gene_names, selected_gene_ids))

def read_metadata(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2) # 2 hours
    def _read_metadata(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"metadata.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_metadata())

def read_dge(dataset, groups, cache, html=True,path_to_files=path_to_files):
    @cache.memoize(60*60*2) # 2 hours
    def _read_dge(dataset,groups,cache, html, path_to_files=path_to_files):
        metadata=read_metadata(cache)
        # print(metadata.head(),dataset,groups )
        metadata=metadata[ (metadata["Set"] == dataset ) & \
            (metadata["Group_1"].isin(groups) ) & \
            (metadata["Group_2"].isin(groups) ) ]
        dge_file=metadata["File"].tolist()[0]
        selected_dge=pd.read_csv(path_to_files+"pairwise/"+dge_file,sep="\t")
        selected_dge["padj"]=selected_dge["padj"].astype(float)
        selected_dge=selected_dge.sort_values(by=["padj"],ascending=True)
        cols=selected_dge.columns.tolist()
        if html:
            for c in cols[2:]:
                selected_dge[c]=selected_dge[c].apply(lambda x: nFormat(x) )
        cols=[ s.replace("_", " ") for s in cols ]
        selected_dge.columns=cols
        samples_names=cols[2:-5]
        samples_names.sort()
        cols=cols[:2]+samples_names+cols[-5:]
        selected_dge=selected_dge[cols]
        mapcols={"baseMean":"base Mean","log2FoldChange":"log2 FC","lfcSE":"lfc SE","pvalue":"p value"}
        selected_dge=selected_dge.rename(columns=mapcols)
        return selected_dge.to_json()
    return pd.read_json(_read_dge(dataset,groups,cache,html=html))

def find_fc(df):
    df_=df[:1]
    samples_names=df_.columns.tolist()[2:-5]
    groups=list(set([ s[:-2] for s in samples_names ]))
    group_1=groups[0]
    group_2=groups[1]

    group_1_list=[ s for s in samples_names if bool(re.match(re.compile(group_1+" ."), s  ) )  ]
    group_2_list=[ s for s in samples_names if bool(re.match(re.compile(group_2+" ."), s  ) )  ]

    group_1_values=np.mean([ df_[s].tolist()[0] for s in group_1_list  ])
    group_2_values=np.mean([ df_[s].tolist()[0] for s in group_2_list  ])

    fc_=group_2_values/group_1_values
    fc=df_["log2 FC"].tolist()[0]
    if fc * fc_ > 0:
        return "log2(%s/%s)" %(group_2,group_1)
    else:
        return "log2(%s/%s)" %(group_1,group_2)

def make_volcano_plot(df,dataset, annotate):

    df_=df.copy()
    fc=find_fc(df_)

    def check_sig(x):
        try:
            if float(x) < 0.05:
                return "red"
            else:
                return "black"
        except:
            return "black"

    df_["sig"]=df_["padj"].apply( lambda x: check_sig(x) )
    df_["-log10(p adj.)"]=df_["padj"].apply(lambda x: np.log10(x)*-1 )
    df_[fc]=df_["log2 FC"]

    df_.loc[df_["sig"]=="red", "group"] = "significant"
    df_.loc[df_["sig"]=="black", "group"] = "not significant"

    pa=defaults_scatter()
    pa["xvals"]=fc
    pa["yvals"]="-log10(p adj.)"
    pa["title"]=dataset
    pa["markerc_col"]="sig"
    pa["xlabel"]=fc
    pa["ylabel"]="-log10(p adj.)"
    pa["marker_alpha"]="0.5"
    pa["labels_col_value"]="gene name"
    pa["fixed_labels"]=annotate
    pa["labels_alpha"]=1

    fig=make_scatter(df_,pa)
    return fig, pa

def make_ma_plot(df,dataset, annotate):
    df_=df.copy()
    fc=find_fc(df_)

    def check_sig(x):
        try:
            if float(x) < 0.05:
                return "red"
            else:
                return "black"
        except:
            return "black"

    df_["sig"]=df_["padj"].apply( lambda x: check_sig(x) )
    df_["log10(base mean)"]=df_["base Mean"].apply(lambda x: np.log10(x) )
    df_[fc]=df_["log2 FC"]

    df_.loc[df_["sig"]=="red", "group"] = "significant"
    df_.loc[df_["sig"]=="black", "group"] = "not significant"

    pa=defaults_scatter()
    pa["xvals"]="log10(base mean)"
    pa["yvals"]=fc
    pa["title"]=dataset
    pa["markerc_col"]="sig"
    pa["xlabel"]="log10(base mean)"
    pa["ylabel"]=fc #"-log10(p adj.)"
    pa["marker_alpha"]="0.5"
    pa["labels_col_value"]="gene name"
    pa["fixed_labels"]=annotate
    pa["labels_alpha"]=1

    fig=make_scatter(df_,pa)
    return fig, pa

def make_pca_plot(df,dataset):
    df_=df.copy()
    pa=defaults_pca()
    pa["xvals"]="gene_id"
    pa["yvals"]=df_.columns.tolist()[2:]
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

    samples=projected["row"].tolist()
    groups=[ s[:-2] for s in samples ]
    projected["Group"]=groups
    groups=list(set(groups))
    
    COLORS=["blue","green","red","black"]
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
    pa["xvals"]=cols[1]
    pa["yvals"]=cols[2]
    pa["title"]=dataset
    pa["markerc_col"]="sig"
    pa["xlabel"]=cols[1]
    pa["ylabel"]=cols[2]
    pa["marker_alpha"]="1"
    pa["labels_col_value"]="row"
    pa["groups_value"]="Group"
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

    fig=make_scatter(projected,pa)
    return fig, pa


    # # print(projected.head(),features.head())
    # import sys
    # sys.stdout.flush()








        

