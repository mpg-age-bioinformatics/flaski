import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pylab as plt
import sys
matplotlib.use('agg')

def GET_COLOR(x):
    if str(x)[:3].lower() == "rgb":
        vals=x.split("rgb(")[-1].split(")")[0].split(",")
        vals=[ float(s.strip(" ")) for s in vals ]
        #vals=tuple(vals)
        return vals
    else:
        return str(x)
        

def make_figure(df,pa):
    
    tmp=df.copy()
    tmp=tmp[pa["vals"]]


    fig, axes = plt.subplots(1, 1,figsize=(float(pa["fig_width"]),float(pa["fig_height"])))
    
#
#    values=pa["values"].split(",")
#    values=[ s.rstrip("\r") for s in values ]
#    values=[ s for s in values if s != "" ]
    for h in pa["groups_settings"].values():
        pa_={}
        if h["color_rgb"] != "":
            pa_["color_value"] = GET_COLOR( h["color_rgb"] )
        else:
            if h["color_value"]=="None":
                h["color_value"]=None
                pa_["color_value"] = h["color_value"]
            else:
                pa_["color_value"] = h["color_value"]
                
        if h[ "line_rgb"] != "":
            pa_["line_color"] = GET_COLOR( h["line_rgb"] )
        else:
            if h["line_color"]=="None":
                h["line_color"]=None
                pa_["line_color"] = h["line_color"]
            else:
                pa_["line_color"] = h["line_color"]

        if h["bins_number"] != "":
            pa_["bins_number"] = int(h["bins_number"])
        else:
            pa_["bins_number"] = h["bins_value"]


        
        if h[ "label"] != "":
            pa_["label"] = h["label"]
        else:
            pa_["label"] = h["name"]
            
        if h["log_scale"] == "on":
            pa_["log_scale"]=False
        else:
            pa_["log_scale"]=True
            
        if h["fill_alpha"]!=pa["fill_alpha"]:
            pa_["fill_alpha"]=float(h["fill_alpha"])
        else:
            pa_["fill_alpha"]=float(pa["fill_alpha"])
        
        if h["linewidth"]!=pa["linewidth"]:
            pa_["linewidth"]=float(h["linewidth"])
        else:
            pa_["linewidth"]=float(pa["linewidth"])
            
        
        if pa_["line_color"]!=None:
            plt.hist(x=h["values"],bins=pa_["bins_number"],histtype=h["histtype_value"],orientation=h["orientation_value"],label=pa_["label"],color=pa_["color_value"], alpha=pa_["fill_alpha"],lw=pa_["linewidth"],edgecolor=pa_["line_color"],log=pa_["log_scale"],linestyle=h["linestyle_value"])
        else:
            plt.hist(x=h["values"],bins=pa_["bins_number"],histtype=h["histtype_value"],orientation=h["orientation_value"],label=pa_["label"],color=pa_["color_value"], alpha=pa_["fill_alpha"],lw=pa_["linewidth"],log=pa_["log_scale"],linestyle=h["linestyle_value"])
            


    plt.title(pa["title"], fontsize=float(pa["title_size_value"]))
    plt.legend()
    locs, labels = plt.xticks()
    min_loc=min(locs)
    max_loc=max(locs)
    step_loc=(max_loc-min_loc)/10
    min_label=min(tmp.min())
    max_label=max(tmp.max())
    step_label=(max_label-min_label)/10
    plt.xticks(np.arange(min_loc,max_loc,step_loc),np.around(np.arange(min_label,max_label,step_label),2))


    return fig

STANDARD_BINS=['auto', 'sturges','fd','doane', 'scott','rice','sqrt']
STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
STANDARD_COLORS=[None,"blue","green","red","cyan","magenta","yellow","black","white"]
LINE_STYLES=["solid","dashed","dashdot","dotted"]
HIST_TYPES=['bar', 'barstacked', 'step',  'stepfilled']
#LOG_TYPES=[False,True]
STANDARD_ORIENTATIONS=['vertical','horizontal']
STANDARD_ALIGNMENTS=['left','right','mid']

def figure_defaults():
    plot_arguments={
        "fig_width":"6.0",\
        "fig_height":"6.0",\
        "title":'Histogram',\
        "title_size":STANDARD_SIZES,\
        "title_size_value":"20",\
        "fill_alpha":0.8,\
        "linewidth":1.0,\
        "cols":[],\
        "groups":[],\
        "vals":[],\
        "list_of_groups":[],\
        "groups_settings":dict(),\
        "show_legend":".on",\
        "log_scale":".off",\
        "legend_font_size":"14",\
        "colors":STANDARD_COLORS,\
        "bins":STANDARD_BINS,\
        "alignment":STANDARD_ALIGNMENTS,\
        "alignment_value":"mid",\
        "hist_types":HIST_TYPES,\
        "histtype_value":"bar",\
        "linestyles":LINE_STYLES,\
        "linestyle_value":"",\
        "orientations":STANDARD_ORIENTATIONS, \
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"Histogram",\
        "session_downloadn":"MySession.histogram.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.histogram.plot",\
        "inputargumentsfile":"Select file.."
    }
    # grid colors not implemented in UI


    checkboxes=["show_legend","log_scale"]

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
