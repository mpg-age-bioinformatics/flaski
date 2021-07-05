#from matplotlib.figure import Figure
import plotly.express as px
import plotly.graph_objects as go

from collections import OrderedDict
import numpy as np
import pandas as pd

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
    for arg in ["show_legend","upper_axis","lower_axis","left_axis","right_axis","x_axis_reverse_color_scale","y_axis_reverse_color_scale",\
        "z_axis_reverse_color_scale","x_tick_labels","y_tick_labels","z_tick_labels"]:
        if pa[arg] in ["off",".off"]:
            pab[arg]=False
        else:
            pab[arg]=True

    if pa["ticks_direction_value"] == "None":
        pa["ticks_direction_value"] = ""


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
            z=tmp[pa["zvals"]].tolist()
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
            fig.add_trace(go.Scatter3d(x=x, y=y, z=z, text=text,\
                hovertemplate ='<b>%{text}</b><br><br><b>'+pa["xvals"]+'</b>: %{x}<br><b>'+pa["yvals"]+'</b>: %{y}<br>'+pa["zvals"]+'</b>: %{z}<br><b>' ,
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

        fig.update_layout(legend_title_text=pa["legend_title"], legend=dict( font=dict( size=float(pa["legend_font_size"]), color="black" ) ) )

    
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
            z=tmp[pa["zvals"]].tolist()
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

            fig.add_trace(go.Scatter3d(x=x, y=y,z=z, text=text,\
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

    #fig.update_xaxes(zeroline=False, showline=pab["lower_axis"], linewidth=float(pa["axis_line_width"]), linecolor='black', mirror=pab["upper_axis"])
    #fig.update_yaxes(zeroline=False, showline=pab["left_axis"], linewidth=float(pa["axis_line_width"]), linecolor='black', mirror=pab["right_axis"])

    #fig.update_xaxes(ticks=pa["ticks_direction_value"], tickwidth=float(pa["axis_line_width"]), tickcolor='black', ticklen=float(pa["ticks_length"]) )
    #fig.update_yaxes(ticks=pa["ticks_direction_value"], tickwidth=float(pa["axis_line_width"]), tickcolor='black', ticklen=float(pa["ticks_length"]) )

    fig.update_layout( scene = dict(
        xaxis = dict(
            zeroline = False, 
            showline = pab["lower_axis"], 
            linewidth = float(pa["axis_line_width"]), 
            linecolor = 'black', 
            mirror = pab["upper_axis"],
            ticks = pa["ticks_direction_value"], 
            tickwidth = float(pa["axis_line_width"]), 
            tickcolor = 'black', 
            ticklen = float(pa["ticks_length"]) 
            ),
        yaxis = dict(
            zeroline = False, 
            showline = pab["left_axis"], 
            linewidth = float(pa["axis_line_width"]), 
            linecolor = 'black', 
            mirror = pab["right_axis"],
            ticks = pa["ticks_direction_value"], 
            tickwidth = float(pa["axis_line_width"]), 
            tickcolor = 'black', 
            ticklen = float(pa["ticks_length"])
            ),
        zaxis = dict(
            zeroline = False, 
            showline = pab["lower_axis"], 
            linewidth = float(pa["axis_line_width"]), 
            linecolor = 'black', 
            mirror = pab["upper_axis"],
            ticks = pa["ticks_direction_value"], 
            tickwidth = float(pa["axis_line_width"]), 
            tickcolor = 'black', 
            ticklen = float(pa["ticks_length"]) 
        ),
    ))

    if (pa["x_lower_limit"]!="") and (pa["x_upper_limit"]!="") :
        xmin=float(pa["x_lower_limit"])
        xmax=float(pa["x_upper_limit"])
        fig.update_layout(scene = dict(xaxis = dict(range=[xmin, xmax])))

    if (pa["y_lower_limit"]!="") and (pa["y_upper_limit"]!="") :
        ymin=float(pa["y_lower_limit"])
        ymax=float(pa["y_upper_limit"])
        fig.update_layout(scene = dict(yaxis = dict(range=[ymin, ymax])))

    if (pa["z_lower_limit"]!="") and (pa["z_upper_limit"]!="") :
        zmin=float(pa["z_lower_limit"])
        zmax=float(pa["z_upper_limit"])
        fig.update_layout(scene = dict(zaxis = dict(range=[zmin, zmax])))

    if pa["maxxticks"]!="":
        fig.update_layout(scene = (dict(xaxis = dict(nticks=int(pa["maxxticks"])))))

    if pa["maxyticks"]!="":
        fig.update_layout(scene = (dict(yaxis = dict(nticks=int(pa["maxyticks"])))))

    if pa["maxzticks"]!="":
        fig.update_layout(scene = (dict(zaxis = dict(nticks=int(pa["maxzticks"])))))
    
    fig.update_layout(
        title={
            'text': pa['title'],
            'xanchor': 'left',
            'yanchor': 'top' ,
            "font": {"size": float(pa["titles"]), "color":"black"  } } )

    fig.update_layout(scene = dict(
        xaxis = dict(
        title_text = pa["xlabel"],
        title_font = {"size": int(pa["xlabels"]),"color":"black"},
        tickangle = float(pa["xticks_rotation"]),
        tickfont = dict(size=float(pa["xticks_fontsize"]), color="black"),
        showticklabels = pab["x_tick_labels"] ),
        yaxis = dict(
        title_text = pa["ylabel"],
        title_font = {"size": int(pa["xlabels"]), "color":"black"},
        tickangle = float(pa["yticks_rotation"]),
        tickfont = dict(size=float(pa["yticks_fontsize"]), color="black" ),
        showticklabels = pab["y_tick_labels"]),
        zaxis = dict(
        title_text = pa["zlabel"],
        title_font = {"size": int(pa["zlabels"]), "color":"black"},
        tickangle = float(pa["zticks_rotation"]),
        tickfont = dict(size=float(pa["zticks_fontsize"]), color="black" ),
        showticklabels = pab["z_tick_labels"]),))

    
        

    ## SETTING TIXK ROTATION
    #fig.update_xaxes(tickangle=float(pa["xticks_rotation"]), tickfont=dict(size=float(pa["xticks_fontsize"]), color="black" ))
    #fig.update_yaxes(tickangle=float(pa["yticks_rotation"]), tickfont=dict(size=float(pa["yticks_fontsize"]), color="black" ))


    if pa["grid_value"] != "None":
        if pa["grid_color_text"]!="":
            grid_color=pa["grid_color_text"]
        else:
            grid_color=pa["grid_color_value"]
        if pa["grid_value"] in ["All","x"]:
            fig.update_layout(scene = dict ( xaxis = dict( showgrid=True, gridwidth=float(pa["grid_linewidth"]), gridcolor=grid_color) ))
        else:
            fig.update_layout(scene = dict ( xaxis = dict( showgrid=False, gridwidth=float(pa["grid_linewidth"]), gridcolor=grid_color) ))
        if pa["grid_value"] in ["All","y"]:
            fig.update_layout(scene = dict ( yaxis = dict( showgrid=True, gridwidth=float(pa["grid_linewidth"]), gridcolor=grid_color) ))
        else:
            fig.update_layout(scene = dict ( yaxis = dict( showgrid=False, gridwidth=float(pa["grid_linewidth"]), gridcolor=grid_color) ))
        if pa["grid_value"] in ["All","z"]:
            fig.update_layout(scene = dict ( zaxis = dict( showgrid=True, gridwidth=float(pa["grid_linewidth"]), gridcolor=grid_color) ))
        else:
            fig.update_layout(scene = dict ( zaxis = dict( showgrid=False, gridwidth=float(pa["grid_linewidth"]), gridcolor=grid_color) ))
    else:
        fig.update_layout(scene = dict ( xaxis = dict(showgrid=False), yaxis = dict(showgrid=False), zaxis = dict(showgrid=False) ))
        #fig.update_xaxes(showgrid=False)
        #fig.update_yaxes(showgrid=False)

    if pa["x_axis_background_color_text"] != "":
        x_bg_color=pa["x_axis_background_color_text"]
    else:
        x_bg_color=pa["x_axis_background_color"]
        
    fig.update_layout(scene = dict(xaxis = dict(backgroundcolor = x_bg_color,)))


    if pa["y_axis_background_color_text"] != "":
        y_bg_color=pa["y_axis_background_color_text"]
    else:
        y_bg_color=pa["y_axis_background_color"]
        
    fig.update_layout(scene = dict(yaxis = dict(backgroundcolor = y_bg_color,)))


    if pa["z_axis_background_color_text"] != "":
        z_bg_color=pa["z_axis_background_color_text"]
    else:
        z_bg_color=pa["z_axis_background_color"]
        
    fig.update_layout(scene = dict(zaxis = dict(backgroundcolor = z_bg_color,)))

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
        z_values=tmp[pa["zvals"]].tolist()
        text_values=tmp["___label___"].tolist()

        annotations=[]
        for x,y,z,text in zip(x_values,y_values,z_values,text_values):
            ann=dict(x=x,
                    y=y,
                    z=z,
                    text=text,
                    showarrow=showarrow,
                    arrowhead=arrowhead,
                    #clicktoshow="onoff",
                    visible=True,
                    standoff=standoff,
                    yshift=yshift,
                    opacity=float(pa["labels_alpha"]),
                    arrowwidth=float(pa["labels_line_width"]),
                    arrowcolor=pa["labels_colors_value"],
                    font=dict(
                        size=float(pa["labels_font_size"]),
                        color=pa["labels_font_color_value"]) 
                    )
            annotations.append(ann)

        fig.update_layout(scene=dict(annotations=annotations))
            
        #fig.update_traces(textposition='top center')
    
    if pa["x_axis_plane"] != "":
        selfdefined_cmap=True
        for value in ["x_plane_lower_color","x_plane_upper_color"]:
            if pa[value]=="":
                selfdefined_cmap=False
                break

        if selfdefined_cmap:
            color_continuous_scale=[ [0, pa["x_plane_lower_color"]], [1, pa["x_plane_upper_color"]] ]
            xplane_color=color_continuous_scale
        else:
            xplane_color=pa["x_axis_plane_color_value"]

        
        if pab["x_axis_reverse_color_scale"]:
            xplane_color=xplane_color+"_r"
        
        tmp=df
        x_=tmp[pa["xvals"]]
        y_=tmp[pa["yvals"]]
        z_=tmp[pa["zvals"]]

        length_data = len(z_)
        #z_plane_pos = 150*np.ones((length_data,length_data))

        fig.add_trace(go.Surface(x=x_.apply(lambda x: float(pa["x_axis_plane"])), y=y_, z = np.array([z_]*length_data),\
                            showscale=False, colorscale=xplane_color, opacity=float(pa["x_axis_plane_color_opacity"])))


    if pa["y_axis_plane"] != "":
        selfdefined_cmap=True
        for value in ["y_plane_lower_color","y_plane_upper_color"]:
            if pa[value]=="":
                selfdefined_cmap=False
                break
            
        if selfdefined_cmap:
            color_continuous_scale=[ [0, pa["y_plane_lower_color"]], [1, pa["y_plane_upper_color"]] ]
            yplane_color=color_continuous_scale
        else:
            yplane_color=pa["y_axis_plane_color_value"]
        
        if pab["y_axis_reverse_color_scale"]:
            yplane_color=yplane_color+"_r"
            
        tmp=df
        x_=tmp[pa["xvals"]]
        y_=tmp[pa["yvals"]]
        z_=tmp[pa["zvals"]]

        length_data = len(z_)
        #z_plane_pos = 150*np.ones((length_data,length_data))

        fig.add_trace(go.Surface(x=x_, y= y_.apply(lambda x: float(pa["y_axis_plane"])), z =  np.array([z]*length_data).transpose(),\
                        colorscale=yplane_color, showscale=False, opacity=float(pa["y_axis_plane_color_opacity"])))
        
    if pa["z_axis_plane"] != "":
        selfdefined_cmap=True
        for value in ["z_plane_lower_color","z_plane_upper_color"]:
            if pa[value]=="":
                selfdefined_cmap=False
                break

        if selfdefined_cmap:
            color_continuous_scale=[ [0, pa["z_plane_lower_color"]], [1, pa["z_plane_upper_color"]] ]
            zplane_color=color_continuous_scale
        
            
        if pab["z_axis_reverse_color_scale"]:
            zplane_color=zplane_color+"_r"
            
        tmp=df
        x_=tmp[pa["xvals"]]
        y_=tmp[pa["yvals"]]
        z_=tmp[pa["zvals"]]

        length_data = len(z_)
        z_plane_pos = float(pa["z_axis_plane"])*np.ones((length_data,length_data))

        fig.add_trace(go.Surface(x=x_, y=y_, z=z_plane_pos, colorscale=zplane_color,  showscale=False, opacity=float(pa["z_axis_plane_color_opacity"])))
        

    return fig

STANDARD_SIZES=[ str(i) for i in list(range(101)) ]

ALLOWED_MARKERS=['circle', 'circle-open', 'square', 'square-open','diamond', 'diamond-open', 'cross', 'x']
TICKS_DIRECTIONS=["None","outside", "inside"]
STANDARD_COLORS=["blue","green","red","cyan","magenta","yellow","black","white"]
PLANE_COLORS=['aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance', 'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg',
'brwnyl', 'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl', 'darkmint', 'deep', 'delta', 'dense', 'earth', 'edge', 'electric',
'emrld', 'fall', 'geyser', 'gnbu', 'gray', 'greens', 'greys', 'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno', 'jet',
'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges', 'orrd', 'oryel', 'peach', 'phase', 'picnic', 'pinkyl', 'piyg',
'plasma', 'plotly3', 'portland', 'prgn', 'pubu', 'pubugn', 'puor', 'purd', 'purp', 'purples', 'purpor', 'rainbow', 'rdbu', 'rdgy',
'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds', 'solar', 'spectral', 'speed', 'sunset', 'sunsetdark', 'teal', 'tealgrn', 'tealrose',
'tempo', 'temps', 'thermal', 'tropic', 'turbid', 'twilight', 'viridis', 'ylgn', 'ylgnbu', 'ylorbr', 'ylorrd']



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
        "title":'3D Scatter plot',\
        "title_size":STANDARD_SIZES,\
        "titles":"20",\
        "xcols":[],\
        "xvals":None,\
        "ycols":[],\
        "yvals":None,\
        "zcols":[],\
        "zvals":None,\
        "groups":["None"],\
        "groups_value":"None",\
        "list_of_groups":[],\
        "groups_settings":[],\
        "show_legend":".on",\
        "legend_title":"",\
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
        "zlabel":"z",\
        "zlabel_size":STANDARD_SIZES,\
        "zlabels":"14",\
        "axis_line_width":"1.0",\
        "left_axis":".on" ,\
        "right_axis":".on",\
        "upper_axis":".on",\
        "lower_axis":".on",\
        # "tick_left_axis":".on" ,\
        # "tick_right_axis":".off",\
        # "tick_upper_axis":".off",\
        # "tick_lower_axis":".on",\
        "x_tick_labels":".on",\
        "y_tick_labels":".on",\
        "z_tick_labels":".on",\
        "ticks_direction":TICKS_DIRECTIONS,\
        "ticks_direction_value":TICKS_DIRECTIONS[1],\
        "ticks_length":"6.0",\
        "xticks_fontsize":"14",\
        "yticks_fontsize":"14",\
        "zticks_fontsize":"14",\
        "xticks_rotation":"0",\
        "yticks_rotation":"0",\
        "zticks_rotation":"0",\
        "x_lower_limit":"",\
        "y_lower_limit":"",\
        "z_lower_limit":"",\
        "x_upper_limit":"",\
        "y_upper_limit":"",\
        "z_upper_limit":"",\
        "maxxticks":"",\
        "maxyticks":"",\
        "maxzticks":"",\
        "grid":["None","All","x","y","z"],\
        "grid_value":"None",\
        "grid_color_text":"",\
        "grid_colors":STANDARD_COLORS,\
        "grid_color_value":"black",\
        "grid_linestyle":['-', '--', '-.', ':'],\
        "grid_linestyle_value":'--',\
        "grid_linewidth":"1",\
        "grid_alpha":"0.1",\
        "plane_colors":PLANE_COLORS,\
        "x_axis_plane":"",\
        #"x_axis_plane_color_text":"",\
        "x_axis_plane_color_value":"blues",\
        "x_axis_reverse_color_scale":".off",\
        "x_plane_lower_color":"",\
        "x_plane_upper_color":"",\
        "x_axis_plane_color_opacity":"0.1",\
        "x_axis_background_colors":STANDARD_COLORS,\
        "x_axis_background_color":"white",\
        "x_axis_background_color_text":"",\
        "y_axis_plane":"",\
        #"y_axis_plane_color_text":"",\
        "y_axis_plane_color_value":"blues",\
        "y_axis_reverse_color_scale":".off",\
        "y_plane_lower_color":"",\
        "y_plane_upper_color":"",\
        "y_axis_plane_color_opacity":"0.1",\
        "y_axis_background_colors":STANDARD_COLORS,\
        "y_axis_background_color":"white",\
        "y_axis_background_color_text":"",\
        "z_axis_plane":"",\
        #"z_axis_plane_color_text":"",\
        "z_axis_plane_color_value":"blues",\
        "z_axis_reverse_color_scale":".off",\
        "z_plane_lower_color":"",\
        "z_plane_upper_color":"",\
        "z_axis_plane_color_opacity":"0.1",\
        "z_axis_background_colors":STANDARD_COLORS,\
        "z_axis_background_color":"white",\
        "z_axis_background_color_text":"",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"ThreeDscatterplot",\
        "session_downloadn":"MySession.ThreeDscatter.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.ThreeDscatter.plot",\
        "inputargumentsfile":"Select file.."
    }

    # grid colors not implemented in UI

    return plot_arguments