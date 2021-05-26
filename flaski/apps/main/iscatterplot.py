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

    fig = go.Figure( )
    fig.update_layout( width=pa_["fig_width"], height=pa_["fig_height"] ) #  autosize=False,

    # MAIN FIGURE
    # if we have groups
    # the user can decide how the diferent groups should look like 
    # by unchecking the groups_autogenerate check box
    pab={}
    for arg in ["show_legend","upper_axis","lower_axis","left_axis","right_axis"]:
        if pa[arg] in ["off",".off"]:
            pab[arg]=False
        else:
            pab[arg]=True

    if pa["labels_col_value"] != "select a column..":
        df["___label___"]=df[pa["labels_col_value"]].tolist()
    else:
        df["___label___"]=df.index.tolist()

    if str(pa["groups_value"])!="None":

        fig.update_layout(legend_title_text=str(pa["groups_value"]), legend=dict( title_font_color="black", font=dict( size=float(pa["legend_font_size"]), color="black" ) ) )
        
        for group in pa["list_of_groups"]:
            tmp=df[df[pa["groups_value"]]==group]

            x=tmp[pa["xvals"]].tolist()
            y=tmp[pa["yvals"]].tolist()
            text=tmp["___label___"].tolist()
            
            pa_=[ g for g in pa["groups_settings"] if g["name"]==group ][0]
            
            if pa_["markeralpha_col_value"] != "select a column..":
                a=[ float(i) for i in tmp[[pa_["markeralpha_col_value"]]].dropna()[pa_["markeralpha_col_value"]].tolist() ][0]
            else:
                a=float(pa_["marker_alpha"])

            if pa_["markerstyles_col"] != "select a column..":
                marker=[ str(i) for i in tmp[[pa_["markerstyles_col"]]].dropna()[pa_["markerstyles_col"]].tolist() ][0]
            else:
                marker=pa_["marker"]

            if pa_["markersizes_col"] != "select a column..":
                s=[ float(i) for i in tmp[[pa_["markersizes_col"]]].dropna()[pa_["markersizes_col"]].tolist() ][0]
            else:
                s=float(pa_["markers"])

            if pa_["markerc_col"] != "select a column..":
                c=[ i for i in tmp[[pa_["markerc_col"]]].dropna()[pa_["markerc_col"]].tolist()][0]
            elif str(pa["markerc_write"]) != "":
                c=pa_["markerc_write"]
            else:
                c=pa_["markerc"]


            if pa_["edgecolor_col"] != "select a column..":
                edgecolor=[ i for i in tmp[[pa_["edgecolor_col"]]].dropna()[pa_["edgecolor_col"]].tolist()][0]
            elif str(pa_["edgecolor_write"]) != "":
                edgecolor=pa_["edgecolor_write"]
            else:
                edgecolor=pa_["edgecolor"]

            if pa_["edge_linewidth_col"] != "select a column..":
                edge_linewidth=[ float(i) for i in tmp[[pa_["edge_linewidth_col"]]].dropna()[pa_["edge_linewidth_col"]].tolist() ][0]
            else:
                edge_linewidth=float(pa_["edge_linewidth"])

            # https://plotly.com/python/line-and-scatter/
            # https://plotly.com/python/marker-style/
            fig.add_trace(go.Scatter(x=x, y=y, text=text,\
                hovertemplate ='<b>%{text}</b><br><br><b>'+pa["xvals"]+'</b>: %{x}<br><b>'+pa["yvals"]+'</b>: %{y}<br>' ,
                mode='markers',
                marker=dict(symbol=marker,\
                    color=c,
                    size=s,
                    opacity=a,
                    line=dict(
                        color=edgecolor,
                        width=edge_linewidth
                        )),\
                showlegend=pab["show_legend"],\
                name=group) )

        fig.update_layout(legend_title_text=str("test"), legend=dict( font=dict( size=float(pa["legend_font_size"]), color="black" ) ) )

    
    elif pa["groups_value"]=="None":

        if pa["markerstyles_col"] != "select a column..":
            markers=[ str(i) for i in df[pa["markerstyles_col"]].tolist() ]
            df["__marker__"]=markers
        else:
            df["__marker__"]=pa["marker"]
    
        for marker in list(OrderedDict.fromkeys(df["__marker__"].tolist())):

            tmp=df[df["__marker__"]==marker]
            x=tmp[pa["xvals"]].tolist()
            y=tmp[pa["yvals"]].tolist()
            text=tmp["___label___"].tolist()


            if pa["markeralpha_col_value"] != "select a column..":
                a=[ float(i) for i in tmp[[pa["markeralpha_col_value"]]].dropna()[pa["markeralpha_col_value"]].tolist() ][0]
            else:
                a=float(pa["marker_alpha"])
            
            if pa["markersizes_col"] != "select a column..":
                s=[ float(i) for i in tmp[pa["markersizes_col"]].tolist() ]
            else:
                s=float(pa["markers"])

            if pa["markerc_col"] != "select a column..":
                c=tmp[pa["markerc_col"]].tolist()
            elif str(pa["markerc_write"]) != "":
                c=pa["markerc_write"]
            else:
                c=pa["markerc"]

            if pa["edgecolor_col"] != "select a column..":
                edgecolor=tmp[[pa["edgecolor_col"]]].dropna()[pa["edgecolor_col"]].tolist()
            elif str(pa["edgecolor_write"]) != "":
                edgecolor=pa["edgecolor_write"]
            else:
                edgecolor=pa["edgecolor"]

            if pa["edge_linewidth_col"] != "select a column..":
                edge_linewidth=[ float(i) for i in tmp[[pa["edge_linewidth_col"]]].dropna()[pa["edge_linewidth_col"]].tolist() ][0]
            else:
                edge_linewidth=float(pa["edge_linewidth"])

            fig.add_trace(go.Scatter(x=x, y=y,text=text,\
                hovertemplate ='<b>%{text}</b><br><br><b>'+pa["xvals"]+'</b>: %{x}<br><b>'+pa["yvals"]+'</b>: %{y}<br>' ,
                hoverinfo='skip',
                mode='markers',
                marker=dict(symbol=marker,\
                    color=c,
                    size=s,
                    opacity=a,
                    line=dict(
                        color=edgecolor,
                        width=edge_linewidth
                        )),\
                showlegend=False,
                name="" ) )

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
            "font": {"size": float(pa["titles"]), "color":"black"  } } )

    fig.update_layout(
        xaxis = dict(
        title_text = pa["xlabel"],
        title_font = {"size": int(pa["xlabels"]),"color":"black"}),
        yaxis = dict(
        title_text = pa["ylabel"],
        title_font = {"size": int(pa["xlabels"]), "color":"black"} ) )

    fig.update_xaxes(tickangle=float(pa["xticks_rotation"]), tickfont=dict(size=float(pa["xticks_fontsize"]), color="black" ))
    fig.update_yaxes(tickangle=float(pa["yticks_rotation"]), tickfont=dict(size=float(pa["yticks_fontsize"]), color="black" ))


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

    if (pa["labels_col_value"] != "select a column..") & (len(pa["fixed_labels"])>0):
        if pa["labels_arrows_value"] == "None":
            showarrow=False
            arrowhead=0
            standoff=0
            yshift=10
        else:
            showarrow=True
            arrowhead=int(pa["labels_arrows_value"])
            standoff=4
            yshift=0
        tmp=df[df["___label___"].isin( pa["fixed_labels"]  )]
            
        x_values=tmp[pa["xvals"]].tolist()
        y_values=tmp[pa["yvals"]].tolist()
        text_values=tmp["___label___"].tolist()

        for x,y,text in zip(x_values,y_values,text_values):
            fig.add_annotation(
                    x=x,
                    y=y,
                    text=text,
                    showarrow=showarrow,
                    arrowhead=arrowhead,
                    clicktoshow="onoff",
                    visible=True,
                    standoff=standoff,
                    yshift=yshift,
                    opacity=float(pa["labels_alpha"]),
                    arrowwidth=float(pa["labels_line_width"]),
                    arrowcolor=pa["labels_colors_value"],
                    font=dict(
                        size=float(pa["labels_font_size"]),
                        color=pa["labels_font_color_value"]
                        )
                    )
        #fig.update_traces(textposition='top center')
    
    if pa["vline"] != "":
        if pa["vline_linestyle_value"] == '-':
            linetype=None
        elif pa["vline_linestyle_value"] == ':':
            linetype="dot"
        elif pa["vline_linestyle_value"] == '-.':
            linetype="dashdot"
        else:
            linetype='dash'
        fig.add_shape(type="line", x0=pa["vline"], x1=pa["vline"],\
            xref='x', yref='paper',\
            y0=0, y1=1,\
            line=dict(color=pa["vline_color_value"],width=float(pa["vline_linewidth"]), dash=linetype))

    if pa['hline'] != "":
        if pa["hline_linestyle_value"] == '-':
            linetype=None
        elif pa["hline_linestyle_value"] == ':':
            linetype="dot"
        elif pa["hline_linestyle_value"] == '-.':
            linetype="dashdot"
        else:
            linetype='dash'
        fig.add_shape(type="line", x0=0, x1=1,\
            xref='paper', yref='y',\
            y0=pa["hline"], y1= pa["hline"],\
            line=dict(color=pa["hline_color_value"],width=float(pa["hline_linewidth"]), dash=linetype))

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
TICKS_DIRECTIONS=["","outside", "inside"]
STANDARD_COLORS=["blue","green","red","cyan","magenta","yellow","black","white"]


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
        "fig_width":"600",\
        "fig_height":"600",\
        "title":'Scatter plot',\
        "title_size":STANDARD_SIZES,\
        "titles":"20",\
        "xcols":[],\
        "xvals":None,\
        "ycols":[],\
        "yvals":None,\
        "groups":["None"],\
        "groups_value":"None",\
        "list_of_groups":[],\
        "groups_settings":[],\
        "show_legend":".on",\
        "legend_font_size":"14",\
        "markerstyles":ALLOWED_MARKERS,\
        "marker":"circle",\
        "markerstyles_cols":["select a column.."],\
        "markerstyles_col":"select a column..",\
        "marker_size":STANDARD_SIZES,\
        "markers":"4",\
        "markersizes_cols":["select a column.."],\
        "markersizes_col":"select a column..",\
        "marker_color":STANDARD_COLORS,\
        "markerc":"black",\
        "markerc_write":"",\
        "markerc_cols":["select a column.."],\
        "markerc_col":"select a column..",\
        "marker_alpha":"1",\
        "markeralpha_col":["select a column.."],\
        "markeralpha_col_value":"select a column..",\
        "edge_colors":STANDARD_COLORS,\
        "edgecolor":"black",\
        "edgecolor_cols":["select a column.."],\
        "edgecolor_col":"select a column..",\
        "edgecolor_write":"",\
        "edge_linewidth_cols":["select a column.."],\
        "edge_linewidth_col":"select a column..",\
        "edge_linewidths":STANDARD_SIZES,\
        "edge_linewidth":"0",\
        "available_labels":[],\
        "fixed_labels":[],\
        "labels_col":["select a column.."],\
        "labels_col_value":"select a column..",\
        "labels_font_size":"10",\
        "labels_font_color":STANDARD_COLORS ,\
        "labels_font_color_value":"black",\
        "labels_arrows":["None","0","1","2","3","4","5","6","7","8"],\
        "labels_arrows_value":"None",\
        "labels_line_width":"0.5",\
        "labels_alpha":"0.5",\
        "labels_colors":STANDARD_COLORS,\
        "labels_colors_value":"black",\
        "xlabel":"x",\
        "xlabel_size":STANDARD_SIZES,\
        "xlabels":"14",\
        "ylabel":"y",\
        "ylabel_size":STANDARD_SIZES,\
        "ylabels":"14",\
        "axis_line_width":"1.0",\
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
        "hline":"",\
        "hline_color_text":"",\
        "hline_colors":STANDARD_COLORS,\
        "hline_color_value":"black",\
        "hline_linestyle":['-', '--', '-.', ':'],\
        "hline_linestyle_value":'--',\
        "hline_linewidth":"1",\
        "hline_alpha":"0.1",\
        "vline":"",\
        "vline_value":"None",\
        "vline_color_text":"",\
        "vline_colors":STANDARD_COLORS,\
        "vline_color_value":"black",\
        "vline_linestyle":['-', '--', '-.', ':'],\
        "vline_linestyle_value":'--',\
        "vline_linewidth":"1",\
        "vline_alpha":"0.1",\
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