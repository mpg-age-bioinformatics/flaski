import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pylab as plt
import seaborn as sns
import sys
from scipy.cluster.hierarchy import fcluster

matplotlib.use('agg')
STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
STANDARD_COLORS=["blue","green","red","cyan","magenta","yellow","black","white"]


def make_figure(df,pa):
    tmp=df.copy()
    tmp.index=tmp[tmp.columns.tolist()[0]].tolist()
    tmp=tmp[pa["yvals"]]

    #print(tmp,pa["yvals"])
    pa_={}
    if pa["yvals_colors"] != "select a column..":
        pa_["yvals_colors"]=list( tmp[ tmp.index == pa["yvals_colors"] ].values[0] )
        tmp=tmp[tmp.index != pa_["yvals_colors"]]
    else :
        pa_["yvals_colors"]=None

    if pa["xvals_colors"] != 'select a row..':
        pa_["xvals_colors"]=df[ pa["xvals_colors"] ].tolist()
    else :
        pa_["xvals_colors"]=None

    checkboxes=["row_cluster","col_cluster","robust","xticklabels","yticklabels","annotate"]

    for c in checkboxes:
        if (pa[c] =="on") | (pa[c] ==".on"):
            pa_[c]=True
        else:
            pa_[c]=False

    for v in ["vmin","vmax","center"]:
        if pa[v] == "":
            pa_[v]=None
        else:
            pa_[v]=float(pa[v])

    if pa["color_bar_label"] == "":
        pa_["color_bar_label"]={}
    else:
        pa_["color_bar_label"]={'label': pa["color_bar_label"]}


    if pa["zscore_value"] == "none":
        pa_["zscore_value"]=None
    elif pa["zscore_value"] == "row":
        pa_["zscore_value"]=0
    elif pa["zscore_value"] == "columns":
        pa_["zscore_value"]=1


    if (int(pa["n_cols_cluster"]) > 0) | (int(pa["n_rows_cluster"]) > 0):
        g = sns.clustermap(tmp,\
                            method=pa["method_value"],\
                            metric=pa["distance_value"],\
                            row_cluster=pa["row_cluster"],\
                            col_cluster=pa["col_cluster"],\
                            xticklabels=False, \
                            yticklabels=False )

        if int(pa["n_cols_cluster"]) > 0:
            def extract_cols_colors(g, k=int(pa["n_cols_cluster"])):
                reordered_cols=g.dendrogram_col.reordered_ind
                cols_linkage=g.dendrogram_col.linkage
                
                clusters = fcluster(cols_linkage, k, criterion='maxclust')
                original_order=pd.DataFrame({"col":tmp.columns.tolist(),"cluster":clusters})
                
                cols_cluster=original_order["cluster"].tolist()
                cols_cluster_=list(set(cols_cluster))
                cols_cluster_dic={}
                for c in cols_cluster_:
                    cols_cluster_dic[c]=np.random.rand(3,)
                cols_cluster=[ cols_cluster_dic[s] for s in cols_cluster ]

                reordered_cols=pd.DataFrame(index=reordered_cols)
                original_order=pd.merge(reordered_cols,original_order,\
                                        how="left",left_index=True, right_index=True)

                return cols_cluster, original_order
            
            cols_cluster, cols_cluster_numbers=extract_cols_colors(g)
            pa_["yvals_colors"]=cols_cluster
            
        if int(pa["n_rows_cluster"]) > 0:
            def extract_rows_colors(g, k=int(pa["n_rows_cluster"])):
                reordered_index=g.dendrogram_row.reordered_ind
                index_linkage=g.dendrogram_row.linkage
                
                clusters = fcluster(index_linkage, k, criterion='maxclust')
                original_order=pd.DataFrame({"col":tmp.index.tolist(),"cluster":clusters})
                
                cols_cluster=original_order["cluster"].tolist()
                cols_cluster_=list(set(cols_cluster))
                cols_cluster_dic={}
                for c in cols_cluster_:
                    cols_cluster_dic[c]=np.random.rand(3,)
                cols_cluster=[ cols_cluster_dic[s] for s in cols_cluster ]

                reordered_index=pd.DataFrame(index=reordered_index)
                original_order=pd.merge(reordered_index,original_order,\
                                        how="left",left_index=True, right_index=True)    

                return cols_cluster, original_order

            cluster_index, index_cluster_numbers = extract_rows_colors(g)
            pa_["xvals_colors"]=cluster_index
        
        plt.close()

    else:
        cols_cluster_numbers = None
        index_cluster_numbers = None


    g = sns.clustermap(tmp, \
                        xticklabels=pa_["yticklabels"], \
                        yticklabels=pa_["xticklabels"], \
                        linecolor=pa["linecolor"],\
                        linewidths=float(pa["linewidths"]), \
                        method=pa["method_value"], \
                        metric=pa["distance_value"], \
                        col_colors=pa_["yvals_colors"], \
                        row_colors=pa_["xvals_colors"], \
                        cmap=pa["cmap_value"],\
                        vmin=pa_["vmin"], vmax=pa_["vmax"], \
                        cbar_kws=pa_["color_bar_label"],\
                        center=pa_["center"], \
                        mask=tmp.isnull(), \
                        row_cluster=pa_["row_cluster"], \
                        col_cluster=pa_["col_cluster"],\
                        figsize=(float(pa["fig_width"]),float(pa["fig_height"])),\
                        robust=pa["robust"], \
                        dendrogram_ratio=(float(pa["col_dendogram_ratio"]),float(pa["row_dendogram_ratio"])),\
                        z_score=pa_["zscore_value"])

    plt.suptitle(pa["title"], fontsize=float(pa["title_size_value"]))
    g.ax_heatmap.set_xticklabels(g.ax_heatmap.get_xmajorticklabels(), fontsize = float(pa["yaxis_font_size"]))
    g.ax_heatmap.set_yticklabels(g.ax_heatmap.get_ymajorticklabels(), fontsize = float(pa["xaxis_font_size"]))

    return g, cols_cluster_numbers, index_cluster_numbers

