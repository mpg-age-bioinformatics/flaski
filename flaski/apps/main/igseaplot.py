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
    pab={}
    for arg in ["upper_axis","lower_axis","left_axis","right_axis", "tick_x_axis", "tick_y_axis"]:
        if pa[arg] in ["off",".off"]:
            pab[arg]=False
        else:
            pab[arg]=True

    if pa["labels_col_value"] != "select a column..":
        df["___label___"]=df[pa["labels_col_value"]].tolist()
    else:
        df["___label___"]=df.index.tolist()
    
   
    tmp=df
    x=tmp[pa["xvals"]].tolist()
    y=tmp[pa["yvals"]].tolist()
    text=tmp["___label___"].tolist()


    # Define gsea line_
    if pa["gseacolor_col"] != "select a column..":
        gseacolor=tmp[[pa["gseacolor_col"]]].dropna()[pa["gseacolor_col"]].tolist()
    elif str(pa["gseacolor_write"]) != "":
        gseacolor=pa["gseacolor_write"]
    else:
        gseacolor=pa["gseacolor"]

    if pa["gsea_linewidth_col"] != "select a column..":
        gsea_linewidth=[ float(i) for i in tmp[[pa["gsea_linewidth_col"]]].dropna()[pa["gsea_linewidth_col"]].tolist() ][0]
    else:
        gsea_linewidth=float(pa["gsea_linewidth"])
        
    if pa["gsea_linestyle_value"] == '-':
        gsea_linetype=None
    elif pa["gsea_linestyle_value"] == ':':
        gsea_linetype="dot"
    elif pa["gsea_linestyle_value"] == '-.':
        gsea_linetype="dashdot"
    else:
        gsea_linetype='dash'
        
    if pa["labels_col_value"] != "select a column..":
        full_text = ['']
        for i, gene in enumerate(text[1:-1]):
            if gene != "nan":
                full_text.append(gene)
            else:
                full_text.append(text[(i+2)])
        full_text.append("")
        text=full_text

    fig.add_trace(go.Scatter(x=x, y=y,text=text,\
        hovertemplate ='<b>%{text}</b><br><br><b>'+pa["xvals"]+'</b>: %{x}<br><b>'+pa["yvals"]+'</b>: %{y}<br>' ,
        hoverinfo='skip',
        mode='lines',
        line=dict(
            color=gseacolor,
            width=gsea_linewidth,
            dash=gsea_linetype
            ),\
        showlegend=False,
        name="" ))

    # Define gene ticks
    if pa["genecolor_col"] != "select a column..":
        gene_color=tmp[[pa["genecolor_col"]]].dropna()[pa["genecolor_col"]].tolist()
    elif str(pa["genecolor_write"]) != "":
        gene_color=pa["genecolor_write"]
    else:
        gene_color=pa["genecolor"]
        
    if pa["gene_linewidth_col"] != "select a column..":
        gene_width=[ float(i) for i in tmp[[pa["gene_linewidth_col"]]].dropna()[pa["gene_linewidth_col"]].tolist() ][0]
    else:
        gene_width=float(pa["gene_linewidth"])
                    
    # if label is present, only plot sites with label present
    if pa["labels_col_value"] != "select a column..":
        tmp=df
        tmp.drop(tmp[tmp["___label___"] == 'nan'].index , inplace=True)
        x=tmp[pa["xvals"]].tolist()
        y=tmp[pa["yvals"]].tolist()
        text=tmp["___label___"].tolist()
        
    fig.add_trace(go.Scatter(x=x, y=[pa["centerline"]]*len(x),text=text, customdata=y, \
        hovertemplate ='<b>%{text}</b><br><br><b>'+pa["xvals"]+'</b>: %{x}<br><b>'+pa["yvals"]+'</b>: %{customdata}<br>' ,
        hoverinfo='skip',
        mode='markers',
        marker=dict(
            color=gene_color,
            symbol=142,
            size = gene_width),\
        showlegend=False,
        name="" ))
            

    fig.update_xaxes(zeroline=False, showline=pab["lower_axis"], linewidth=float(pa["axis_line_width"]), linecolor='black', mirror=pab["upper_axis"])
    fig.update_yaxes(zeroline=False, showline=pab["left_axis"], linewidth=float(pa["axis_line_width"]), linecolor='black', mirror=pab["right_axis"])

    if pab["tick_x_axis"] :
        fig.update_xaxes(ticks=pa["ticks_direction_value"], tickwidth=float(pa["axis_line_width"]), tickcolor='black', ticklen=float(pa["ticks_length"]) )
    else:
        fig.update_xaxes(ticks="", tickwidth=float(pa["axis_line_width"]), tickcolor='black', ticklen=float(pa["ticks_length"]) )

    if pab["tick_y_axis"] :
        fig.update_yaxes(ticks=pa["ticks_direction_value"], tickwidth=float(pa["axis_line_width"]), tickcolor='black', ticklen=float(pa["ticks_length"]) )
    else:
        fig.update_yaxes(ticks="", tickwidth=float(pa["axis_line_width"]), tickcolor='black', ticklen=float(pa["ticks_length"]))
    
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
        if pa["labels_ypos"] == "":
            y=float(pa["centerline"]) + max([abs(ele) for ele in y_values])* 0.12
        else:
            y = pa["labels_ypos"] 
        
        for x,text in zip(x_values,text_values):
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
                    textangle=float(pa["label_angle"]),
                    opacity=float(pa["labels_alpha"]),
                    arrowwidth=float(pa["labels_line_width"]),
                    arrowcolor=pa["labels_colors_value"],
                    font=dict(
                        size=float(pa["labels_font_size"]),
                        color=pa["labels_font_color_value"]
                        )
                    )

        #fig.update_traces(textposition='top center')
    
    # plot line at 0, add yes or no box or at other spots
    if pa["centerline"] != "":
        if pa["center_color_text"]!="":
            center_color=pa["center_color_text"]
        else:
            center_color=pa["center_color_value"]

        if pa["center_linestyle_value"] == '-':
            center_linetype=None
        elif pa["center_linestyle_value"] == ':':
            center_linetype="dot"
        elif pa["center_linestyle_value"] == '-.':
            center_linetype="dashdot"
        else:
            center_linetype='dash'
    
        fig.add_shape(type="line", x0=0, x1=1,\
            xref='paper', yref='y',\
            y0=pa["centerline"], y1=pa["centerline"], line=dict(color = center_color, width =  float(pa["center_linewidth"]), dash = center_linetype))

    
    if pa["vline"] != "":
        if pa["vline_color_text"]!="":
            vline_color=pa["vline_color_text"]
        else:
            vline_color=pa["vline_color_value"]

        if pa["vline_linestyle_value"] == '-':
            vline_linetype=None
        elif pa["vline_linestyle_value"] == ':':
            vline_linetype="dot"
        elif pa["vline_linestyle_value"] == '-.':
            vline_linetype="dashdot"
        else:
            vline_linetype='dash'

        fig.add_shape(type="line", x0=pa["vline"], x1=pa["vline"],\
            xref='x', yref='paper',\
            y0=0, y1=1,\
            line=dict(color=vline_color,width=float(pa["vline_linewidth"]), dash=vline_linetype))

    if pa['hline1'] != "":
        if pa["hline1_color_text"]!="":
            hline1_color=pa["hline1_color_text"]
        else:
            hline1_color=pa["hline1_color_value"]

        if pa["hline1_linestyle_value"] == '-':
            hline1_linetype=None
        elif pa["hline1_linestyle_value"] == ':':
            hline1_linetype="dot"
        elif pa["hline1_linestyle_value"] == '-.':
            hline1_linetype="dashdot"
        else:
            hline1_linetype='dash'

        fig.add_shape(type="line", x0=0, x1=1,\
            xref='paper', yref='y',\
            y0=pa["hline1"], y1= pa["hline1"],\
            line=dict(color=hline1_color,width=float(pa["hline1_linewidth"]), dash=hline1_linetype))
    
    if pa['hline2'] != "":
        if pa["hline2_color_text"]!="":
            hline2_color=pa["hline2_color_text"]
        else:
            hline2_color=pa["hline2_color_value"]

        if pa["hline2_linestyle_value"] == '-':
            hline2_linetype=None
        elif pa["hline2_linestyle_value"] == ':':
            hline2_linetype="dot"
        elif pa["hline2_linestyle_value"] == '-.':
            hline2_linetype="dashdot"
        else:
            hline2_linetype='dash'

        fig.add_shape(type="line", x0=0, x1=1,\
            xref='paper', yref='y',\
            y0=pa["hline2"], y1= pa["hline2"],\
            line=dict(color=hline2_color,width=float(pa["hline2_linewidth"]), dash=hline2_linetype))


    return fig

STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
TICKS_DIRECTIONS=["","outside", "inside"]
STANDARD_COLORS=["blue","green","red","cyan","magenta","yellow","black","white", 'lightgray', "limegreen"]


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
        "fig_width":"800",\
        "fig_height":"600",\
        "title":'GSEA plot',\
        "title_size":STANDARD_SIZES,\
        "titles":"20",\
        "xcols":[],\
        "xvals":None,\
        "ycols":[],\
        "yvals":None,\
        "gsea_colors":STANDARD_COLORS,\
        "gseacolor":"limegreen",\
        "gseacolor_cols":["select a column.."],\
        "gseacolor_col":"select a column..",\
        "gseacolor_write":"",\
        "gsea_linewidth_cols":["select a column.."],\
        "gsea_linewidth_col":"select a column..",\
        "gsea_linewidths":STANDARD_SIZES,\
        "gsea_linewidth":"2",\
        "gsea_linestyle": ['-', '--', '-.', ':'],\
        "gsea_linestyle_value": "-",\
        "gene_colors":STANDARD_COLORS,\
        "genecolor":"black",\
        "genecolor_cols":["select a column.."],\
        "genecolor_col":"select a column..",\
        "genecolor_write":"",\
        "gene_linewidth_cols":["select a column.."],\
        "gene_linewidth_col":"select a column..",\
        "gene_linewidths":STANDARD_SIZES,\
        "gene_linewidth":"40",\
        "gene_linestyle": ['-', '--', '-.', ':'],\
        "gene_linestyle_value": "-",\
        "available_labels":[],\
        "fixed_labels":[],\
        "labels_col":["select a column.."],\
        "labels_col_value":"select a column..",\
        "labels_position":"with_genes",\
        "labels_font_size":"10",\
        "labels_font_color":STANDARD_COLORS ,\
        "labels_font_color_value":"black",\
        "labels_arrows":["None","0","1","2","3","4","5","6","7","8"],\
        "labels_arrows_value":"None",\
        "labels_line_width":"0.5",\
        "labels_alpha":"0.5",\
        "labels_colors":STANDARD_COLORS,\
        "labels_colors_value":"black",\
        "labels_ypos": "",\
        "label_angle":"0",\
        "xlabel":"Rank",\
        "xlabel_size":STANDARD_SIZES,\
        "xlabels":"14",\
        "ylabel":"Enrichment Score",\
        "ylabel_size":STANDARD_SIZES,\
        "ylabels":"14",\
        "axis_line_width":"1.0",\
        "left_axis":".off" ,\
        "right_axis":".off",\
        "upper_axis":".off",\
        "lower_axis":".off",\
        "tick_x_axis":".on" ,\
        "tick_y_axis":".on",\
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
        "grid_value":"both",\
        "grid_color_text":"",\
        "grid_colors":STANDARD_COLORS,\
        "grid_color_value":"lightgray",\
        "grid_linestyle":['-', '--', '-.', ':'],\
        "grid_linestyle_value":'--',\
        "grid_linewidth":"1",\
        "grid_alpha":"0.1",\
        "centerline":"0",\
        "center_color_text":"",\
        "center_colors":STANDARD_COLORS,\
        "center_color_value":"black",\
        "center_linestyle":['-', '--', '-.', ':'],\
        "center_linestyle_value":'-',\
        "center_linewidth":"1",\
        "center_alpha":"0.1",\
        "hline1":"",\
        "hline1_color_text":"",\
        "hline1_colors":STANDARD_COLORS,\
        "hline1_color_value":"red",\
        "hline1_linestyle":['-', '--', '-.', ':'],\
        "hline1_linestyle_value":'--',\
        "hline1_linewidth":"1",\
        "hline1_alpha":"0.1",\
        "hline2":"",\
        "hline2_color_text":"",\
        "hline2_colors":STANDARD_COLORS,\
        "hline2_color_value":"red",\
        "hline2_linestyle":['-', '--', '-.', ':'],\
        "hline2_linestyle_value":'--',\
        "hline2_linewidth":"1",\
        "hline2_alpha":"0.1",\
        "vline":"",\
        "vline_value":"None",\
        "vline_color_text":"",\
        "vline_colors":STANDARD_COLORS,\
        "vline_color_value":"blue",\
        "vline_linestyle":['-', '--', '-.', ':'],\
        "vline_linestyle_value":'--',\
        "vline_linewidth":"1",\
        "vline_alpha":"0.1",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"gsea",\
        "session_downloadn":"MySession.igsea.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.igsea.plot",\
        "inputargumentsfile":"Select file.."
    }

    # grid colors not implemented in UI

    return plot_arguments