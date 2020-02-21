import scipy.cluster.hierarchy as sch
import scipy.spatial as scs
from scipy import stats
import plotly.graph_objects as go
import plotly.figure_factory as ff
from scipy.cluster.hierarchy import fcluster
import numpy as np
import pandas as pd

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

    checkboxes=["row_cluster","col_cluster","xticklabels","yticklabels","row_dendogram_dist", "col_dendogram_dist"] # "robust"
    for c in checkboxes:
        if (pa[c] =="on") | (pa[c] ==".on"):
            pa_[c]=True
        else:
            pa_[c]=False

    for v in ["col_color_threshold","row_color_threshold"]:
        if pa[v] == "":
            pa_[v]=None
        else:
            pa_[v]=float(pa[v])

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

    if not pa_["col_color_threshold"]:
        import sys
        print(pa["method_value"],pa["distance_value"])
        sys.stdout.flush()
        fig = ff.create_dendrogram(data_array_, orientation='bottom', labels=labels,\
                            distfun = lambda x: scs.distance.pdist(x, metric=pa["distance_value"]) ,\
                            linkagefun= lambda x: sch.linkage(x, pa["method_value"]))
        dists=[]
        for d in fig["data"]:
            dists.append(d["y"][2])
        color_threshold=abs(np.percentile(dists,50))
        pa_["col_color_threshold"]=color_threshold

    if not pa_["row_color_threshold"]:
        dendro_side = ff.create_dendrogram(data_array, orientation='bottom', labels=rows,\
                            distfun = lambda x: scs.distance.pdist(x, metric=pa["distance_value"]),\
                            linkagefun= lambda x: sch.linkage(x, pa["method_value"]))
        dists=[]
        for d in dendro_side["data"]:
            dists.append(d["x"][2])
        color_threshold=abs(np.percentile(dists,50))
        pa_["row_color_threshold"]=color_threshold
        
    # Initialize figure by creating upper dendrogram
    fig = ff.create_dendrogram(data_array_, orientation='bottom', labels=labels, color_threshold=pa_["col_color_threshold"],\
                            distfun = lambda x: scs.distance.pdist(x, metric=pa["distance_value"]),\
                            linkagefun= lambda x: sch.linkage(x, pa["method_value"]))
    for i in range(len(fig['data'])):
        fig['data'][i]['yaxis'] = 'y2'
    dendro_leaves_y_labels = fig['layout']['xaxis']['ticktext']
    dendro_leaves_y = [ labels.index(i) for i in dendro_leaves_y_labels ]

    d = scs.distance.pdist(data_array_, metric=pa["distance_value"])
    Z = sch.linkage(d, pa["method_value"]) #linkagefun(d)
    max_d = pa_["col_color_threshold"]
    clusters_cols = fcluster(Z, max_d, criterion='distance')
    clusters_cols=pd.DataFrame({"col":tmp.columns.tolist(),"cluster":list(clusters_cols)})

    # Create Side Dendrogram
    dendro_side = ff.create_dendrogram(data_array, orientation='right', labels=rows, color_threshold=pa_["row_color_threshold"],\
                                        distfun = lambda x: scs.distance.pdist(x, metric=pa["distance_value"]),\
                                        linkagefun= lambda x: sch.linkage(x, pa["method_value"] ))
    for i in range(len(dendro_side['data'])):
        dendro_side['data'][i]['xaxis'] = 'x2'
    dendro_leaves_x_labels = dendro_side['layout']['yaxis']['ticktext']
    dendro_leaves_x = [ rows.index(i) for i in dendro_leaves_x_labels ]

    d = scs.distance.pdist(data_array, metric=pa["distance_value"])
    Z = sch.linkage(d, pa["method_value"]) #linkagefun(d)
    max_d =pa_["row_color_threshold"]
    clusters_rows = fcluster(Z, max_d, criterion='distance')
    clusters_rows = pd.DataFrame({"col":tmp.index.tolist(),"cluster":list(clusters_rows)})

    # Add Side Dendrogram Data to Figure
    for data in dendro_side['data']:
        fig.add_trace(data)

    # Create Heatmap
    heat_data=data_array
    heat_data = heat_data[dendro_leaves_x,:]
    heat_data = heat_data[:,dendro_leaves_y]

    heatmap = [
        go.Heatmap(
            x = dendro_leaves_x_labels,
            y = dendro_leaves_y_labels,
            z = heat_data,
            colorscale = pa['colorscale_value'],
            colorbar={"title":{"text":pa["color_bar_label"] ,"font":{"size": float(pa["color_bar_font_size"]) }},
                    "lenmode":"pixels", "len":float(pa["fig_height"])/4,
                    "xpad":float(pa["color_bar_horizontal_padding"]),"tickfont":{"size":float(pa["color_bar_ticks_font_size"])}}
        )
    ]

    heatmap[0]['x'] = fig['layout']['xaxis']['tickvals']
    heatmap[0]['y'] = dendro_side['layout']['yaxis']['tickvals']

    # Add Heatmap Data to Figure
    for data in heatmap:
        fig.add_trace(data)

    # Edit Layout
    fig.update_layout({'width':float(pa["fig_width"]), 'height':float(pa["fig_height"]),
                            'showlegend':False, 'hovermode': 'closest',
                            "yaxis":{"mirror" : "allticks", 
                                    'side': 'right',
                                    'showticklabels':pa_["xticklabels"],
                                    'ticktext':dendro_leaves_x_labels}})

    # Edit xaxis
    fig.update_layout(xaxis={'domain': [ float(pa["row_dendogram_ratio"]), 1],
                                    'mirror': False,
                                    'showgrid': False,
                                    'showline': False,
                                    'zeroline': False,
                                    'showticklabels': pa_["yticklabels"],
                                    "tickfont":{"size":float(pa["yaxis_font_size"])},
                                    'ticks':"",\
                                    'ticktext':dendro_leaves_y_labels})
    # Edit xaxis2
    fig.update_layout(xaxis2={'domain': [0, float(pa["row_dendogram_ratio"])],
                                    'mirror': False,
                                    'showgrid': False,
                                    'showline': False,
                                    'zeroline': False,
                                    'showticklabels': pa_["row_dendogram_dist"],
                                    'ticks':""})

    # Edit yaxis 
    fig.update_layout(yaxis={'domain': [0, 1-float(pa["col_dendogram_ratio"])+0.04 ],
                                    'mirror': False,
                                    'showgrid': False,
                                    'showline': False,
                                    'zeroline': False,
                                    'showticklabels': pa_["xticklabels"],
                                    "tickfont":{"size":float(pa["xaxis_font_size"])} ,
                                    'ticks': "",\
                                    'tickvals':dendro_side['layout']['yaxis']['tickvals'],\
                                    'ticktext':dendro_leaves_x_labels})

    # Edit yaxis2 showticklabels
    fig.update_layout(yaxis2={'domain':[1-float(pa["col_dendogram_ratio"]), 1],
                                    'mirror': False,
                                    'showgrid': False,
                                    'showline': False,
                                    'zeroline': False,
                                    'showticklabels': pa_["col_dendogram_dist"],
                                    'ticks':""})

    fig.update_layout(template='plotly_white')

    fig.update_layout(title={"text":pa["title"],"yanchor":"top","font":{"size":float(pa["title_size_value"])}})

    cols=list(fig['layout']['xaxis']['ticktext'])
    rows=list(fig['layout']['yaxis']['ticktext'])
    df_=pd.DataFrame({"i":range(len(rows))}, index=rows )
    df_=df_.sort_values(by=["i"], ascending=False)
    df_=df_.drop(["i"], axis=1)    
    df_=pd.merge(df_,tmp, how="left", left_index=True, right_index=True)
    df_=df_[cols]

    clusters_cols_=pd.DataFrame({"col":cols})
    clusters_cols=pd.merge(clusters_cols_,clusters_cols,on=["col"],how="left")
    clusters_rows_=pd.DataFrame({"col":df_.index.tolist()})
    clusters_rows=pd.merge(clusters_rows_,clusters_rows,on=["col"],how="left")

    return fig, clusters_cols, clusters_rows, df_

