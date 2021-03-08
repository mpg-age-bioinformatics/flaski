# from scipy import stats
import numpy as np
import pandas as pd
import seaborn as sns
from functools import reduce
import matplotlib.pyplot as plt
from collections import OrderedDict
import plotly.express as px
import plotly.graph_objects as go


def make_figure(df,pa):
    df_circ=df.copy()
    
    r=pa["angvals"]
    print(r)
    theta=pa["radvals"]
    print(theta)
    color=pa["groupval"]
    print(color)

    ## Fit the data into the model

    pa_={}
    for n in ["fig_width","fig_height"]:
        if pa[n] == "":
            pa_[n]=None
        else:
            pa_[n]=float(pa[n])

    for n in ["angular_grid","angular_line","angular_ticklabels","radial_grid","radial_line","radial_visibility","radial_ticklabels"]:
        if pa[n] in ["off", ".off"]:
            pa_[n]=False
        else:
            pa_[n]=True

    color_discrete_sequence_=[]

    if str(pa["groupval"]) == "None":
        colorv=None
        print(pa["bar_colour_val"])
        color_discrete_sequence_.append( pa["bar_colour_val"] )

    elif str(pa["groupval"]) != "None":
        colorv=str(color)
        
        for group in pa["list_of_groups"]:

            PA_=[ g for g in pa["groups_settings"] if g["name"]==group ][0]

            barColor=PA_["bar_colour_val"]
            color_discrete_sequence_.append(barColor)
    
    print(color_discrete_sequence_)

    fig = px.bar_polar(df_circ, r=str(r), theta=str(theta), color=colorv,
                   color_discrete_sequence=color_discrete_sequence_, ## Fix according to groups/colors
                   barnorm=pa["barnorm_val"],  
                   barmode=pa["barmode_val"], 
                   direction=pa["direction_val"], 
                   start_angle=int(pa["start_angle"]), 
                   title=pa["title"])


    fig.update_layout(width=pa_["fig_width"], height=pa_["fig_height"], template="plotly_white",

                  legend = dict(bgcolor = pa["legend_bgcolor"], bordercolor=pa["legend_bordercolor"], borderwidth=float(pa["legend_borderwidth"]), 
                                font={"color":"black","family":"sans serif", "size":int(pa["legend_title_font"])},
                                orientation=pa["legend_orientation"], title={"text":"group","font":{"color":"black","size":int(pa["legend_text_font"]), "family":"sans serif"}}), 
                  
                  font=dict(color="black", family="sans serif", size=int(pa["plot_font"])), 
                  
                  title=dict(font={"family":"sans serif","size":int(pa["titles"]),"color":pa["title_color"]}, xanchor="center", x=0.5),

                  polar_bargap=float(pa["polar_bargap"]),
                  polar_barmode=pa["polar_barmode"],
                  polar_bgcolor=pa["polar_bgcolor"],
                  polar_hole=float(pa["polar_hole"]),
                  paper_bgcolor=pa["paper_bgcolor"], 
                  
                  polar_angularaxis=dict(showgrid=pa_["angular_grid"], gridcolor=pa["angular_gridcolor"], gridwidth=float(pa["angular_gridwidth"]),
                                         showline=pa_["angular_line"], linecolor=pa["angular_linecolor"], linewidth=float(pa["angular_linewidth"]),
                                         showticklabels=pa_["angular_ticklabels"], tickcolor=pa["angular_tickcolor"], ticklen=float(pa["angular_ticklen"]), 
                                         tickangle=float(pa["angular_tickangle"]), tickwidth=float(pa["angular_tickwidth"]), ticks=pa["angular_ticks"]), 

                  polar_radialaxis=dict(showgrid=pa_["radial_grid"], gridcolor=pa["radial_gridcolor"], gridwidth=float(pa["radial_gridwidth"]), 
                                        showline=pa_["radial_line"], linecolor=pa["radial_linecolor"], visible=pa_["radial_visibility"], 
                                        linewidth=float(pa["radial_linewidth"]), angle=float(pa["radial_angle"]), tickangle=float(pa["radial_tickangle"]), 
                                        ticklen=float(pa["radial_ticklen"]), tickwidth=float(pa["radial_tickwidth"]),tickcolor=pa["radial_tickcolor"],
                                        showticklabels=pa_["radial_ticklabels"], ticks=pa["radial_tickside"]), 
                  
                 )

    return fig
        

STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
STANDARD_GAPS= ['0.0','0.1','0.2','0.3','0.4','0.5','0.6','0.7','0.8','0.9','1.0']
STANDARD_COLORS=["aliceblue","antiquewhite","aqua","aquamarine","azure","beige",\
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
LINE_STYLES=["solid","dashed","dashdot","dotted"]
HIST_TYPES=['bar', 'barstacked', 'step',  'stepfilled']
STANDARD_ORIENTATIONS=['vertical','horizontal']
STANDARD_ALIGNMENTS=['left','right','mid']
STANDARD_DIRECTIONS=["counterclockwise","clockwise"]
TICKS_DIRECTIONS=["outside","inside",""]

LEGEND_ORIENTATION=['v','h']

BAR_MODES=["group","overlay","relative"]  
POLAR_BAR_MODES=["stack","overlay"] ## how to deal with bars that have the same coordinates
MODES=["expand",None]


def figure_defaults():
    """Generates default figure arguments.
    Returns:
        dict: A dictionary of the style { "argument":"value"}
    """
    plot_arguments={
        "fig_width":"800",\
        "fig_height":"600",\
        "title":'Circular Barplot',\
        "title_size":STANDARD_SIZES,\
        "titles":"28",\
        "title_colors":STANDARD_COLORS,\
        "title_color":"pink",\
        "angcols":[],\
        "angvals":"",\
        "radcols":[],\
        "radvals":"",\
        "group":["None"],\
        "groupval":"",\
        "groups_settings":[],\
        "bar_colours":STANDARD_COLORS,\
        "bar_colour_val":"blue",\
        "barmode":BAR_MODES,\
        "barmode_val":"relative",\
        "barnorm":["","fraction","percent"],\
        "barnorm_val":"",\
        "direction":STANDARD_DIRECTIONS,\
        "direction_val":"clockwise",\
        "start_angle":"90",\
        "plot_font_sizes":STANDARD_SIZES,\
        "plot_font":"10",\
        "legend_bgcolor":"cyan",\
        "legend_bordercolor":"black",\
        "legend_colors":STANDARD_COLORS,\
        "legend_borderwidth":"0.25",\
        "legend_title_sizes":STANDARD_SIZES,\
        "legend_title_font":"10",\
        "legend_text_sizes":STANDARD_SIZES,\
        "legend_text_font":"12",\
        "legend_orientation":"v",\
        "legend_orientations":LEGEND_ORIENTATION,\
        "polar_bargaps":STANDARD_GAPS,\
        "polar_bargap":"0.4",\
        "polar_barmodes":POLAR_BAR_MODES,\
        "polar_barmode":"overlay",\
        "polar_bgcolors":STANDARD_COLORS,\
        "polar_bgcolor":"lightblue",\
        "polar_holes":STANDARD_GAPS,\
        "polar_hole":"0.05",\
        "paper_bgcolors":STANDARD_COLORS,\
        "paper_bgcolor":"dimgrey",\
        "angular_grid":".off",\
        "angular_gridcolors":STANDARD_COLORS,\
        "angular_gridcolor":"black",\
        "angular_gridwidth":"0.5",\
        "angular_line":".on",\
        "angular_linecolors":STANDARD_COLORS,\
        "angular_linecolor":"black",\
        "angular_linewidth":"0.5",\
        "angular_ticklabels":".off",\
        "angular_tickcolors":STANDARD_COLORS,\
        "angular_tickcolor":"black",\
        "angular_ticklen":"2.0",\
        "angular_tickwidth":"0",\
        "angular_tickangle":"0",\
        "angular_tickDirections":TICKS_DIRECTIONS,\
        "angular_ticks":"outside",\
        "radial_grid":".off",\
        "radial_gridcolors":STANDARD_COLORS,\
        "radial_gridcolor":"black",\
        "radial_gridwidth":"0.5",\
        "radial_line":".on",\
        "radial_linecolors":STANDARD_COLORS,\
        "radial_linecolor":"black",\
        "radial_visibility":".on",\
        "radial_linewidth":"1.25", 
        "radial_angle":"90",\
        "radial_tickangle":"90",\
        "radial_ticklen":"0",\
        "radial_tickwidth":"0",\
        "radial_tickcolors":STANDARD_COLORS,\
        "radial_tickcolor":"black",\
        "radial_ticklabels":"o.n",\
        "radial_ticksides":TICKS_DIRECTIONS,\
        "radial_tickside":"inside",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"CircularBarPlot",\
        "session_downloadn":"MySession.CircularBarPlot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.CircularBarPlot",\
        "inputargumentsfile":"Select file.."}

    return plot_arguments