import matplotlib.pyplot as plt
import matplotlib
from collections import OrderedDict
import numpy as np
from adjustText import adjust_text

import pandas as pd
from bokeh.plotting import figure, show, output_file, ColumnDataSource
from bokeh.sampledata.iris import flowers
from bokeh import models
from bokeh.models import LinearAxis, Range1d, DataRange1d, Legend
from bokeh.palettes import brewer

import mpld3

import math 


def make_figure(df,pa):
    
    valid_indexes=df[[pa["xvals"],pa["yvals"] ]].dropna()
    valid_indexes=valid_indexes.index.tolist()
    valid_df=df[df.index.isin(valid_indexes)]

    if pa["markerstyles_col"] != "select a column..":
        marker=[ str(i) for i in valid_df[[pa["markerstyles_col"]]].dropna()[pa["markerstyles_col"]].tolist() ]
    else:
        marker=pa["marker"]
    valid_df["____marker____"]=marker

    TOOLTIPS = [ ("x", "$x"),("y", "$y") ]

    if pa["labels_col_value"] != "select a column..":
        TOOLTIPS.append(("label", "@label"))

    fig = figure(plot_width=int(pa["fig_width"]), plot_height=int(pa["fig_height"]), tooltips=TOOLTIPS,
        title=pa["title"], x_axis_label=pa["xlabel"], y_axis_label=pa["ylabel"])
    #fig.add_tools(CustomSaveTool(save_name = 'custom name 1'))

    fig.output_backend = {"png":"canvas","svg":"svg"}.get(pa["downloadf"])
    fig.title.vertical_align = 'top'

    if pa["groups_value"]!="None":
        valid_df["___groups___"]=valid_df[pa["groups_value"]].tolist()
        if ( pa["groups_auto_generate"] != "off" ) & (len(set(valid_df[pa["groups_value"]].tolist())) > 1 ) :
            category_items = valid_df[pa["groups_value"]].unique()
            palette = brewer['Set2'][len(category_items) + 1]
            colormap = dict(zip(category_items, palette))
            valid_df["___groups_color___"]=valid_df[pa["groups_value"]].map(colormap)

        if pa["show_legend"] != "off":
            legend_visible=True
        else:
            legend_visible=False            
    else:
        valid_df["___groups___"]="groups"
        legend_visible=False

    groups=list(OrderedDict.fromkeys(valid_df["___groups___"].tolist()))

    for group in groups:
        group_df=valid_df[valid_df["___groups___"]==group]

        markers=list(OrderedDict.fromkeys(group_df["____marker____"].tolist()))
        for marker in markers:
            tmp=group_df[group_df["____marker____"]==marker]
    
            x=tmp[pa["xvals"]].tolist()
            y=tmp[pa["yvals"]].tolist()

            data=dict(x=x,y=y)

            if pa["labels_col_value"] != "select a column..":
                label=tmp[[pa["labels_col_value"]]].astype(str)[pa["labels_col_value"]].tolist()
                data["label"]=label

            if pa["markersizes_col"] != "select a column..":
                s=[ float(i) for i in tmp[pa["markersizes_col"]].tolist() ]
            else:
                s=[ float(pa["markers"]) for i in x ]
            data["size"]=s

            if pa["markeralpha_col_value"] != "select a column..":
                a=[ float(i) for i in  tmp[pa["markeralpha_col_value"]].tolist() ]
            else:
                a=[ float(pa["marker_alpha"]) for i in x ]
            data["alpha"]=a

            if  "___groups_color___" in tmp.columns.tolist():
                c=tmp["___groups_color___"].tolist()
            elif pa["markerc_col"] != "select a column..":
                c=tmp[pa["markerc_col"]].tolist()
            elif str(pa["markerc_write"]) != "":
                c=[ pa["markerc_write"] for i in x ]               
            else:
                c=[ pa["markerc"] for i in x ]
            data["color"]=c
            
            source = ColumnDataSource(data)

            ALLOWED_MARKERS=["asterisk","circle","circle_cross","circle_x","cross","dash","diamond",\
                "diamond_cross","inverted_triangle","square","square_cross","square_x",\
                "triangle","x"]
    
            if marker == "asterisk":
                fig.asterisk('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "circle":
                fig.circle('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "circle_cross":
                fig.circle_cross('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "circle_x":
                fig.circle_x('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "cross":
                fig.cross('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "dash":
                fig.dash('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "diamond":
                fig.diamond('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "diamond_cross":
                fig.diamond_cross('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "inverted_triangle":
                fig.inverted_triangle('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "square":
                fig.square('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "square_cross":
                fig.square_cross('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "square_x":
                fig.square_x('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "triangle":
                fig.triangle('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")
            if marker == "x":
                fig.x('x', 'y', source=source,  size="size", fill_alpha="alpha", line_alpha="alpha", color='color', line_color='color', legend_label=group)#, legend_group="groups")

    fig.legend.label_text_font_size = pa["legend_font_size"]+"pt"
    fig.legend.visible = legend_visible

    if legend_visible:
        new_legend = fig.legend[0]
        fig.legend[0] = None
        fig.add_layout(new_legend, 'right')
        pa["right_axis"] = "off"
        pa["upper_axis"] = "off"

        fig.legend.click_policy="hide"        
    
    fig.title.text_font_size = pa["titles"]+"pt"#'8pt'
    fig.title.align = 'center'

    fig.xaxis.axis_label_text_font_size = pa["xlabels"]+"pt"
    fig.yaxis.axis_label_text_font_size = pa["ylabels"]+"pt"

    if pa["x_lower_limit"]!="":
        fig.x_range.start=float(pa["x_lower_limit"])
    if pa["x_upper_limit"]!="":
        fig.x_range.end=float(pa["x_upper_limit"])

    if pa["y_lower_limit"]!="":
        fig.y_range.start=float(pa["y_lower_limit"])
    if pa["y_upper_limit"]!="":
        fig.y_range.end=float(pa["y_upper_limit"])

    #print(fig.y_range.to_json(include_defaults=True))
    #ystart=fig.y_range.on_change("start")
    #yend=fig.y_range.on_change("end")

    #for axis,argv in zip(['top','bottom','left','right'], [pa["upper_axis"],pa["lower_axis"],pa["left_axis"],pa["right_axis"]]):
    #if pa["right_axis"] == "on":
    fig.extra_y_ranges = {'mocky': DataRange1d(bounds=(None, None)) }
    fig.add_layout(LinearAxis(y_range_name='mocky'), 'right')
    #if pa["upper_axis"] == "on":
    fig.extra_x_ranges = {'mockx': DataRange1d(bounds=(None, None)) }
    fig.add_layout(LinearAxis(x_range_name='mockx'), 'above')

    #fig.v_symmetry=True

    if pa["maxxticks"]!="":
        fig.xaxis.ticker.desired_num_ticks=int(pa["maxxticks"])
    # fig.xaxis[0].ticker.num_minor_ticks=2 # not yet in HTML
    if pa["maxyticks"]!="":
        fig.yaxis.ticker.desired_num_ticks=int(pa["maxyticks"])
    # fig.yaxis[0].ticker.num_minor_ticks=2 # not yet in HTML

    if pa["xticks_rotation"] != "0":
        fig.xaxis.major_label_orientation=math.radians(float(pa["xticks_rotation"]))
    if pa["yticks_rotation"] != "0":
        fig.yaxis.major_label_orientation=math.radians(float(pa["yticks_rotation"]))

    fig.xaxis.major_tick_line_width=float(pa["axis_line_width"])
    fig.yaxis.major_tick_line_width=float(pa["axis_line_width"])
    fig.xaxis.minor_tick_line_width=float(pa["axis_line_width"])
    fig.yaxis.minor_tick_line_width=float(pa["axis_line_width"])

    if pa["lower_axis"] == "on":
        fig.xaxis[1].axis_line_width = float(pa["axis_line_width"])
    else:
        fig.xaxis[1].axis_line_width = 0

    if pa["upper_axis"] == "on":
        fig.xaxis[0].axis_line_width = float(pa["axis_line_width"])
    else:
        fig.xaxis[0].axis_line_width = 0

    if pa["left_axis"] == "on":
        fig.yaxis[0].axis_line_width = float(pa["axis_line_width"])
    else:
        fig.yaxis[0].axis_line_width = 0

    if pa["right_axis"] == "on":
        fig.yaxis[1].axis_line_width = float(pa["axis_line_width"])
    else:
        fig.yaxis[1].axis_line_width = 0

    fig.axis.minor_tick_in = 0
    fig.axis.major_tick_in = 0

    if pa["tick_lower_axis"] == "on":
        fig.xaxis[1].major_tick_out = int(float(pa["ticks_length"]))
        fig.xaxis[1].minor_tick_out = int(float(pa["ticks_length"])/2)
        fig.xaxis[1].major_label_text_font_size = pa["xticks_fontsize"]+"pt"
    else:
        fig.xaxis[1].major_tick_out = 0
        fig.xaxis[1].minor_tick_out = 0
        fig.xaxis[1].major_label_text_font_size ="0pt"

    if pa["tick_upper_axis"] == "on":
        fig.xaxis[0].major_tick_out = int(float(pa["ticks_length"]))
        fig.xaxis[0].minor_tick_out = int(float(pa["ticks_length"])/2)
        fig.xaxis[0].major_label_text_font_size = pa["xticks_fontsize"]+"pt"
    else:
        fig.xaxis[0].major_tick_out = 0
        fig.xaxis[0].minor_tick_out = 0
        fig.xaxis[0].major_label_text_font_size ="0pt"

    if pa["tick_left_axis"] == "on":
        fig.yaxis[0].major_tick_out = int(float(pa["ticks_length"]))
        fig.yaxis[0].minor_tick_out = int(float(pa["ticks_length"])/2)
        fig.yaxis[0].major_label_text_font_size = pa["yticks_fontsize"]+"pt"
    else:
        fig.yaxis[0].major_tick_out = 0
        fig.yaxis[0].minor_tick_out = 0
        fig.yaxis[0].major_label_text_font_size ="0pt"

    if pa["tick_right_axis"] == "on":
        fig.yaxis[1].major_tick_out = int(float(pa["ticks_length"]))
        fig.yaxis[1].minor_tick_out = int(float(pa["ticks_length"])/2)
        fig.yaxis[1].major_label_text_font_size = pa["yticks_fontsize"]+"pt"
    else:
        fig.yaxis[1].major_tick_out = 0
        fig.yaxis[1].minor_tick_out = 0
        fig.yaxis[1].major_label_text_font_size ="0pt"

    #fig.yaxis.major_label_text_font_size ="20pt"

    if pa["grid_color_text"]!="":
        grid_color=pa["grid_color_text"]
    else:
        grid_color=pa["grid_color_value"]

    fig.xgrid.grid_line_color = grid_color
    fig.ygrid.grid_line_color = grid_color

    if pa["grid_value"] == "None":
        fig.xgrid.visible = False
        fig.ygrid.visible = False
    elif pa["grid_value"] == "both":
        fig.xgrid.visible = True
        fig.ygrid.visible = True
    elif pa["grid_value"] == "x":
        fig.xgrid.visible = True
        fig.ygrid.visible = False
    elif pa["grid_value"] == "y":
        fig.xgrid.visible = False
        fig.ygrid.visible = True
    
    fig.grid.grid_line_alpha=float(pa["grid_alpha"])
    fig.grid.grid_line_width=float(pa["grid_linewidth"])
    fig.grid.grid_line_dash=pa["grid_linestyle_value"]

    ## others

    #fig.outline_line_width=float(pa["axis_line_width"])
    #fig.outline_line_alpha=1
    #fig.outline_line_color="black"

    #https://rdrr.io/cran/rbokeh/man/x_axis.html
    #plot.xaxis.visible = False
    #plot.yaxis.visible = False

    #fig.tools[3].name="myname"
    #print(fig.tools[3].name)#, .SaveTool)

    #fig.plot_view.save("my_oh_my_bokeh_plot")
    #from bokeh.models import SaveTool

    #print(help(SaveTool))

    return fig

STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
ALLOWED_MARKERS=["asterisk","circle","circle_cross","circle_x","cross","dash","diamond",\
            "diamond_cross","inverted_triangle","square","square_cross","square_x",\
            "triangle","x"]
TICKS_DIRECTIONS=["in","out","inout"]
STANDARD_COLORS=["blue","green","red","cyan","magenta","yellow","black","white"]


def figure_defaults():
    
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
        "title":'My interactive scatter plot',\
        "title_size":STANDARD_SIZES,\
        "titles":"14",\
        "xcols":[],\
        "xvals":None,\
        "ycols":[],\
        "yvals":None,\
        "groups":["None"],\
        "groups_value":"None",\
        "groups_auto_generate":".on",\
        "show_legend":".on",\
        "legend_font_size":"14",\
        "markerstyles":ALLOWED_MARKERS,\
        "marker":ALLOWED_MARKERS[1],\
        "markerstyles_cols":["select a column.."],\
        "markerstyles_col":"select a column..",\
        "marker_size":STANDARD_SIZES,\
        "markers":"10",\
        "markersizes_cols":["select a column.."],\
        "markersizes_col":"select a column..",\
        "marker_color":STANDARD_COLORS,\
        "markerc":"black",\
        "markerc_write":"",\
        "markerc_cols":["select a column.."],\
        "markerc_col":"select a column..",\
        "marker_alpha":"0.5",\
        "markeralpha_col":["select a column.."],\
        "markeralpha_col_value":"select a column..",\
        "labels_col":["select a column.."],\
        "labels_col_value":"select a column..",\
        "labels_font_size":"10",\
        "labels_font_color":STANDARD_COLORS ,\
        "labels_font_color_value":"black",\
        "labels_arrows":["None","-","->"],\
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
        "grid_value":"both",\
        "grid_color_text":"",\
        "grid_colors":STANDARD_COLORS,\
        "grid_color_value":"black",\
        "grid_linestyle":["solid", "dashed", "dotted", "dotdash", "dashdot"],\
        "grid_linestyle_value":"dashed",\
        "grid_linewidth":"1",\
        "grid_alpha":"0.1",\
        "download_format":["png","svg"],\
        "downloadf":"png",\
        "downloadn":"scatterplot",\
        "session_downloadn":"MySession.scatter.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.scatter.plot",\
        "inputargumentsfile":"Select file.."
    }
    # grid colors not implemented in UI
    # "groups_auto_generate":".on",\ also not implemented in UI

    checkboxes=["left_axis","right_axis","upper_axis","lower_axis",\
            "tick_left_axis","tick_right_axis","tick_upper_axis","tick_lower_axis",\
            "groups_auto_generate","show_legend"]

    # not update list
    notUpdateList=["inputsessionfile"]

    # lists without a default value on the arguments
    excluded_list=[]

    # lists with a default value on the arguments
    allargs=list(plot_arguments.keys())

    # dictionary of the type 
    # {"key_list_name":"key_default_value"} 
    # eg. {"marker_size":"markers"}
    lists={} 
    for i in range(len(allargs)):
        if type(plot_arguments[allargs[i]]) == type([]):
            if allargs[i] not in excluded_list:
                lists[allargs[i]]=allargs[i+1]

    return plot_arguments, lists, notUpdateList, checkboxes

# def input_check(df,pa):
#     errors=[]
#     try:
#         pa["title"]=str(pa["title"])
#     else:
#         errors=errors+["Could not convert title to string."]

#     try:
#         pa["titles"]=int(pa["titles"])
#     except:
#         errors=errors+["Could not convert title size to int."]

#     for x in pa["xcols"]:
#         if x not in df.columns.tolist():
#             errors=errors+["%s could not be found on your dataframe headers." %x]

#     for y in pa["ycols"]:
#         if y not in df.columns.tolist():
#             errors=errors+["%s could not be found on your dataframe headers." %y]

#     if type(pa["xvals"]) != list:
#         if str(pa["xvals"]).lower() == "none":
#             errors=errors+["No x vals selected."]
#         else:
#             errors=errors+["Could not find proper values for x"]
#     else:
#         for v in pa["xvals"]:
#             values=[]
#             try:
#                 values=values+[float(v)]
#             except:
#                 errors=errors+["Could not find proper values for x"]

    

    

    
    

        

            


