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

from matplotlib.patches import PathPatch

def adjust_box_widths(g, fac):
    """
    Adjust the widths of a seaborn-generated boxplot.
    """

    # iterating through Axes instances
    for ax in g.axes:

        # iterating through axes artists:
        for c in ax.get_children():

            # searching for PathPatches
            if isinstance(c, PathPatch):
                # getting current width of box:
                p = c.get_path()
                verts = p.vertices
                verts_sub = verts[:-1]
                xmin = np.min(verts_sub[:, 0])
                xmax = np.max(verts_sub[:, 0])
                xmid = 0.5*(xmin+xmax)
                xhalf = 0.5*(xmax - xmin)

                # setting new width of box
                xmin_new = xmid-fac*xhalf
                xmax_new = xmid+fac*xhalf
                verts_sub[verts_sub[:, 0] == xmin, 0] = xmin_new
                verts_sub[verts_sub[:, 0] == xmax, 0] = xmax_new

                # setting new width of median line
                for l in ax.lines:
                    if np.all(l.get_xdata() == [xmin, xmax]):
                        l.set_xdata([xmin_new, xmax_new])


def make_figure(df,pa,fig=None,ax=None):
    """Generates figure.

    Args:
        df (pandas.core.frame.DataFrame): Pandas DataFrame containing the input data.
        pa (dict): A dictionary of the style { "argument":"value"} as outputted by `figure_defaults`.

    Returns:
        A Matplotlib figure
        
    """
   # MAIN FIGURE
    fig, axes = plt.subplots(figsize=(float(pa["fig_width"]),float(pa["fig_height"])))
  
    #UPLOAD ARGUMENTS
    vals=pa["vals"].copy()
    vals.remove(None)
    tmp=df.copy()
    tmp=tmp[vals]



    possible_nones=[ "x_val" , "y_val" , "hue", "order", "hue_order" , "inner","vp_palette",\
        "sp_palette","bp_palette","x_val","y_val","hue","sp_edgecolor","edgecolor","facecolor"]
    for p in possible_nones:
        if pa[p] == "None" :
            pa[p]=None

    #Set Dodge to True by default if user selected Hue
    if pa["hue"]!=None:
        pa["sp_dodge"]="on"
        pa["vp_dodge"]="on"
        pa["bp_dodge"]="on"
    
    pab={}
    for arg in ["upper_axis","lower_axis","left_axis","right_axis",\
        "tick_left_axis","tick_lower_axis","tick_upper_axis","tick_right_axis",\
        "split","sp_dodge","vp_dodge","bp_dodge","scale_hue","shadow","fancybox","markerfirst"]:
        if pa[arg] in ["off",".off"]:
            pab[arg]=False
        else:
            pab[arg]=True

    floats=[ "framealpha", "labelspacing", "columnspacing","handletextpad",\
        "handlelength","borderaxespad","borderpad","cut","bw_float","vp_width","vp_linewidth","vp_saturation",\
        "sp_size","sp_linewidth","sp_saturation","bp_width","bp_saturation","bp_fliersize","bp_linewidth",\
        "bp_whis","group_width"]
    for a in floats:
        if pa[a] == "":
            pab[a]=None
        else:
            pab[a]=float(pa[a])
    
    ints=["gridsize","legend_ncol"]
    for a in ints:
        if pa[a] == "":
            pab[a]=None
        else:
            pab[a]=int(pa[a])
            
    if pa["sp_color_rgb"] != "":
        sp_color=GET_COLOR(pa["sp_color_rgb"]).split(",")
    else:
        if pa["sp_color_value"]=="None":
            sp_color=None
        else:
            sp_color=pa["sp_color_value"]
              
    if pa["vp_color_rgb"] != "":
        vp_color=GET_COLOR(pa["vp_color_rgb"]).split(",")
    else:
        if pa["vp_color_value"]=="None":
            vp_color=None
        else:
            vp_color=pa["vp_color_value"]  
    
    if pa["bp_color_rgb"] != "":
        bp_color=GET_COLOR(pa["bp_color_rgb"]).split(",")
    else:
        if pa["bp_color_value"]=="None":
            bp_color=None
        else:
            bp_color=pa["bp_color_value"]
    
    for each in ["sp_orient","vp_orient","bp_orient"]:
        if pa[each]=="horizontal":
            pab[each]="h"
        elif pa[each]=="vertical":
            pab[each]="v"

    if pab["bw_float"]==None:
        bw=pa["bw"]
    else:
        bw=pab["bw_float"]
    
    scale=pa["scale"]

    #Define color, palette or user input
    if pa["hue"]!=None:
        categories=list(set(tmp[pa["hue"]]))
    else:
        categories=list(set(tmp[pa["x_val"]]))
        print(categories)

    if type(sp_color)==list:
        sp_palette=dict()
        for each,color in zip(categories,sp_color):
            sp_palette[each]=color
        sp_color=None
    else:
        sp_palette=pa["sp_palette"]
    
    if type(vp_color)==list:
        vp_palette=dict()
        for each,color in zip(categories,vp_color):
            vp_palette[each]=color
        vp_color=None

    else:
        vp_palette=pa["vp_palette"]

    if type(bp_color)==list:
        bp_palette=dict()
        for each,color in zip(categories,bp_color):
            bp_palette[each]=color
        bp_color=None
    else:
        bp_palette=pa["bp_palette"]


    #PLOT MAIN FIGURE

    if "Violinplot" in pa["style"]:
        sns.violinplot(x=pa["x_val"],y=pa["y_val"],hue=pa["hue"],data=df,order=pa["order"],hue_order=pa["hue_order"],bw=bw,cut=pab["cut"],scale=scale,\
        scale_hue=pab["scale_hue"],gridsize=pab["gridsize"],width=pab["vp_width"],inner=pa["inner"],split=pab["split"],dodge=pab["vp_dodge"],orient=pab["vp_orient"],\
        linewidth=pab["vp_linewidth"],color=vp_color,palette=vp_palette,saturation=pab["vp_saturation"])
    if "Boxplot" in pa["style"]:
        sns.boxplot(x=pa["x_val"],y=pa["y_val"],hue=pa["hue"],data=df,orient=pab["bp_orient"],color=bp_color,palette=bp_palette,saturation=pab["bp_saturation"],\
        width=pab["bp_width"], dodge=pab["bp_dodge"], fliersize=pab["bp_fliersize"], linewidth=pab["bp_linewidth"], whis=pab["bp_whis"])
    if "Swarmplot" in pa["style"]:
        sns.swarmplot(x=pa["x_val"],y=pa["y_val"],hue=pa["hue"],data=df,dodge=pab["sp_dodge"], orient=pab["sp_orient"], color=sp_color, palette=sp_palette,\
        size=pab["sp_size"], edgecolor=pa["sp_edgecolor"], linewidth=pab["sp_linewidth"], alpha=pab["sp_saturation"])       
    
    #Set group distance
    if pa["hue"]!=None:
        adjust_box_widths(fig, pab["group_width"])

    
    #SET LEGEND OPTIONS
    facecolor= pa["facecolor"]
    edgecolor=pa["edgecolor"]
    loc=pa["legend_loc"]
    mode=pa["mode"]
    legend_title=pa["legend_title"]

    if pa["legend_title_fontsize_value"]!="":
        legend_title_fontsize=pa["legend_title_fontsize_value"]
    else:
        legend_title_fontsize=pa["legend_title_fontsize"]

    if pa["legend_body_fontsize_value"]!="":
        legend_body_fontsize=float(pa["legend_body_fontsize_value"])
    else:
        legend_body_fontsize=pa["legend_body_fontsize"]

    
    plt.legend(loc=loc,ncol=pab["legend_ncol"],fontsize=legend_body_fontsize,\
        markerfirst=pab["markerfirst"],fancybox=pab["fancybox"],shadow=pab["shadow"],framealpha=pab["framealpha"], \
        facecolor=facecolor, edgecolor=edgecolor,mode=mode,title=legend_title,\
        title_fontsize=legend_title_fontsize,borderpad=pab["borderpad"],labelspacing=pab["labelspacing"],\
        handlelength=pab["handlelength"],handletextpad=pab["handletextpad"],\
        borderaxespad=pab["borderaxespad"],columnspacing=pab["columnspacing"])



    #SET GRID, AXIS AND TICKS
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

    if pa["title"]=="":
        title=pa["style"]
    else:
        title=pa["title"]
    plt.title(title, fontsize=float(pa["title_size_value"]))

    plt.tight_layout()


    return fig

STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
LINE_STYLES=["solid","dashed","dashdot","dotted"]
STANDARD_STYLES=["Violinplot","Swarmplot","Boxplot","Violinplot and Swarmplot","Boxplot and Swarmplot"]
BWS=["scott","silverman"]
STANDARD_COLORS=[None,"blue","green","red","cyan","magenta","yellow","black","white"]
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
        "style":"violinplot",\
        "styles":STANDARD_STYLES,\
        "hue":None,\
        "x_val":None,\
        "y_val":None,\
        "cols":[],\
        "vals":[],\
        "order":None,\
        "hue_order":None,\
        "bw":"scott",\
        "bws":BWS,\
        "bw_float":"",\
        "cut":"2",\
        "group_width":"0.7",\
        "colors":STANDARD_COLORS,\
        "sp_color_value":"None",\
        "sp_color_rgb":"",\
        "vp_color_value":"None",\
        "vp_color_rgb":"",\
        "bp_color_value":"None",\
        "bp_color_rgb":"",\
        "bp_width":"0.8",\
        "bp_fliersize":"5",\
        "bp_whis":"1.5",\
        "sp_edgecolor":None,\
        "sp_linewidth":"",\
        "bp_linewidth":"",\
        "vp_linewidth":"",\
        "gridsize":"100",\
        "scale":"area",\
        "scales":STANDARD_SCALES,\
        "scale_hue":".off",\
        "vp_width":"0.8",\
        "inner":"box",\
        "inner_values":STANDARD_INNER,\
        "split":".off",\
        "vp_dodge":"on",\
        "sp_dodge":"on",\
        "bp_dodge":"on",\
        "vp_orient":"vertical",\
        "sp_orient":"vertical",\
        "bp_orient":"vertical",\
        "orientations":STANDARD_ORIENTATIONS,\
        "vp_palette":None,\
        "sp_palette":None,\
        "bp_palette":None,\
        "palettes":STANDARD_PALETTES,\
        "sp_size":"5",\
        "vp_saturation":"0.75",\
        "bp_saturation":"0.75",\
        "sp_saturation":"0.75",\
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
        "downloadn":"scatterplot",\
        "session_downloadn":"MySession.violin.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.violin.plot",\
        "inputargumentsfile":"Select file.."
    }
    #grid colors not implemented in UI
    return plot_arguments

    

    
    

        

            



