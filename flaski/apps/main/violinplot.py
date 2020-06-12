from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
from collections import OrderedDict
import numpy as np
import seaborn as sns


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
    
    #IF THE USER IS GOING TO PLOT A DEFAULT VIOLIN PLOT
    if pa["default"]=="on":
    
        if pa["color_rgb"] != "":
            color=pa["color_rgb"]
        else:
            color=pa["color_value"]
        
        if pa["cut"]!="":
            cut=pa["cut"]
        
        
    sns.violinplot(data=df)
    
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
        "title":'Scatter plot',\
        "title_size":STANDARD_SIZES,\
        "titles":"20",\
        "default":"on",\
        "hue":"",\
        "x_vals":"",\
        "y_vals":"",\
        "cols":[],\
        "vals":[],\
        "order":[],\
        "order_hue":[],\
        "bw":"",\
        "bws":BWS,\
        "bw_float":"",\
        "cut":"",\
        "colors":STANDARD_COLORS,\
        "color_value":"",\
        "color_rgb":"",\
        "scale":"",\
        "scales":STANDARD_SCALES,\
        "scale_hue":False,\
        "v_width":"",\
        "linewidth":"",\
        "inner_values":STANDARD_INNER,\
        "split":False,\
        "dodge":False,\
        "orientation":"",\
        "orientations":ORIENTATIONS,\
        "pallete":"",\
        "palletes":STANDARD_PALETTES,\
        "saturation":"",\
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

    

    
    

        

            



