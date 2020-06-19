from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
from collections import OrderedDict
import numpy as np
import seaborn as sns
import inspect

from adjustText import adjust_text


import mpld3

matplotlib.use('agg')


def GET_COLOR(x):
    if str(x)[:3].lower() == "rgb":
        vals=x.split("rgb(")[-1].split(")")[0].split(",")
        vals=[ float(s.strip(" ")) for s in vals ]
        return vals
    else:
        return str(x)


def make_figure(df,pa,fig=None,ax=None):
    """Generates figure.

    Args:
        df (pandas.core.frame.DataFrame): Pandas DataFrame containing the input data.
        pa (dict): A dictionary of the style { "argument":"value"} as outputted by `figure_defaults`.

    Returns:
        A Matplotlib figure
        
    """

    #matplotlib.rcParams['axes.linewidth'] = float(pa["axis_line_width"])

    # MAIN FIGURE
    fig, axes = plt.subplots(figsize=(float(pa["fig_width"]),float(pa["fig_height"])))
        
    #UPLOAD ARGUMENTS
    tmp=df.copy()
    tmp=tmp[pa["vals"]]
    x=pa["x_vals"]
    y=pa["y_vals"]
    hue=pa["hue"]
    scale=pa["scale"]
    scale_hue=pa["scale_hue"]
    split=pa["split"]
    dodge=pa["dodge"]

    if pa["order"]=="None":
        order=None
    else:
        order=pa["order"]
    
    if pa["hue_order"]=="None":
        hue_order=None
    else:
        hue_order=pa["hue_order"]
                
    if pa["color_rgb"] != "":
        color=GET_COLOR(pa["color_rgb"])
    else:
        if pa["color_value"]=="default":
            color=None
        else:
            color=pa["color_value"]
    
    if pa["cut"]!="":
        cut=float(pa["cut"])
    else:
        cut=2

    if pa["bw_float"]!="":
        bw=float(pa["bw_float"])
    else:
        bw=pa["bw"]
    
    if pa["gridsize"]!="":
        gridsize=int(pa["gridsize"])
    else:
        gridsize=100

    if pa["v_width"]!="":
        v_width=float(pa["v_width"])
    else:
        v_width=0.8
    
    if pa["inner"]=="None":
        inner=None
    else:
        inner=pa["inner"]

    if pa["linewidth"]!="":
        linewidth=float(pa["linewidth"])
    else:
        linewidth=None

    if pa["palette"]=="None":
        palette=None
    else:
        palette=pa["palette"]

    if pa["saturation"]=="":
        saturation=float(pa["saturation"])
    else:
        saturation=0.75
    
    if pa["orient"]=="None":
        orient=None
    else:
        orient=pa["orient"]

    if pa["default"]!="on":
        sns.violinplot(x=x,y=y,hue=hue,data=tmp,order=order,hue_order=hue_order,bw=bw,cut=cut,scale=scale,\
        scale_hue=scale_hue,gridsize=gridsize,width=v_width,inner=inner,split=split,dodge=dodge,orient=orient,\
        linewidth=linewidth,color=color,saturation=saturation)
    else:
        sns.violinplot(data=tmp,bw=bw,cut=cut,scale=scale,gridsize=gridsize,width=v_width,inner=inner,orient=orient,\
        linewidth=linewidth,color=color,saturation=saturation)

    #Plot grid, axes and ticks
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

    plt.title(pa["title"], fontsize=float(pa["title_size_value"]))

    plt.tight_layout()


    return fig

STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
LINE_STYLES=["solid","dashed","dashdot","dotted"]

BWS=["scott","silverman"]
STANDARD_COLORS=["blue","green","red","cyan","magenta","yellow","black","white","default"]
STANDARD_SCALES=["area","count","width"]
STANDARD_INNER=["box", "quartile", "point", "stick", None]
STANDARD_PALETTES=["deep", "muted", "bright", "pastel", "dark", "colorblind",None]
STANDARD_ORIENTATIONS=["vertical","horizontal"]
STANDARD_ALIGNMENTS=['left','right','mid']
TICKS_DIRECTIONS=["in","out", "inout"]
LEGEND_LOCATIONS=['best','upper right','upper left','lower left','lower right','right','center left','center right','lower center','upper center','center']
LEGEND_FONTSIZES=['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large']
MODES=["expand",None]

def figure_defaults():
    """Generates default figure arguments.

    Returns:
        dict: A dictionary of the style { "argument":"value"}
    """
    
    # https://matplotlib.org/3.1.1/api/markers_api.html
    # https://matplotlib.org/2.0.2/api/colors_api.html


    # lists allways need to have the default value after the list
    # eg.:
    # "title_size":standard_sizes,\
    # "titles":"20"
    # "fig_size_x"="6"
    # "fig_size_y"="6"

    plot_arguments={
        "fig_width":"6.0",\
        "fig_height":"6.0",\
        "title":'Violin plot',\
        "title_size_value":"20",\
        "title_size":STANDARD_SIZES,\
        "titles":"20",\
        "default":"on",\
        "hue":None,\
        "x_vals":None,\
        "y_vals":None,\
        "cols":[],\
        "vals":[],\
        "order":None,\
        "hue_order":None,\
        "bw":"scott",\
        "bws":BWS,\
        "bw_float":"",\
        "cut":"2",\
        "colors":STANDARD_COLORS,\
        "color_value":"default",\
        "color_rgb":"",\
        "gridsize":"100",\
        "scale":"area",\
        "scales":STANDARD_SCALES,\
        "scale_hue":True,\
        "v_width":"0.8",\
        "linewidth":"",\
        "inner":"box",\
        "inner_values":STANDARD_INNER,\
        "split":False,\
        "dodge":True,\
        "orient":None,\
        "orientations":STANDARD_ORIENTATIONS,\
        "palette":None,\
        "palettes":STANDARD_PALETTES,\
        "saturation":"0.75",\
        "axis_line_width":1.0,\
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
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"scatterplot",\
        "session_downloadn":"MySession.scatter.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.scatter.plot",\
        "inputargumentsfile":"Select file.."
    }
    # grid colors not implemented in UI
    return plot_arguments

    

    
    

        

            



