#from matplotlib.figure import Figure
import plotly.express as px
import plotly.graph_objects as go

from collections import OrderedDict
import numpy as np

def make_figure(df,pa):
    """Generates figure.

    Args:
        df (pandas.core.frame.DataFrame): Pandas DataFrame containing the input data.
        pa (dict): A dictionary of the style { "argument":"value"} as outputted by `figure_defaults`.

    Returns:
        A Plotly figure
        
    """

    pa_={}
    for n in ["fig_width","fig_height"]:
        if pa[n] == "":
            pa_[n]=None
        else:
            pa_[n]=float(pa[n])

    tmp=df.copy()
    tmp=tmp[pa["vals"]]

    fig = go.Figure( )
    fig.update_layout( width=pa_["fig_width"], height=pa_["fig_height"] ) #  autosize=False,

    # MAIN FIGURE
    pab={}
    for arg in ["show_legend","upper_axis","lower_axis","left_axis","right_axis"]:
        if pa[arg] in ["off",".off"]:
            pab[arg]=False
        else:
            pab[arg]=True

    for h in pa["groups_settings"].values():

        if h["label"]!="":
            name=h["label"]
        else:
            name=""

        if h["color_rgb"] == "" or h["color_rgb"]=="None":
            if h["color_value"]=="None":
                marker_color=None
            else:
                marker_color = h["color_value"]
        else:
            marker_color = GET_COLOR( h["color_rgb"] )
                
        if h[ "line_rgb"] == "" or h["line_rgb"]==None:
            line_color = str(h["line_color"])
        else:
            line_color = GET_COLOR( h["line_rgb"] )

        if h["histnorm"] == "None":
            histnorm = ""
        else:
            histnorm = h["histnorm"]

        if (h["bins_number"] == "") or (h["bins_number"]==None):
            nbins = None
        else:
            nbins = int(h["bins_number"])
            
        if h["fill_alpha"]!=pa["fill_alpha"]:
            opacity=float(h["fill_alpha"])
        else:
            opacity=float(pa["fill_alpha"])
        
        if h["linewidth"]!=pa["linewidth"]:
            linewidth=float(h["linewidth"])
        else:
            linewidth=float(pa["linewidth"])

        if pa["log_scale"]=="on":
            log=True
        else:
            log=False
        
        if h["density"]=="on":
            pa_["density"]=True
        else:
            pa_["density"]=False

        if h["cumulative"]=="on":
            cumulative_enabled=True
        else:
            cumulative_enabled=False

        if h["orientation_value"]=="vertical":
            fig.add_trace(go.Histogram(x=tmp[h["name"]],cumulative_enabled=cumulative_enabled,\
                opacity=opacity,nbinsx=nbins,marker_color=marker_color,name=name))
            
            if pa["log_scale"]==True:
                fig.update_xaxes(type="log")

        else:
            fig.add_trace(go.Histogram(y=tmp[h["name"]],cumulative_enabled=cumulative_enabled,\
                opacity=opacity,nbinsy=nbins,marker_color=marker_color,name=name))

            if pa["log_scale"]==True:
                fig.update_xyaxes(type="log")
    #Update layout of histograms
    fig.update_layout(barmode=pa["barmode"])

    fig.update_xaxes(zeroline=False, showline=pab["lower_axis"], linewidth=float(pa["axis_line_width"]), linecolor='black', mirror=pab["upper_axis"])
    fig.update_yaxes(zeroline=False, showline=pab["left_axis"], linewidth=float(pa["axis_line_width"]), linecolor='black', mirror=pab["right_axis"])

    fig.update_xaxes(ticks=pa["ticks_direction_value"], tickwidth=float(pa["axis_line_width"]), tickcolor='black', ticklen=float(pa["ticks_length"]) )
    fig.update_yaxes(ticks=pa["ticks_direction_value"], tickwidth=float(pa["axis_line_width"]), tickcolor='black', ticklen=float(pa["ticks_length"]) )

    if (pa["x_lower_limit"]!="") and (pa["x_upper_limit"]!="") :
        xmin=float(pa["x_lower_limit"])
        xmax=float(pa["x_upper_limit"])
        fig.update_xaxes(range=[xmin, xmax])

    if (pa["y_lower_limit"]!="") and (pa["y_upper_limit"]!="") :
        ymin=float(pa["y_lower_limit"])
        ymax=float(pa["y_upper_limit"])
        fig.update_yaxes(range=[ymin, ymax])

    if pa["maxxticks"]!="":
        fig.update_yaxes(nticks=int(pa["maxxticks"]))

    if pa["maxyticks"]!="":
        fig.update_yaxes(nticks=int(pa["maxyticks"]))
    
    fig.update_layout(
        title={
            'text': pa['title'],
            'xanchor': 'left',
            'yanchor': 'top' ,
            "font": {"size": float(pa["titles"]) } } )

    fig.update_layout(
        xaxis = dict(
        title_text = pa["xlabel"],
        title_font = {"size": int(pa["xlabels"])}),
        yaxis = dict(
        title_text = pa["ylabel"],
        title_font = {"size": int(pa["xlabels"])} ) )

    fig.update_xaxes(tickangle=float(pa["xticks_rotation"]), tickfont=dict(size=float(pa["xticks_fontsize"])))
    fig.update_yaxes(tickangle=float(pa["yticks_rotation"]), tickfont=dict(size=float(pa["yticks_fontsize"])))


    if pa["grid_value"] != "None":
        if pa["grid_color_text"]!="":
            grid_color=pa["grid_color_text"]
        else:
            grid_color=pa["grid_color_value"]
        if pa["grid_value"] in ["both","x"]:
            fig.update_xaxes(showgrid=True, gridwidth=float(pa["grid_linewidth"]), gridcolor=grid_color)
        else:
            fig.update_xaxes(showgrid=False, gridwidth=float(pa["grid_linewidth"]), gridcolor=grid_color)
        if pa["grid_value"] in ["both","y"]:
            fig.update_yaxes(showgrid=True, gridwidth=float(pa["grid_linewidth"]), gridcolor=grid_color)
        else:
            fig.update_yaxes(showgrid=False, gridwidth=float(pa["grid_linewidth"]), gridcolor=grid_color)
    else:
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)

    fig.update_layout(template='plotly_white')


    if pab["show_legend"]==True:

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

        
        fig.update_layout(showlegend=True,legend_title_text=legend_title)
        fig.update_layout(
        legend=dict(
            font=dict(
            size=legend_body_fontsize,
            ),
            )
        )

    return fig

STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
ALLOWED_MARKERS=['circle', 'circle-open', 'circle-dot', 'circle-open-dot', 'square', 'square-open', 
'square-dot', 'square-open-dot', 'diamond', 'diamond-open', 'diamond-dot', 'diamond-open-dot', 
'cross', 'cross-open', 'cross-dot', 'cross-open-dot', 'x', 'x-open', 'x-dot', 'x-open-dot', 
'triangle-up', 'triangle-up-open', 'triangle-up-dot', 'triangle-up-open-dot', 'triangle-down', 
'triangle-down-open', 'triangle-down-dot', 'triangle-down-open-dot', 'triangle-left', 'triangle-left-open', 
'triangle-left-dot', 'triangle-left-open-dot', 'triangle-right', 'triangle-right-open', 'triangle-right-dot', 
'triangle-right-open-dot', 'triangle-ne', 'triangle-ne-open', 'triangle-ne-dot', 'triangle-ne-open-dot', 
'triangle-se', 'triangle-se-open', 'triangle-se-dot', 'triangle-se-open-dot', 'triangle-sw', 
'triangle-sw-open', 'triangle-sw-dot', 'triangle-sw-open-dot', 'triangle-nw', 'triangle-nw-open',
 'triangle-nw-dot', 'triangle-nw-open-dot', 'pentagon', 'pentagon-open', 'pentagon-dot', 'pentagon-open-dot', 
 'hexagon', 'hexagon-open', 'hexagon-dot', 'hexagon-open-dot', 'hexagon2', 'hexagon2-open', 'hexagon2-dot',
  'hexagon2-open-dot', 'octagon', 'octagon-open', 'octagon-dot', 'octagon-open-dot', 'star', 'star-open', 
  'star-dot', 'star-open-dot', 'hexagram', 'hexagram-open', 'hexagram-dot', 'hexagram-open-dot', 
  'star-triangle-up', 'star-triangle-up-open', 'star-triangle-up-dot', 'star-triangle-up-open-dot', 
  'star-triangle-down', 'star-triangle-down-open', 'star-triangle-down-dot', 'star-triangle-down-open-dot', 
  'star-square', 'star-square-open', 'star-square-dot', 'star-square-open-dot', 'star-diamond', 
  'star-diamond-open', 'star-diamond-dot', 'star-diamond-open-dot', 'diamond-tall', 'diamond-tall-open', 
  'diamond-tall-dot', 'diamond-tall-open-dot', 'diamond-wide', 'diamond-wide-open', 'diamond-wide-dot', 
  'diamond-wide-open-dot', 'hourglass', 'hourglass-open', 'bowtie', 'bowtie-open', 'circle-cross', 
  'circle-cross-open', 'circle-x', 'circle-x-open', 'square-cross', 'square-cross-open', 'square-x', 
  'square-x-open', 'diamond-cross', 'diamond-cross-open', 'diamond-x', 'diamond-x-open', 'cross-thin', 
  'cross-thin-open', 'x-thin', 'x-thin-open', 'asterisk', 'asterisk-open', 'hash', 'hash-open', 
  'hash-dot', 'hash-open-dot', 'y-up', 'y-up-open', 'y-down', 'y-down-open', 'y-left', 'y-left-open', 
  'y-right', 'y-right-open', 'line-ew', 'line-ew-open', 'line-ns', 'line-ns-open', 'line-ne', 
  'line-ne-open', 'line-nw', 'line-nw-open']
STANDARD_COLORS=["blue","green","red","cyan","magenta","yellow","black","white"]
STANDARD_HISTNORMS=['None', 'percent', 'probability', 'density', 'probability density']
STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
STANDARD_COLORS=[None,"blue","green","red","cyan","magenta","yellow","black","white"]
LINE_STYLES=["solid","dashed","dashdot","dotted"]
STANDARD_BARMODES=["stack", "group","overlay","relative"]
STANDARD_ORIENTATIONS=['vertical','horizontal']
STANDARD_ALIGNMENTS=['left','right','mid']
TICKS_DIRECTIONS=["inside","outside",'']
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


    # lists allways need to have thee default value after the list
    # eg.:
    # "title_size":standard_sizes,\
    # "titles":"20"
    # "fig_size_x"="6"
    # "fig_size_y"="6"

def figure_defaults():
    plot_arguments={
        "fig_width":"600",\
        "fig_height":"600",\
        "title":'iHistogram',\
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
        "histnorms":STANDARD_HISTNORMS,\
        "alignment":STANDARD_ALIGNMENTS,\
        "alignment_value":"mid",\
        "barmode":"overlay",\
        "barmodes":STANDARD_BARMODES,\
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
        "downloadn":"ihistogram",\
        "session_downloadn":"MySession.ihistogram.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.ihistogram.plot",\
        "inputargumentsfile":"Select file.."
    }
    return plot_arguments