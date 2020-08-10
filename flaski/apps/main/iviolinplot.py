#from matplotlib.figure import Figure
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from collections import OrderedDict
import numpy as np

def GET_COLOR(x):
    if str(x)[:3].lower() == "rgb":
        vals=x.split("rgb(")[-1].split(")")[0].split(",")
        vals=[ float(s.strip(" ")) for s in vals ]
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
    #UPLOAD ARGUMENTS
    vals=pa["vals"].copy()
    vals.remove(None)
    tmp=df.copy()
    tmp=tmp[vals]

    fig = go.Figure( )

    # MAIN FIGURE
    #Load checkboxes
    pab={}
    for arg in ["show_legend","upper_axis","lower_axis","left_axis","right_axis",\
        "tick_left_axis","tick_lower_axis","tick_upper_axis","tick_right_axis"]:
        if pa[arg] in ["off",".off"]:
            pab[arg]=False
        else:
            pab[arg]=True

    #Load floats
    floats=["x","y","axis_line_width","ticks_line_width","opacity",\
        "ticks_length","x_lower_limit","x_upper_limit","y_lower_limit","y_upper_limit","spikes_thickness","xticks_rotation",\
        "yticks_rotation","xticks_fontsize","yticks_fontsize","grid_width","legend_borderwidth","legend_tracegroupgap","legend_x",\
        "legend_y","fig_width","fig_height","vp_width","vp_bw","vp_linewidth","vp_pointpos","vp_jitter","vp_meanline_width","vp_marker_opacity",\
        "vp_marker_size","vp_marker_line_width","vp_marker_line_outlierwidth"]

    for a in floats:
        if pa[a] == "" or pa[a]=="None" or pa[a]==None:
            pab[a]=None
        else:
            pab[a]=float(pa[a])

    #Load integers
    integers=["label_fontsize","legend_fontsize","legend_title_fontsize","title_fontsize","maxxticks","maxyticks",\
        "vp_hover_fontsize"]
    for a in integers:
        if pa[a] == "" or pa[a]=="None" or pa[a]==None:
            pab[a]=None
        else:
            pab[a]=int(pa[a])

    #Load Nones
    possible_nones=["title_fontcolor","axis_line_color","ticks_color","spikes_color","label_fontcolor",\
    "paper_bgcolor","plot_bgcolor","grid_color","legend_bgcolor","legend_bordercolor","legend_fontcolor","legend_title_fontcolor",\
    "title_fontfamily","label_fontfamily","legend_fontfamily","legend_title_fontfamily","vp_hover_bgcolor","vp_hover_bordercolor",\
    "vp_hover_fontfamily","vp_hover_fontcolor","vp_linecolor","vp_meanline_color","vp_marker_outliercolor","vp_marker_fillcolor",\
    "vp_marker_line_color","vp_marker_line_outliercolor"]
    for p in possible_nones:
        if pa[p] == "None" or pa[p]=="Default" :
            pab[p]=None
        else:
            pab[p]=pa[p]

    if pa["vp_orient"]=="horizontal":
        pab["vp_orient"]="h"
    else:
        pab["vp_orient"]="v"

    if pa["vp_color_rgb"] != "":
        vp_color=GET_COLOR(pa["vp_color_rgb"])
    else:
        if pa["vp_color_value"]=="None":
            vp_color=None
        else:
            vp_color=pa["vp_color_value"]  

    #MAIN BODY
    hoverlabel=dict(bgcolor=pab["vp_hover_bgcolor"],bordercolor=pab["vp_hover_bordercolor"],\
        font=dict(family=pab["vp_hover_fontfamily"],size=pab["vp_hover_fontsize"],color=pab["vp_hover_fontcolor"]),\
        align=pa["vp_hover_align"])
    line=dict(color=pab["vp_linecolor"],width=pab["vp_linewidth"])
    marker=dict(outliercolor=pab["vp_marker_outliercolor"],symbol=pa["vp_marker_symbol"],opacity=pab["vp_marker_opacity"],\
    size=pab["vp_marker_size"],color=pab["vp_marker_fillcolor"],line=dict(color=pab["vp_marker_line_color"],\
    width=pab["vp_marker_line_width"],outliercolor=pab["vp_marker_line_outliercolor"],outlierwidth=pab["vp_marker_line_outlierwidth"]))

    if pab["vp_meanline_color"]!=None:
        meanline=dict(visible=True,color=pab["vp_meanline_color"],width=pab["vp_meanline_width"])
    else:
        meanline=dict(visible=False)

    if pa["hue"]=="None":
        fig.add_trace(go.Violin(y=tmp[pa["y_val"]],x=tmp[pa["x_val"]],text=pa["vp_text"],width=pab["vp_width"],orientation=pab["vp_orient"],\
        bandwidth=pab["vp_bw"],opacity=pab["opacity"],hovertext=pa["vp_hovertext"],hoverinfo=pa["vp_hoverinfo"],hoveron=pa["vp_hoveron"],\
        hoverlabel=hoverlabel,fillcolor=vp_color,line=line,pointpos=pab["vp_pointpos"],jitter=pab["vp_jitter"],meanline=meanline,\
        side=pa["vp_side"],spanmode=pa["vp_span"],marker=marker))
    else:
        for each,side in zip(list(set(tmp[pa["hue"]])),["negative","positive"]):
            fig.add_trace(go.Violin(y=tmp[pa["y_val"]][tmp[pa["hue"]] == each ],x=tmp[pa["x_val"]][tmp[pa["hue"]] == each ],\
            legendgroup=each,name=each,scalegroup=each,text=pa["vp_text"],width=pab["vp_width"],orientation=pab["vp_orient"],\
            bandwidth=pab["vp_bw"],opacity=pab["opacity"],hovertext=pa["vp_hovertext"],hoverinfo=pa["vp_hoverinfo"],hoveron=pa["vp_hoveron"],\
            hoverlabel=hoverlabel,fillcolor=vp_color,line=line,pointpos=pab["vp_pointpos"],jitter=pab["vp_jitter"],meanline=meanline,\
            side=side,spanmode=pa["vp_span"],marker=marker))
        fig.update_layout(violingap=0, violinmode='overlay')





    #UPDATE LAYOUT OF PLOTS
    #Figure size
    fig.update_layout( width=pab["fig_width"], height=pab["fig_height"] ) #  autosize=False,

    #Update title
    title=dict(text=pa["title"],font=dict(family=pab["title_fontfamily"],size=pab["title_fontsize"],color=pab["title_fontcolor"]),\
        xref=pa["xref"],yref=pa["yref"],x=pab["x"],y=pab["y"],xanchor=pa["title_xanchor"],yanchor=pa["title_yanchor"])

    fig.update_layout(title=title)


    #Update axes
    
    if pa["log_scale"]==True and pa["orientation"]=="vertical":
        fig.update_yaxes(type="log")
    elif pa["log_scale"]==True and pa["orientation"]=="horizontal":
        fig.update_xaxes(type="log")

    fig.update_xaxes(zeroline=False, showline=pab["lower_axis"], linewidth=pab["axis_line_width"], linecolor=pab["axis_line_color"])
    fig.update_yaxes(zeroline=False, showline=pab["left_axis"], linewidth=pab["axis_line_width"], linecolor=pab["axis_line_color"])

    #Update ticks

    if pab["tick_lower_axis"]==False and pab["tick_right_axis"]==False and pab["tick_left_axis"]==False and pab["tick_upper_axis"]==False:
        pa["ticks_direction_value"]=""
        ticks=""
    else:
        ticks=pa["ticks_direction_value"]

    fig.update_xaxes(ticks=ticks, tickwidth=pab["ticks_line_width"], tickcolor=pab["ticks_color"], ticklen=pab["ticks_length"])
    fig.update_yaxes(ticks=ticks, tickwidth=pab["ticks_line_width"], tickcolor=pab["ticks_color"], ticklen=pab["ticks_length"])

    #Update mirror property of axis based on ticks and axis selected by user
    #Determines if the axis lines or/and ticks are mirrored to the opposite side of the plotting area. 
    # If "True", the axis lines are mirrored. If "ticks", the axis lines and ticks are mirrored. If "False", mirroring is disable. 
    # If "all", axis lines are mirrored on all shared-axes subplots. If "allticks", axis lines and ticks are mirrored on all shared-axes subplots.
    if pab["upper_axis"]==True and pab["tick_upper_axis"]==True:
        fig.update_xaxes(mirror="ticks")
    elif pab["upper_axis"]==True and pab["tick_upper_axis"]==False:
        fig.update_xaxes(mirror=True)
    else:
        fig.update_xaxes(mirror=False)
    
    
    if pab["right_axis"]==True and pab["tick_right_axis"]==True:
        fig.update_yaxes(mirror="ticks")
    elif pab["right_axis"]==True and pab["tick_right_axis"]==False:
        fig.update_yaxes(mirror=True)
    else:
        fig.update_xaxes(mirror=False)

    if (pa["x_lower_limit"]!="") and (pa["x_upper_limit"]!="") :
        xmin=pab["x_lower_limit"]
        xmax=pab["x_upper_limit"]
        fig.update_xaxes(range=[xmin, xmax])

    if (pa["y_lower_limit"]!="") and (pa["y_upper_limit"]!="") :
        ymin=pab["y_lower_limit"]
        ymax=pab["y_upper_limit"]
        fig.update_yaxes(range=[ymin, ymax])

    if pa["maxxticks"]!="":
        fig.update_yaxes(nticks=pab["maxxticks"])

    if pa["maxyticks"]!="":
        fig.update_yaxes(nticks=pab["maxyticks"])

    #Update spikes
    
    if pa["spikes_value"]=="both":
        fig.update_xaxes(showspikes=True,spikecolor=pab["spikes_color"],spikethickness=pab["spikes_thickness"],spikedash=pa["spikes_dash"],spikemode=pa["spikes_mode"])
        fig.update_yaxes(showspikes=True,spikecolor=pab["spikes_color"],spikethickness=pab["spikes_thickness"],spikedash=pa["spikes_dash"],spikemode=pa["spikes_mode"])

    elif pa["spikes_value"]=="x":
        fig.update_xaxes(showspikes=True,spikecolor=pab["spikes_color"],spikethickness=pab["spikes_thickness"],spikedash=pa["spikes_dash"],spikemode=pa["spikes_mode"])   
    
    elif pa["spikes_value"]=="y":
        fig.update_yaxes(showspikes=True,spikecolor=pab["spikes_color"],spikethickness=pab["spikes_thickness"],spikedash=pa["spikes_dash"],spikemode=pa["spikes_mode"])   

    elif pa["spikes_value"]=="None":
        fig.update_xaxes(showspikes=None)
        fig.update_yaxes(showspikes=None)


    #UPDATE X AXIS AND Y AXIS LAYOUT

    xaxis=dict(visible=True, title=dict(text=pa["xlabel"],font=dict(family=pab["label_fontfamily"],size=pab["label_fontsize"],color=pab["label_fontcolor"])))
    yaxis=dict(visible=True, title=dict(text=pa["ylabel"],font=dict(family=pab["label_fontfamily"],size=pab["label_fontsize"],color=pab["label_fontcolor"])))

    fig.update_layout(paper_bgcolor=pab["paper_bgcolor"],plot_bgcolor=pab["plot_bgcolor"],xaxis = xaxis,yaxis = yaxis)

    fig.update_xaxes(tickangle=pab["xticks_rotation"], tickfont=dict(size=pab["xticks_fontsize"]))
    fig.update_yaxes(tickangle=pab["yticks_rotation"], tickfont=dict(size=pab["yticks_fontsize"]))

    #UPDATE GRID PROPERTIES


    if pa["grid_value"] == "None":
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)

    elif pa["grid_value"]=="x":
        fig.update_yaxes(showgrid=True,gridcolor=pab["grid_color"],gridwidth=pab["grid_width"])
    elif pa["grid_value"]=="y":
        fig.update_xaxes(showgrid=True,gridcolor=pab["grid_color"],gridwidth=pab["grid_width"])
    elif pa["grid_value"]=="both":
        fig.update_xaxes(showgrid=True,gridcolor=pab["grid_color"],gridwidth=pab["grid_width"])
        fig.update_yaxes(showgrid=True,gridcolor=pab["grid_color"],gridwidth=pab["grid_width"])

    fig.update_layout(template='plotly_white')

    #UPDATE LEGEND PROPERTIES
    if pab["show_legend"]==True:

        labels=[x["label"] for x in pa["groups_settings"].values()]

        if pa["legend_orientation"]=="vertical":
            legend_orientation="v"
        elif pa["legend_orientation"]=="horizontal":
            legend_orientation="h"
        
        fig.update_layout(showlegend=True,legend=dict(x=pab["legend_x"],y=pab["legend_y"],bgcolor=pab["legend_bgcolor"],bordercolor=pab["legend_bordercolor"],\
            borderwidth=pab["legend_borderwidth"],valign=pa["legend_valign"],\
            font=dict(family=pab["legend_fontfamily"],size=pab["legend_fontsize"],color=pab["legend_fontcolor"]),orientation=legend_orientation,\
            traceorder=pa["legend_traceorder"],tracegroupgap=pab["legend_tracegroupgap"],\
            title=dict(text=pa["legend_title"],side=pa["legend_side"],font=dict(family=pab["legend_title_fontfamily"],size=pab["legend_title_fontsize"],\
            color=pab["legend_title_fontcolor"]))))
    
    else:
        fig.update_layout(showlegend=False)
    

    return fig

