#from matplotlib.figure import Figure
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
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

    tmp=df.copy()
    tmp=tmp[pa["vals"]]

    fig = go.Figure( )

    # MAIN FIGURE
    #Load checkboxes
    pab={}
    for arg in ["show_legend","upper_axis","lower_axis","left_axis","right_axis","errorbar",\
        "errorbar_symmetric","tick_left_axis","tick_lower_axis","tick_upper_axis","tick_right_axis",\
        "kde","show_hist","show_curve","show_rug"]:
        if pa[arg] in ["off",".off"]:
            pab[arg]=False
        else:
            pab[arg]=True

    #Load floats
    floats=["bin_size","errorbar_value","errorbar_thickness","errorbar_width","x","y","axis_line_width","ticks_line_width",\
        "ticks_length","x_lower_limit","x_upper_limit","y_lower_limit","y_upper_limit","spikes_thickness","xticks_rotation",\
        "yticks_rotation","xticks_fontsize","yticks_fontsize","grid_width","legend_borderwidth","legend_tracegroupgap","legend_x",\
        "legend_y","fig_width","fig_height"]

    for a in floats:
        if pa[a] == "" or pa[a]=="None" or pa[a]==None:
            pab[a]=None
        else:
            pab[a]=float(pa[a])

    #Load integers
    integers=["label_fontsize","legend_fontsize","legend_title_fontsize","title_fontsize","maxxticks","maxyticks"]
    for a in integers:
        if pa[a] == "" or pa[a]=="None" or pa[a]==None:
            pab[a]=None
        else:
            pab[a]=int(pa[a])

    #Load Nones
    possible_nones=["errorbar_color","title_fontcolor","axis_line_color","ticks_color","spikes_color","label_fontcolor",\
    "paper_bgcolor","plot_bgcolor","grid_color","legend_bgcolor","legend_bordercolor","legend_fontcolor","legend_title_fontcolor",\
     "title_fontfamily","label_fontfamily","legend_fontfamily","legend_title_fontfamily"]
    for p in possible_nones:
        if pa[p] == "None" or pa[p]=="Default" :
            pab[p]=None
        else:
            pab[p]=pa[p]

    #KDE (KERNEL DENSITY ESTIMATION) plot
    if pab["kde"]==True:
        colors=list()
        if pa["rug_text"]!="":
            rug_text=pa["rug_text"].split(",")
        else:
            rug_text=[]

        for h in pa["groups_settings"].values():
            if h["color_rgb"] == "":
                if h["color_value"]=="None":
                    colors.append(None)
                else:
                    colors.append(h["color_value"])
            else:
                colors.append(GET_COLOR( h["color_rgb"] ))
        
        hist_data=[]
        for col in tmp.columns:
            hist_data.append(tmp[col])

        fig=ff.create_distplot(hist_data=hist_data,group_labels=pa["vals"],curve_type=pa["curve_type"],show_hist=pab["show_hist"],\
            show_curve=pab["show_curve"],show_rug=pab["show_rug"],bin_size=pab["bin_size"],rug_text=rug_text,colors=colors, histnorm=pa["kde_histnorm"])

    else:
        for h in pa["groups_settings"].values():
            #Initialize dummie dict
            h_=dict()

            #Load integers
            integers=["hover_fontsize","bins_number"]
            for a in integers:
                if h[a] == "" or h[a]=="None" or h[a] == None:
                    h_[a]=None
                else:
                    h_[a]=int(h[a])

            #Load Nones
            possible_nones=["hover_bgcolor","hover_bordercolor","hover_fontfamily","hover_fontcolor"]
            for p in possible_nones:
                if h[p] == "None" or h[p]=="Default" :
                    h_[p]=None
                else:
                    h_[p]=h[p]

            #Load floats
            floats=["opacity","linewidth"]

            for a in floats:
                if h[a] == "":
                    h_[a]=None
                else:
                    h_[a]=float(h[a])

            if h["label"]!="":
                name=h["label"]
            else:
                name=""
            
            if h["text"]!="":
                text=h["text"]
            else:
                text=""

            if h["color_rgb"] == "":
                if h["color_value"]=="None":
                    marker_color=None
                else:
                    marker_color = h["color_value"]
            else:
                marker_color = GET_COLOR( h["color_rgb"] )
                    
            if h["line_rgb"] == "":
                if h["line_color"]=="None":
                    line_color=None
                else:
                    line_color = h["line_color"]
            else:
                line_color = GET_COLOR( h["line_rgb"] )


            if h["histnorm"] == "None":
                histnorm = ""
            else:
                histnorm = h["histnorm"]

            if h["cumulative"]=="on":
                cumulative_enabled=True
            else:
                cumulative_enabled=False
            
            marker=dict(color=marker_color,line=dict(width=h_["linewidth"],color=line_color))
            cumulative=dict(enabled=cumulative_enabled,direction=h["cumulative_direction"])

            hoverlabel=dict(bgcolor=h_["hover_bgcolor"],bordercolor=h_["hover_bordercolor"],align=h["hover_align"],\
                font=dict(family=h_["hover_fontfamily"],size=h_["hover_fontsize"],color=h_["hover_fontcolor"]))
            
            if pab["errorbar"]==True:
                    errorbar=True

            if h["orientation_value"]=="vertical":

                if pab["errorbar"]==True:
                    error_y=dict(visible=errorbar,value=pab["errorbar_value"],type=pa["errorbar_type"],symmetric=pab["errorbar_symmetric"],color=pab["errorbar_color"],\
                        thickness=pab["errorbar_thickness"],width=pab["errorbar_width"])
                else:
                    error_y=dict(visible=False)

                trace=fig.add_trace(go.Histogram(x=tmp[h["name"]],text=text,hoverinfo=h["hoverinfo"],histfunc=h["histfunc"],cumulative=cumulative,\
                    opacity=h_["opacity"],nbinsx=h_["bins_number"],name=name,marker=marker,error_y=error_y,hoverlabel=hoverlabel))
            

            elif h["orientation_value"]=="horizontal":

                if pab["errorbar"]==True:
                    error_x=dict(visible=errorbar,value=pab["errorbar_value"],type=pa["errorbar_type"],symmetric=pab["errorbar_symmetric"],color=pab["errorbar_color"],\
                        thickness=pab["errorbar_thickness"],width=pab["errorbar_width"])
                else:
                    error_x=dict(visible=False)
                
                fig.add_trace(go.Histogram(y=tmp[h["name"]],text=text,hoverinfo=h["hoverinfo"],histfunc=h["histfunc"],cumulative=cumulative,\
                opacity=h_["opacity"],nbinsy=h_["bins_number"],name=name,marker=marker,error_x=error_x,hoverlabel=hoverlabel))



    #UPDATE LAYOUT OF HISTOGRAMS
    #Figure size
    fig.update_layout( width=pab["fig_width"], height=pab["fig_height"] ) #  autosize=False,

    #Update title
    title=dict(text=pa["title"],font=dict(family=pab["title_fontfamily"],size=pab["title_fontsize"],color=pab["title_fontcolor"]),\
        xref=pa["xref"],yref=pa["yref"],x=pab["x"],y=pab["y"],xanchor=pa["title_xanchor"],yanchor=pa["title_yanchor"])

    fig.update_layout(title=title,barmode=pa["barmode"])


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
STANDARD_HISTNORMS=['None', 'percent', 'probability', 'density', 'probability density']
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
STANDARD_HISTFUNC=["count","sum","avg","min","max"]
STANDARD_CUMULATIVE_DIRECTIONS=["increasing","decreasing"]
STANDARD_ERRORBAR_TYPES=["percent","constant","sqrt"]
STANDARD_REFERENCES=["container","paper"]
STANDARD_TITLE_XANCHORS=["auto","left","center","right"]
STANDARD_TITLE_YANCHORS=["top","middle","bottom"]
STANDARD_LEGEND_XANCHORS=["auto","left","center","right"]
STANDARD_LEGEND_YANCHORS=["auto","top","middle","bottom"]
STANDARD_TRACEORDERS=["reversed", "grouped", "reversed+grouped", "normal"]
STANDARD_SIDES=["top","left","top left"]
STANDARD_SPIKEMODES=["toaxis", "across", "marker","toaxis+across","toaxis+marker","across+marker","toaxis+across+marker"]
STANDARD_CURVETYPES=["kde","normal"]

