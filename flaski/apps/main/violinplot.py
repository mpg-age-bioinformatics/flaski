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
    fig, ax = plt.subplots(figsize=(float(pa["fig_width"]),float(pa["fig_height"])))
    
    plt.title(pa['title'], fontsize=int(pa["titles"]))
    
    #UPLOAD ARGUMENTS
    tmp=df.copy()
    tmp=tmp[pa["vals"]]
    x=pa["x_vals"]
    y=pa["y_vals"]
    hue=pa["hue"]
    scale=pa["scale"]
    scale_hue=pa["scale_hue"]
    data=df
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
        color=pa["color_rgb"]
    else:
        color=pa["color_value"]
    
    if pa["cut"]!="":
        cut=float(pa["cut"])
    else:
        cut=2

    if pa["bw_float"]!="":
        bw=pa["bw_float"]
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

    sns.violinplot(x=x,y=y,hue=hue,data=tmp,order=order,hue_order=hue_order,bw=bw,cut=cut,scale=scale,\
        scale_hue=scale_hue,gridsize=gridsize,width=v_width,inner=inner,split=split,dodge=dodge,orient=orient,\
        linewidth=linewidth,color=color,palette=palette,saturation=saturation)
    
    return fig

STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
BWS=["scott","silverman"]
STANDARD_COLORS=["blue","green","red","cyan","magenta","yellow","black","white"]
STANDARD_SCALES=["area","count","width"]
STANDARD_INNER=["box", "quartile", "point", "stick", None]
STANDARD_PALETTES=["deep", "muted", "bright", "pastel", "dark", "colorblind",None]
ORIENTATIONS=["vertical","horizontal"]

def figure_defaults():
    """Generates default figure arguments.

    Returns:
        dict: A dictionary of the style { "argument":"value"}
    """
    
    # https://matplotlib.org/3.1.1/api/markers_api.html
    # https://matplotlib.org/2.0.2/api/colors_api.html


    # lists allways need to have thee default value after the list
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
        "color_value":None,\
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
        "orientations":ORIENTATIONS,\
        "palette":None,\
        "palettes":STANDARD_PALETTES,\
        "saturation":"0.75",\
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

    

    
    

        

            