STANDARD_SIZES=[str(i) for i in list(range(1,101))]
STANDARD_STYLES=["Violinplot","Swarmplot","Boxplot","Violinplot and Swarmplot","Boxplot and Swarmplot"]
STANDARD_COLORS=["None","aliceblue","antiquewhite","aqua","aquamarine","azure","beige",\
    "bisque","black","blanchedalmond","blue","blueviolet","brown","burlywood",\
    "cadetblue","chartreuse","chocolate","coral","cornflowerblue","cornsilk",\
    "crimson","cyan","darkblue","darkcyan","darkgoldenrod","darkgray","darkgrey",\
    "darkgreen","darkkhaki","darkmagenta","darkolivegreen","darkorange","darkorchid",\
    "darkred","darksalmon","darkseagreen","darkslateblue","darkslategray","darkslategrey",\
    "darkturquoise","darkviolet","deeppink","deepskyblue","dimgray","dimgrey","dodgerblue",\
    "firebrick","floralwhite","forestgreen","fuchsia","gainsboro","ghostwhite","gold",\
    "goldenrod","gray","grey","green","greenyellow","honeydew","hotpink","indianred","indigo",\
    "ivory","khaki","lavender","lavenderblush","lawngreen","lemonchiffon","lightblue","lightcoral",\
    "lightcyan","lightgoldenrodyellow","lightgray","lightgrey","lightgreen","lightpink","lightsalmon",\
    "lightseagreen","lightskyblue","lightslategray","lightslategrey","lightsteelblue","lightyellow",\
    "lime","limegreen","linen","magenta","maroon","mediumaquamarine","mediumblue","mediumorchid",\
    "mediumpurple","mediumseagreen","mediumslateblue","mediumspringgreen","mediumturquoise",\
    "mediumvioletred","midnightblue","mintcream","mistyrose","moccasin","navajowhite","navy",\
    "oldlace","olive","olivedrab","orange","orangered","orchid","palegoldenrod","palegreen",\
    "paleturquoise","palevioletred","papayawhip","peachpuff","peru","pink","plum","powderblue",\
    "purple","red","rosybrown","royalblue","rebeccapurple","saddlebrown","salmon","sandybrown",\
    "seagreen","seashell","sienna","silver","skyblue","slateblue","slategray","slategrey","snow",\
    "springgreen","steelblue","tan","teal","thistle","tomato","turquoise","violet","wheat","white",\
    "whitesmoke","yellow","yellowgreen"]