def figure_defaults():

    """ Generates default figure arguments.

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
        "title":'iHistogram',\
        "title_fontsize":"20",\
        "title_fontfamily":"Default",\
        "title_fontcolor":"None",\
        "titles":"20",\
        "kde":".off",\
        "curve_type":"kde",\
        "curve_types":STANDARD_CURVETYPES,\
        "kde_histnorm":"probability density",\
        "kde_histnorms":["probability density","probability"],\
        "show_hist":"on",\
        "show_curve":"on",\
        "show_rug":"on",\
        "rug_text":"",\
        "bin_size":"1",\
        "opacity":0.8,\
        "paper_bgcolor":"white",\
        "plot_bgcolor":"white",\
        "hoverinfos":STANDARD_HOVERINFO,\
        "hover_alignments":STANDARD_ALIGNMENTS,\
        "histfuncs":STANDARD_HISTFUNC,\
        "references":STANDARD_REFERENCES,\
        "xref":"container",\
        "yref":"container",\
        "x":"0.5",\
        "y":"0.9",\
        "title_xanchors":STANDARD_TITLE_XANCHORS,\
        "title_yanchors":STANDARD_TITLE_YANCHORS,\
        "title_xanchor":"auto",\
        "title_yanchor":"auto",\
        "show_legend":"on",\
        "errorbar":".off",\
        "errorbar_value":"10",\
        "errorbar_type":"percent",\
        "errorbar_types":STANDARD_ERRORBAR_TYPES,\
        "errorbar_symmetric":".off",\
        "errorbar_color":"darkgrey",\
        "errorbar_width":"2",\
        "errorbar_thickness":"2",\
        "axis_line_width":1.0,\
        "axis_line_color":"lightgrey",\
        "ticks_line_width":1.0,\
        "ticks_color":"lightgrey",\
        "cols":[],\
        "groups":[],\
        "vals":[],\
        "groups_settings":dict(),\
        "log_scale":".off",\
        "fonts":STANDARD_FONTS,\
        "cumulative_directions":STANDARD_CUMULATIVE_DIRECTIONS,\
        "colors":STANDARD_COLORS,\
        "histnorms":STANDARD_HISTNORMS,\
        "barmode":"overlay",\
        "barmodes":STANDARD_BARMODES,\
        "histtype_value":"bar",\
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
        "downloadn":"ihistogram",\
        "session_downloadn":"MySession.ihistogram.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.ihistogram.plot",\
        "inputargumentsfile":"Select file.."}
    
    return plot_arguments