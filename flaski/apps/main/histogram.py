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

    """Generates figure.

    Args:
        df (pandas.core.frame.DataFrame): Pandas DataFrame containing the input data.
        pa (dict): A dictionary of the style { "argument":"value"} as outputted by `figure_defaults`.

    Returns:
        A Plotly figure
        
    """
    
    tmp=df.copy()
    tmp=tmp[pa["vals"]]



    fig, axes = plt.subplots(1, 1,figsize=(float(pa["fig_width"]),float(pa["fig_height"])))
    
    #Read histogram arguments and plot one histogram per column selected by user

    for h in pa["groups_settings"].values():
        pa_={}
        if h["color_rgb"] == "" or h["color_rgb"]=="None":
            if h["color_value"]=="None":
                pa_["color_value"]=None
            else:
                pa_["color_value"] = h["color_value"]
        else:
            pa_["color_value"] = GET_COLOR( h["color_rgb"] )
                
        if h[ "line_rgb"] == "" or h["line_rgb"]==None:
            pa_["line_color"] = str(h["line_color"])
        else:
            pa_["line_color"] = GET_COLOR( h["line_rgb"] )

        if (h["bins_number"] == "") or (h["bins_number"]==None):
            pa_["bins_number"] = h["bins_value"]
        else:
            pa_["bins_number"] = int(h["bins_number"])
            
        if h["fill_alpha"]!=pa["fill_alpha"]:
            pa_["fill_alpha"]=float(h["fill_alpha"])
        else:
            pa_["fill_alpha"]=float(pa["fill_alpha"])
        
        if h["linewidth"]!=pa["linewidth"]:
            pa_["linewidth"]=float(h["linewidth"])
        else:
            pa_["linewidth"]=float(pa["linewidth"])

        if pa["log_scale"]=="on":
            pa_["log_scale"]=True
        else:
            pa_["log_scale"]=False
        
        if h["density"]=="on":
            pa_["density"]=True
        else:
            pa_["density"]=False

        if h["cumulative"]=="on":
            pa_["cumulative"]=True
        else:
            pa_["cumulative"]=False

        if pa_["line_color"]=="None":
            plt.hist(x=h["values"],bins=pa_["bins_number"],histtype=h["histtype_value"],orientation=h["orientation_value"],\
            color=pa_["color_value"], alpha=pa_["fill_alpha"],lw=pa_["linewidth"],log=pa_["log_scale"],linestyle=h["linestyle_value"],\
            cumulative=pa_["cumulative"],density=pa_["density"])
        else:
            plt.hist(x=h["values"],bins=pa_["bins_number"],histtype=h["histtype_value"],orientation=h["orientation_value"],\
            color=pa_["color_value"], alpha=pa_["fill_alpha"],lw=pa_["linewidth"],edgecolor=pa_["line_color"],log=pa_["log_scale"],\
            linestyle=h["linestyle_value"],cumulative=pa_["cumulative"],density=pa_["density"])



    for axis in ['top','bottom','left','right']:
        axes.spines[axis].set_linewidth(float(pa["axis_line_width"]))

    for axis,argv in zip(['top','bottom','left','right'], [pa["upper_axis"],pa["lower_axis"],pa["left_axis"],pa["right_axis"]]):
        if (argv =="on") | (argv ==".on"):
            axes.spines[axis].set_visible(True)
        else:
            axes.spines[axis].set_visible(False)

    ticks={}
    for axis,argv in zip(['top','bottom','left','right'], \
        [pa["tick_upper_axis"],pa["tick_lower_axis"],pa["tick_left_axis"],pa["tick_right_axis"]]):
        if (argv =="on") | (argv ==".on"):
            show=True
        else:
            show=False
        ticks[axis]=show

    axes.tick_params(right= ticks["right"],top=ticks["top"],\
        left=ticks["left"], bottom=ticks["bottom"])

    axes.tick_params(direction=pa["ticks_direction_value"], width=float(pa["axis_line_width"]),length=float(pa["ticks_length"]))  

    if (pa["x_lower_limit"]!="") or (pa["x_upper_limit"]!="") :
        xmin, xmax = axes.get_xlim()
        if pa["x_lower_limit"]!="":
            xmin=float(pa["x_lower_limit"])
        if pa["x_upper_limit"]!="":
            xmax=float(pa["x_upper_limit"])
        plt.xlim(xmin, xmax)

    if (pa["y_lower_limit"]!="") or (pa["y_upper_limit"]!="") :
        ymin, ymax = axes.get_ylim()
        if pa["y_lower_limit"]!="":
            ymin=float(pa["y_lower_limit"])
        if pa["y_upper_limit"]!="":
            ymax=float(pa["y_upper_limit"])
        plt.ylim(xmin, ymax)

    if pa["maxxticks"]!="":
        axes.xaxis.set_major_locator(plt.MaxNLocator(int(pa["maxxticks"])))

    if pa["maxyticks"]!="":
        axes.yaxis.set_major_locator(plt.MaxNLocator(int(pa["maxyticks"])))

    plt.xlabel(pa["xlabel"], fontsize=int(pa["xlabels"]))
    plt.ylabel(pa["ylabel"], fontsize=int(pa["ylabels"]))

    plt.xticks(fontsize=float(pa["xticks_fontsize"]), rotation=float(pa["xticks_rotation"]))
    plt.yticks(fontsize=float(pa["yticks_fontsize"]), rotation=float(pa["yticks_rotation"]))

    if pa["grid_value"] != "None":
        if pa["grid_color_text"]!="":
            grid_color=GET_COLOR(pa["grid_color_text"])
        else:
            grid_color=GET_COLOR(pa["grid_color_value"])

        axes.grid(axis=pa["grid_value"], color=grid_color, linestyle=pa["grid_linestyle_value"], linewidth=float(pa["grid_linewidth"]), alpha=float(pa["grid_alpha"]) )

    if pa["show_legend"]!="off":

        labels=[x["label"] for x in pa["groups_settings"].values()]
        facecolor= pa["facecolor"]
        edgecolor=pa["edgecolor"]
        loc=pa["legend_loc"]
        ncol=int(pa["legend_ncol"])
        mode=pa["mode"]
        legend_title=pa["legend_title"]

        if pa["markerfirst"]=="on":
            markerfirst=True
        else:
            markerfirst=False
        
        if pa["fancybox"]== "on":
            fancybox=True
        else:
            fancybox=False

        if pa["shadow"]=="on":
            shadow=True
        else:
            shadow=False

        if pa["framealpha"]=="":
            framealpha=None
        else:
            framealpha=float(pa["framealpha"])
        
        if pa["labelspacing"]=="":
            labelspacing=None
        else:
            labelspacing=float(pa["labelspacing"])
        
        if pa["columnspacing"]=="":
            columnspacing=None
        else:
            columnspacing=float(pa["columnspacing"])

        if pa["handletextpad"]=="":
            handletextpad=None
        else:
            handletextpad=float(pa["handletextpad"])

        if pa["handlelength"]=="":
            handlelength=None
        else:
            handlelength=float(pa["handlelength"])

        if pa["borderaxespad"]=="":
            borderaxespad=None
        else:
            borderaxespad=float(pa["borderaxespad"])

        if pa["borderpad"]=="":
            borderpad=None
        else:
            borderpad=float(pa["borderpad"])

        if pa["legend_title_fontsize_value"]!="":
            legend_title_fontsize=pa["legend_title_fontsize_value"]
        else:
            legend_title_fontsize=pa["legend_title_fontsize"]

        if pa["legend_body_fontsize_value"]!="":
            legend_body_fontsize=float(pa["legend_body_fontsize_value"])
        else:
            legend_body_fontsize=pa["legend_body_fontsize"]

        
        plt.legend(labels=labels,loc=loc,ncol=ncol,fontsize=legend_body_fontsize,\
            markerfirst=markerfirst,fancybox=fancybox,shadow=shadow,framealpha=framealpha, \
            facecolor=facecolor, edgecolor=edgecolor,mode=mode,title=legend_title,\
            title_fontsize=legend_title_fontsize,borderpad=borderpad,labelspacing=labelspacing,\
            handlelength=handlelength,handletextpad=handletextpad,\
            borderaxespad=borderaxespad,columnspacing=columnspacing)



    plt.title(pa["title"], fontsize=float(pa["title_size_value"]))

    plt.tight_layout()


    return fig