def figure_defaults():
    plot_arguments={
        "fig_width":"800",\
        "fig_height":"800",\
        "xcols":[],\
        "xvals":"",\
        "ycols":[],\
        "yvals":"",\
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
        "col_color_threshold":"",\
        "row_color_threshold":"",\
        "colorscale":['aggrnyl','agsunset','blackbody','bluered','blues','blugrn','bluyl','brwnyl',\
                    'bugn','bupu','burg','burgyl','cividis','darkmint','electric','emrld','gnbu',\
                    'greens','greys','hot','inferno','jet','magenta','magma','mint','orrd','oranges',\
                    'oryel','peach','pinkyl','plasma','plotly3','pubu','pubugn','purd','purp','purples',\
                    'purpor','rainbow','rdbu','rdpu','redor','reds','sunset','sunsetdark','teal',\
                    'tealgrn','viridis','ylgn','ylgnbu','ylorbr','ylorrd','algae','amp','deep','dense',\
                    'gray','haline','ice','matter','solar','speed','tempo','thermal','turbid','armyrose',\
                    'brbg','earth','fall','geyser','prgn','piyg','picnic','portland','puor','rdgy',\
                    'rdylbu','rdylgn','spectral','tealrose','temps','tropic','balance','curl','delta',\
                        'edge','hsv','icefire','phase','twilight','mrybm','mygbm'],\
        "colorscale_value":"blues",\
        "color_bar_label":"",\
        "color_bar_font_size":"10",\
        "color_bar_ticks_font_size":"10",\
        "color_bar_horizontal_padding":"100",\
        "row_cluster":".on",\
        "col_cluster":".on",\
        "robust":".on",\
        "col_dendogram_ratio":"0.15",\
        "row_dendogram_ratio":"0.15",\
        "row_dendogram_dist":".off", \
        "col_dendogram_dist":".off",\
        "zscore":["none","row","columns"],\
        "zscore_value":"none",\
        "xaxis_font_size":"10",\
        "yaxis_font_size":"10",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"heatmap",\
        "session_downloadn":"MySession.iheatmap",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.iheatmap",\
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