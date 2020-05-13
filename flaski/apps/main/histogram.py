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
        

def make_figure(pa):

    fig, axes = plt.subplots(1, 1,figsize=(float(pa["fig_width"]),float(pa["fig_height"])))


    pa_={}
    
    values=pa["values"].split(",")
    values=[ s.rstrip("\r") for s in values ]
    values=[ s for s in values if s != "" ]

    if pa[ "color_rgb"] != "":
        pa_["color_value"] = GET_COLOR( pa["color_rgb"] )
    else:
        pa_["color_value"] = pa["color_value"]

    if pa[ "bins_number"] != "":
        pa_["bins_number"] = int(pa["bins_number"])
    else:
        pa_["bins_number"] = pa["bins_value"]
        
    if pa[ "line_rgb"] != "":
        pa_["line_color"] = GET_COLOR( pa["line_rgb"] )
    else:
        pa_["line_color"] = pa["line_color"]
    
    
        
    plt.hist(values,color=pa["color_value"],bins=pa_["bins_number"],orientation=pa["orientation_value"], histtype=pa["histtype_value"], alpha=float(pa["fill_alpha"]),linewidth=pa["linewidth"],edgecolor=pa_["line_color"],ls=pa["linestyle_value"])
    
    plt.title(pa["title"], fontsize=float(pa["title_size_value"]))

    return fig

STANDARD_BINS=['auto', 'sturges','fd','doane', 'scott','rice','sqrt']
STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
STANDARD_COLORS=["blue","green","red","cyan","magenta","yellow","black","white"]
LINE_STYLES=["solid","dashed","dashdot","dotted","None"]
HIST_TYPES=['bar', 'barstacked', 'step',  'stepfilled']
STANDARD_ORIENTATIONS=['vertical','horizontal']

def figure_defaults():
    plot_arguments={
        "fig_width":"6.0",\
        "fig_height":"6.0",\
        "title":'Histogram',\
        "title_size":STANDARD_SIZES,\
        "title_size_value":"20",\
        "values":"Enter values separated by a comma",\
        "colors":STANDARD_COLORS,\
        "color_value":"blue",\
        "color_rgb":"",\
        "bins":STANDARD_BINS,\
        "bins_value":"auto",\
        "bins_number":"",\
        "hist_types":HIST_TYPES,\
        "histtype_value":"bar",\
        "line_alpha":"1.0",\
        "fill_alpha":"0.5",\
        "linewidth":"0.2",\
        "linestyles":LINE_STYLES,\
        "linestyle_value":"",\
        "orientations":STANDARD_ORIENTATIONS, \
        "orientation_value":"",\
        "alpha":"0.8",\
        "line_color":"blue",\
        "line_rgb":"",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"histogram",\
        "session_downloadn":"MySession.histogram.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.histogram.plot",\
        "inputargumentsfile":"Select file.."
    }
    # grid colors not implemented in UI


    checkboxes=[]

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