STANDARD_BINS=['auto', 'sturges','fd','doane', 'scott','rice','sqrt']
STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
STANDARD_COLORS=[None,"blue","green","red","cyan","magenta","yellow","black","white"]
LINE_STYLES=["solid","dashed","dashdot","dotted"]
HIST_TYPES=['bar', 'barstacked', 'step',  'stepfilled']
#LOG_TYPES=[False,True]
STANDARD_ORIENTATIONS=['vertical','horizontal']
STANDARD_ALIGNMENTS=['left','right','mid']
TICKS_DIRECTIONS=["in","out", "inout"]
LEGEND_LOCATIONS=['best','upper right','upper left','lower left','lower right','right','center left','center right','lower center','upper center','center']
LEGEND_FONTSIZES=['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large']
MODES=["expand",None]

def figure_defaults():
    plot_arguments={
        "fig_width":"6.0",\
        "fig_height":"6.0",\
        "title":'Histogram',\
        "title_size":STANDARD_SIZES,\
        "title_size_value":"20",\
        "titles":"20",\
        "fill_alpha":0.8,\
        "linewidth":1.0,\
        "show_legend":"on",\
        "axis_line_width":1.0,\
        "cols":[],\
        "groups":[],\
        "vals":[],\
        "list_of_groups":[],\
        "groups_settings":dict(),\
        "log_scale":".off",\
        "colors":STANDARD_COLORS,\
        "bins":STANDARD_BINS,\
        "alignment":STANDARD_ALIGNMENTS,\
        "alignment_value":"mid",\
        "hist_types":HIST_TYPES,\
        "histtype_value":"bar",\
        "linestyles":LINE_STYLES,\
        "linestyle_value":"",\
        "orientations":STANDARD_ORIENTATIONS, \
        "xlabel_size":STANDARD_SIZES,\
        "ylabel_size":STANDARD_SIZES,\
        "xlabel":"",\
        "ylabel":"",\
        "xlabels":"14",\
        "ylabels":"14",\
        "left_axis":".on" ,\
        "right_axis":".on",\
        "upper_axis":".on",\
        "lower_axis":".on",\
        "tick_left_axis":".on" ,\
        "tick_right_axis":".off",\
        "tick_upper_axis":".off",\
        "tick_lower_axis":".on",\
        "ticks_direction":TICKS_DIRECTIONS,\
        "ticks_direction_value":TICKS_DIRECTIONS[1],\
        "ticks_length":"6.0",\
        "xticks_fontsize":"14",\
        "yticks_fontsize":"14",\
        "xticks_rotation":"0",\
        "yticks_rotation":"0",\
        "x_lower_limit":"",\
        "y_lower_limit":"",\
        "x_upper_limit":"",\
        "y_upper_limit":"",\
        "maxxticks":"",\
        "maxyticks":"",\
        "grid":["None","both","x","y"],\
        "grid_value":"None",\
        "grid_color_text":"",\
        "grid_colors":STANDARD_COLORS,\
        "grid_color_value":"black",\
        "grid_linestyle":['-', '--', '-.', ':'],\
        "grid_linestyle_value":'--',\
        "grid_linewidth":"1",\
        "grid_alpha":"0.1",\
        "legend_loc":"best",\
        "legend_locations":LEGEND_LOCATIONS,\
        "legend_ncol": "1",\
        "legend_fontsizes":LEGEND_FONTSIZES,\
        "legend_body_fontsize":"small",\
        "legend_title_fontsize":"14",\
        "legend_body_fontsize_value":"",
        "legend_title_fontsize_value":"",
        "markerfirst":"on",\
        "fancybox":"on",\
        "shadow":".off",\
        "framealpha":"",\
        "facecolor":None,\
        "edgecolor":None,\
        "mode":None,\
        "modes":MODES,\
        "legend_title":"",\
        "borderpad":"",\
        "handlelength":"",\
        "labelspacing":"",\
        "handletextpad":"",\
        "borderaxespad":"",\
        "columnspacing":"",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"Histogram",\
        "session_downloadn":"MySession.histogram.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.histogram.plot",\
        "inputargumentsfile":"Select file.."
    }
    return plot_arguments