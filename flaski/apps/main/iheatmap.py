import scipy.cluster.hierarchy as sch
import scipy.spatial as scs
from scipy import stats
import plotly.graph_objects as go
import plotly.figure_factory as ff


STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
STANDARD_COLORS=["blue","green","red","cyan","magenta","yellow","black","white"]


def make_figure(df,pa):
    tmp=df.copy()
    tmp.index=tmp[tmp.columns.tolist()[0]].tolist()
    tmp=tmp[pa["yvals"]]

    #print(tmp,pa["yvals"])
    pa_={}
    # if pa["yvals_colors"] != "select a column..":
    #     pa_["yvals_colors"]=list( tmp[ tmp.index == pa["yvals_colors"] ].values[0] )
    #     tmp=tmp[tmp.index != pa_["yvals_colors"]]
    # else :
    #     pa_["yvals_colors"]=None

    # if pa["xvals_colors"] != 'select a row..':
    #     pa_["xvals_colors"]=df[ pa["xvals_colors"] ].tolist()
    # else :
    #     pa_["xvals_colors"]=None

    checkboxes=["row_cluster","col_cluster","xticklabels","yticklabels","annotate"] # "robust"
    for c in checkboxes:
        if (pa[c] =="on") | (pa[c] ==".on"):
            pa_[c]=True
        else:
            pa_[c]=False

    # for v in ["vmin","vmax","center"]:
    #     if pa[v] == "":
    #         pa_[v]=None
    #     else:
    #         pa_[v]=float(pa[v])

    # if pa["color_bar_label"] == "":
    #     pa_["color_bar_label"]={}
    # else:
    #     pa_["color_bar_label"]={'label': pa["color_bar_label"]}


    if pa["zscore_value"] == "row":
        tmp=pd.DataFrame(stats.zscore(tmp, axis=1, ddof=1),columns=tmp.columns.tolist(), index=tmp.index.tolist())
    elif pa["zscore_value"] == "columns":
        tmp=pd.DataFrame(stats.zscore(tmp, axis=0, ddof=1),columns=tmp.columns.tolist(), index=tmp.index.tolist())

    data_array=tmp.values
    data_array_=tmp.transpose().values
    labels=tmp.columns.tolist()
    rows=tmp.index.tolist()

    # Initialize figure by creating upper dendrogram
    fig = ff.create_dendrogram(data_array_, orientation='bottom', labels=labels, color_threshold=1.5,\
                            distfun = scs.distance.pdist,\
                            linkagefun= lambda x: sch.linkage(x, "complete"))
    for i in range(len(fig['data'])):
        fig['data'][i]['yaxis'] = 'y2'
    dendro_leaves_y_labels = fig['layout']['xaxis']['ticktext']
    dendro_leaves_y = [ labels.index(i) for i in dendro_leaves_y_labels ]

    #print(dendro_leaves_y)

    # Create Side Dendrogram
    dendro_side = ff.create_dendrogram(data_array, orientation='right', labels=rows, color_threshold=1.5,\
                                        distfun = scs.distance.pdist,\
                                        linkagefun= lambda x: sch.linkage(x, "complete"))
    for i in range(len(dendro_side['data'])):
        dendro_side['data'][i]['xaxis'] = 'x2'
    dendro_leaves_x_labels = dendro_side['layout']['yaxis']['ticktext']
    dendro_leaves_x = [ rows.index(i) for i in dendro_leaves_x_labels ]

    # Add Side Dendrogram Data to Figure
    for data in dendro_side['data']:
        fig.add_trace(data)

    # Create Heatmap
    #print(dendro_leaves_x)

    #dendro_leaves = list(map(int, dendro_leaves))
    #data_dist = pdist(data_array)
    #heat_data = squareform(data_dist)
    heat_data=data_array
    heat_data = heat_data[dendro_leaves_x,:]
    heat_data = heat_data[:,dendro_leaves_y]

    #print(len(dendro_leaves_x_labels),len(dendro_leaves_y_labels))

    heatmap = [
        go.Heatmap(
            x = dendro_leaves_x_labels,
            y = dendro_leaves_y_labels,
            z = heat_data,
            colorscale = 'Blues',
            colorbar={"title":{"text":"Number of Bills per Cell" ,"font":{"size":10}},
                    "lenmode":"pixels", "len":800/4,
                    "xpad":100,"tickfont":{"size":10}}
        )
    ]

    heatmap[0]['x'] = fig['layout']['xaxis']['tickvals']
    heatmap[0]['y'] = dendro_side['layout']['yaxis']['tickvals']

    # Add Heatmap Data to Figure
    for data in heatmap:
        fig.add_trace(data)

    # Edit Layout
    fig.update_layout({'width':800, 'height':800,
                            'showlegend':False, 'hovermode': 'closest',
                            "yaxis":{"mirror" : "allticks", 
                                    'side': 'right',
                                    'showticklabels':True,
                                    'ticktext':dendro_leaves_x_labels}})

    # Edit xaxis
    fig.update_layout(xaxis={'domain': [.15, 1],
                                    'mirror': False,
                                    'showgrid': False,
                                    'showline': False,
                                    'zeroline': False,
                                    'showticklabels': True,
                                    "tickfont":{"size":10},
                                    'ticks':"",\
                                    'ticktext':dendro_leaves_y_labels})
    # Edit xaxis2
    fig.update_layout(xaxis2={'domain': [0, .15],
                                    'mirror': False,
                                    'showgrid': False,
                                    'showline': False,
                                    'zeroline': False,
                                    'showticklabels': False,
                                    'ticks':""})

    # Edit yaxis 
    fig.update_layout(yaxis={'domain': [0, .85],
                                    'mirror': False,
                                    'showgrid': False,
                                    'showline': False,
                                    'zeroline': False,
                                    'showticklabels': True,
                                    "tickfont":{"size":8},
                                    'ticks': "",\
                                    'tickvals':dendro_side['layout']['yaxis']['tickvals'],\
                                    'ticktext':dendro_leaves_x_labels})

    # Edit yaxis2 showticklabels
    fig.update_layout(yaxis2={'domain':[.825, .975],
                                    'mirror': False,
                                    'showgrid': False,
                                    'showline': False,
                                    'zeroline': False,
                                    'showticklabels': False,
                                    'ticks':""})

    fig.update_layout(template='plotly_white')

    fig.update_layout(font={"size":2})

    fig.update_layout(title={"text":"Heatmap title","yanchor":"top","font":{"size":25}})

    # fig.update_layout(
    #     yaxis = dict(
    #         tickmode = 'array',
    #         ticktext = dendro_leaves_x_labels ) )

    # Plot!
    fig.show()




    # g = sns.clustermap(tmp, \
    #                     xticklabels=pa_["yticklabels"], \
    #                     yticklabels=pa_["xticklabels"], \
    #                     linecolor=pa["linecolor"],\
    #                     linewidths=float(pa["linewidths"]), \
    #                     method=pa["method_value"], \
    #                     metric=pa["distance_value"], \
    #                     col_colors=pa_["yvals_colors"], \
    #                     row_colors=pa_["xvals_colors"], \
    #                     cmap=pa["cmap_value"],\
    #                     vmin=pa_["vmin"], vmax=pa_["vmax"], \
    #                     cbar_kws=pa_["color_bar_label"],\
    #                     center=pa_["center"], \
    #                     mask=tmp.isnull(), \
    #                     row_cluster=pa_["row_cluster"], \
    #                     col_cluster=pa_["col_cluster"],\
    #                     figsize=(float(pa["fig_width"]),float(pa["fig_height"])),\
    #                     robust=pa["robust"], \
    #                     dendrogram_ratio=(float(pa["col_dendogram_ratio"]),float(pa["row_dendogram_ratio"])),\
    #                     z_score=pa_["zscore_value"])

    # plt.suptitle(pa["title"], fontsize=float(pa["title_size_value"]))
    # g.ax_heatmap.set_xticklabels(g.ax_heatmap.get_xmajorticklabels(), fontsize = float(pa["yaxis_font_size"]))
    # g.ax_heatmap.set_yticklabels(g.ax_heatmap.get_ymajorticklabels(), fontsize = float(pa["xaxis_font_size"]))

    # if type(index_cluster_numbers) != type(None):
    #     index_cluster_numbers_=index_cluster_numbers.copy()
    #     df_=pd.DataFrame( index= index_cluster_numbers_[index_cluster_numbers_.columns.tolist()[0]].tolist() )
    #     df_=pd.merge(df_, tmp, how="left", left_index=True, right_index=True)
    # else:
    #     df_=tmp.copy()

    # if type(cols_cluster_numbers) != type(None):
    #     cols_cluster_numbers_=cols_cluster_numbers.copy()
    #     cols_cluster_numbers_=cols_cluster_numbers_[cols_cluster_numbers_.columns.tolist()[0]].tolist()
    #     df_=df_[cols_cluster_numbers_]

    # df_.reset_index(inplace=True, drop=False)
    # cols=df_.columns.tolist()
    # cols[0]="rows"
    # df_.columns=cols

    return g, cols_cluster_numbers, index_cluster_numbers, df_

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