def figure_defaults():
    plot_arguments={
        "fig_width":"6.0",\
        "fig_height":"6.0",\
        "xcols":[],\
        "xvals":"",\
        "xvals_colors":"",\
        "ycols":[],\
        "yvals":"",\
        "yvals_colors":"",\
        "title":'',\
        "title_size":STANDARD_SIZES,\
        "title_size_value":"10",\
        "xticklabels":'.off',\
        "yticklabels":".on",\
        "method":['single','complete','average', 'weighted','centroid','median','ward'],\
        "method_value":"ward",\
        "distance":["euclidean","minkowski","cityblock","seuclidean","sqeuclidean",\
                   "cosine","correlation","hamming","jaccard","chebyshev","canberra",\
                   "braycurtis","mahalanobis","yule","matching","dice","kulsinski","rogerstanimoto",\
                   "russellrao","sokalmichener","sokalsneath","wminkowski"],\
        "distance_value":"euclidean",\
        "n_cols_cluster":"0",\
        "n_rows_cluster":"0",\
        "cmap":["viridis","plasma","inferno","magma","cividis","Greys","Purples",\
               "Blues","Greens","Oranges","Reds","YlOrBr","YlOrRd","OrRd","PuRd",\
               "RdPu","BuPu","GnBu","PuBu","YlGnBu","PuBuGn","BuGn","YlGn",\
               "binary","gist_yard","gist_gray","gray","bone","pink","spring",\
               "summer","autumn","winter","cool","Wistia","hot","afmhot","gist_heat",\
               "copper","PiYg","PRGn","BrBG","PuOr","RdGy","RdBu","RdYlBu","Spectral",\
               "coolwarm","bwr","seismic","Pastel1","Pastel2","Paired","Accent","Dark2",\
               "Set1","Set2","Set3","tab10","tab20","tab20b","tab20c","flag","prism","ocean",\
               "gist_earth", "gnuplot","gnuplot2","CMRmap","cubehelix","brg","hsv",\
               "gist_rainbow","rainbow","jet","nipy_spectral","gist_ncar"],\
        "cmap_value":"YlOrRd",\
        "vmin":"",\
        "vmax":"",\
        "linewidths":"0",\
        "linecolor":STANDARD_COLORS,\
        "linecolor_value":"white",\
        "color_bar_label":"",\
        "center":"",\
        "row_cluster":".on",\
        "col_cluster":".on",\
        "robust":".on",\
        "col_dendogram_ratio":"0.25",\
        "row_dendogram_ratio":"0.25",\
        "zscore":["none","row","columns"],\
        "zscore_value":"none",\
        "xaxis_font_size":"10",\
        "yaxis_font_size":"10",\
        "annotate":".off",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"heatmap",\
        "session_downloadn":"MySession.heatmap",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.heatmap",\
        "inputargumentsfile":"Select file.."}
    
    checkboxes=["row_cluster","col_cluster","robust","xticklabels","yticklabels"]

    # not update list
    notUpdateList=["inputsessionfile"]

    # lists without a default value on the arguments
    excluded_list=[]

    # lists with a default value on the arguments
    allargs=list(plot_arguments.keys())

    # dictionary of the type 
    # {"key_list_name":"key_default_value"} 
    # eg. {"marker_size":"markers"}
    lists={} 
    for i in range(len(allargs)):
        if type(plot_arguments[allargs[i]]) == type([]):
            if allargs[i] not in excluded_list:
                lists[allargs[i]]=allargs[i+1]

    return plot_arguments, lists, notUpdateList, checkboxes