LINE_STYLES=["solid", "dot", "dash", "longdash", "dashdot","longdashdot"]
STANDARD_BARMODES=["stack", "group","overlay","relative"]
STANDARD_ORIENTATIONS=['vertical','horizontal']
STANDARD_ALIGNMENTS=["left","right","auto"]
STANDARD_VERTICAL_ALIGNMENTS=["top", "middle","bottom"]
STANDARD_FONTS=["Arial", "Balto", "Courier New", "Default", "Droid Sans", "Droid Serif", "Droid Sans Mono",\
                "Gravitas One", "Old Standard TT", "Open Sans", "Overpass", "PT Sans Narrow", "Raleway", "Times New Roman"]
TICKS_DIRECTIONS=["inside","outside",'']
LEGEND_LOCATIONS=['best','upper right','upper left','lower left','lower right','right','center left','center right','lower center','upper center','center']
MODES=["expand",None]
STANDARD_HOVERINFO=["x", "y", "z", "text", "name","all","none","skip","x+y","x+text","x+name",\
                    "y+text","y+name","text+name","x+y+name","x+y+text","x+text+name","y+text+name"]
STANDARD_HOVERONS=["violins", "points", "kde","violins+points", "violins+kde","points+kde","violins+points+kde", "all" ]
STANDARD_ERRORBAR_TYPES=["percent","constant","sqrt"]
STANDARD_REFERENCES=["container","paper"]
STANDARD_TITLE_XANCHORS=["auto","left","center","right"]
STANDARD_TITLE_YANCHORS=["top","middle","bottom"]
STANDARD_LEGEND_XANCHORS=["auto","left","center","right"]
STANDARD_LEGEND_YANCHORS=["auto","top","middle","bottom"]
STANDARD_TRACEORDERS=["reversed", "grouped", "reversed+grouped", "normal"]
STANDARD_SIDES=["top","left","top left"]
STANDARD_SPIKEMODES=["toaxis", "across", "marker","toaxis+across","toaxis+marker","across+marker","toaxis+across+marker"]
STANDARD_SCALEMODES=["width","count"]
STANDARD_SYMBOLS=["0","circle","100","circle-open","200","circle-dot","300","circle-open-dot","1","square",\
    "101","square-open","201","square-dot","301","square-open-dot","2","diamond","102","diamond-open","202",\
    "diamond-dot","302","diamond-open-dot","3","cross","103","cross-open","203","cross-dot","303","cross-open-dot",\
    "4","x","104","x-open","204","x-dot","304","x-open-dot","5","triangle-up","105","triangle-up-open","205",\
    "triangle-up-dot","305","triangle-up-open-dot","6","triangle-down","106","triangle-down-open","206","triangle-down-dot",\
    "306","triangle-down-open-dot","7","triangle-left","107","triangle-left-open","207","triangle-left-dot","307",\
    "triangle-left-open-dot","8","triangle-right","108","triangle-right-open","208","triangle-right-dot","308",\
    "triangle-right-open-dot","9","triangle-ne","109","triangle-ne-open","209","triangle-ne-dot","309",\
    "triangle-ne-open-dot","10","triangle-se","110","triangle-se-open","210","triangle-se-dot","310","triangle-se-open-dot",\
    "11","triangle-sw","111","triangle-sw-open","211","triangle-sw-dot","311","triangle-sw-open-dot","12","triangle-nw",\
    "112","triangle-nw-open","212","triangle-nw-dot","312","triangle-nw-open-dot","13","pentagon","113","pentagon-open",\
    "213","pentagon-dot","313","pentagon-open-dot","14","hexagon","114","hexagon-open","214","hexagon-dot","314","hexagon-open-dot",\
    "15","hexagon2","115","hexagon2-open","215","hexagon2-dot","315","hexagon2-open-dot","16","octagon","116","octagon-open",\
    "216","octagon-dot","316","octagon-open-dot","17","star","117","star-open","217","star-dot","317","star-open-dot","18",\
    "hexagram","118","hexagram-open","218","hexagram-dot","318","hexagram-open-dot","19","star-triangle-up","119",\
    "star-triangle-up-open","219","star-triangle-up-dot","319","star-triangle-up-open-dot","20","star-triangle-down","120",\
    "star-triangle-down-open","220","star-triangle-down-dot","320","star-triangle-down-open-dot","21","star-square","121",\
    "star-square-open","221","star-square-dot","321","star-square-open-dot","22","star-diamond","122","star-diamond-open",\
    "222","star-diamond-dot","322","star-diamond-open-dot","23","diamond-tall","123","diamond-tall-open","223",\
    "diamond-tall-dot","323","diamond-tall-open-dot","24","diamond-wide","124","diamond-wide-open","224","diamond-wide-dot",\
    "324","diamond-wide-open-dot","25","hourglass","125","hourglass-open","26","bowtie","126","bowtie-open","27","circle-cross",\
    "127","circle-cross-open","28","circle-x","128","circle-x-open","29","square-cross","129","square-cross-open","30",\
    "square-x","130","square-x-open","31","diamond-cross","131","diamond-cross-open","32","diamond-x","132","diamond-x-open",\
    "33","cross-thin","133","cross-thin-open","34","x-thin","134","x-thin-open","35","asterisk","135","asterisk-open","36",\
    "hash","136","hash-open","236","hash-dot","336","hash-open-dot","37","y-up","137","y-up-open","38","y-down","138",\
    "y-down-open","39","y-left","139","y-left-open","40","y-right","140","y-right-open","41","line-ew","141","line-ew-open",\
    "42","line-ns","142","line-ns-open","43","line-ne","143","line-ne-open","44","line-nw","144","line-nw-open"]

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

    plot_arguments={"fig_width":"600",\
        "fig_height":"600",\
        "title":'iViolinplot',\
        "title_fontsize":"20",\
        "title_fontfamily":"Default",\
        "title_fontcolor":"None",\
        "titles":"20",\
        "opacity":"1",\
        "style":"violinplot",\
        "styles":STANDARD_STYLES,\
        "paper_bgcolor":"white",\
        "plot_bgcolor":"white",\
        "hoverinfos":STANDARD_HOVERINFO,\
        "hover_alignments":STANDARD_ALIGNMENTS,\
        "references":STANDARD_REFERENCES,\
        "vp_text":"",\
        "vp_width":"0",\
        "vp_orient":"vertical",\
        "vp_color_rgb":"",\
        "vp_color_value":"None",\
        "vp_bw":"",\
        "vp_hovertext":"",\
        "vp_hoverinfo":"all",\
        "vp_hoveron":"violins+points+kde",\
        "hoverons":STANDARD_HOVERONS,\
        "vp_hover_bgcolor":"None",\
        "vp_hover_bordercolor":"None",\
        "vp_hover_fontfamily":"Default",\
        "vp_hover_fontsize":"12",\
        "vp_hover_fontcolor":"None",\
        "vp_hover_align":"auto",\
        "vp_linecolor":"None",\
        "vp_linewidth":"2",\
        "vp_pointpos":"0",\
        "vp_jitter":"0.5",\
        "vp_meanline_width":"0",\
        "vp_meanline_color":"None",\
        "vp_scalemode":"width",\
        "vp_span":"soft",\
        "spans":["soft","hard"],\
        "vp_side":"both",\
        "vp_sides":["both","positive","negative"],\
        "scalemodes":STANDARD_SCALEMODES,\
        "vp_marker_symbol":"circle",\
        "marker_symbols":STANDARD_SYMBOLS,\
        "vp_marker_outliercolor":"None",\
        "vp_marker_opacity":"1",\
        "vp_marker_size":"6",\
        "vp_marker_fillcolor":"None",\
        "vp_marker_line_color":"None",\
        "vp_marker_line_width":"0",\
        "vp_marker_line_outlierwidth":"1",\
        "vp_marker_line_outliercolor":"None",\
        "xref":"container",\
        "yref":"container",\
        "x":"0.5",\
        "y":"0.9",\
        "title_xanchors":STANDARD_TITLE_XANCHORS,\
        "title_yanchors":STANDARD_TITLE_YANCHORS,\
        "title_xanchor":"auto",\
        "title_yanchor":"auto",\
        "show_legend":"on",\
        "axis_line_width":1.0,\
        "axis_line_color":"lightgrey",\
        "ticks_line_width":1.0,\
        "ticks_color":"lightgrey",\
        "cols":[],\
        "groups":[],\
        "vals":[],\
        "hue":None,\
        "x_val":None,\
        "y_val":None,\
        "groups_settings":dict(),\
        "log_scale":".off",\
        "fonts":STANDARD_FONTS,\
        "colors":STANDARD_COLORS,\
        "linestyles":LINE_STYLES,\
        "linestyle_value":"",\
        "orientations":STANDARD_ORIENTATIONS, \
        "fontsizes":STANDARD_SIZES,\
        "xlabel_size":STANDARD_SIZES,\
        "ylabel_size":STANDARD_SIZES,\
        "xlabel":"",\
        "ylabel":"",\
        "label_fontfamily":"Default",\
        "label_fontsize":"15",\
        "label_fontcolor":"None",\
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
        "spikes":["None","both","x","y"],\
        "spikes_value":"None",\
        "spikes_color":"None",\
        "spikes_thickness":"3.0",\
        "dashes":LINE_STYLES,\
        "spikes_dash":"dash",\
        "spikes_mode":"toaxis",\
        "spikes_modes":STANDARD_SPIKEMODES,\
        "grid":["None","both","x","y"],\
        "grid_value":"None",\
        "grid_width":"1",\
        "grid_color":"lightgrey",\
        "legend_title":"",\
        "legend_bgcolor":"None",\
        "legend_borderwidth":"0",\
        "legend_bordercolor":"None",\
        "legend_fontfamily":"Default",\
        "legend_fontsize":"12",\
        "legend_fontcolor":"None",\
        "legend_title_fontfamily":"Default",\
        "legend_title_fontsize":"12",\
        "legend_title_fontcolor":"None",\
        "legend_orientation":"vertical",\
        "traceorders":STANDARD_TRACEORDERS,\
        "legend_traceorder":"normal",\
        "legend_tracegroupgap":"10",\
        "legend_y":"1",\
        "legend_x":"1.02",\
        "legend_xanchor":"left",\
        "legend_yanchor":"auto",\
        "legend_xanchors":STANDARD_LEGEND_XANCHORS,\
        "legend_yanchors":STANDARD_LEGEND_YANCHORS,\
        "legend_valign":"middle",\
        "valignments":STANDARD_VERTICAL_ALIGNMENTS,\
        "sides":STANDARD_SIDES,\
        "legend_side":"left",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"iviolinplot",\
        "session_downloadn":"MySession.iviolinplot.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.iviolinplot.plot",\
        "inputargumentsfile":"Select file.."
    }
    return plot_arguments