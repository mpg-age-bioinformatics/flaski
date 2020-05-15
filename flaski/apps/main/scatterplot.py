#from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
from collections import OrderedDict
import numpy as np
from adjustText import adjust_text


import mpld3

matplotlib.use('agg')


def GET_COLOR(x):
    if str(x)[:3].lower() == "rgb":
        vals=x.split("rgb(")[-1].split(")")[0].split(",")
        vals=[ float(s.strip(" ")) for s in vals ]
        #vals=tuple(vals)
        return vals
    else:
        return str(x)


def make_figure(df,pa):

    #matplotlib.rcParams['axes.linewidth'] = float(pa["axis_line_width"])

    # MAIN FIGURE
    #fig=plt.figure(figsize=(float(pa["fig_width"]),float(pa["fig_height"])))

    fig, ax = plt.subplots(figsize=(float(pa["fig_width"]),float(pa["fig_height"])))

    # if we have groups
    # the user can decide how the diferent groups should look like 
    # by unchecking the groups_autogenerate check box

    print(pa["xvals"],pa["yvals"])

    if str(pa["groups_value"])!="None":
        for group in list(OrderedDict.fromkeys(df[pa["groups_value"]].tolist())):
            tmp=df[df[pa["groups_value"]]==group]

            x=tmp[pa["xvals"]].tolist()
            y=tmp[pa["yvals"]].tolist()

            if pa["groups_auto_generate"] == "off" :

                if pa["markeralpha_col_value"] != "select a column..":
                    a=[ float(i) for i in tmp[[pa["markeralpha_col_value"]]].dropna()[pa["markeralpha_col_value"]].tolist() ][0]
                else:
                    a=float(pa["marker_alpha"])

                if pa["markerstyles_col"] != "select a column..":
                    marker=[ str(i) for i in tmp[[pa["markerstyles_col"]]].dropna()[pa["markerstyles_col"]].tolist() ][0]
                else:
                    marker=pa["marker"]

                if pa["markersizes_col"] != "select a column..":
                    s=[ float(i) for i in tmp[[pa["markersizes_col"]]].dropna()[pa["markersizes_col"]].tolist() ][0]
                else:
                    s=float(pa["markers"])

                if pa["markerc_col"] != "select a column..":
                    c=[ GET_COLOR(i) for i in tmp[[pa["markerc_col"]]].dropna()[pa["markerc_col"]].tolist()][0]
                    if type(c) == list:
                        c=np.array([c]*len(tmp))/255.0
                elif str(pa["markerc_write"]) != "":
                    c=GET_COLOR(pa["markerc_write"])
                    if type(c) == list:
                        c=np.array([c]*len(tmp))/255.0
                else:
                    c=pa["markerc"]


                if pa["edgecolor_col"] != "select a column..":
                    edgecolor=[ GET_COLOR(i) for i in tmp[[pa["edgecolor_col"]]].dropna()[pa["edgecolor_col"]].tolist()][0]
                    if type(edgecolor) == list:
                        edgecolor=np.array([edgecolor]*len(tmp))/255.0
                elif str(pa["edgecolor_write"]) != "":
                    edgecolor=GET_COLOR(pa["edgecolor_write"])
                    if type(edgecolor) == list:
                        edgecolor=np.array([edgecolor]*len(tmp))/255.0
                else:
                    edgecolor=pa["edgecolor"]

                if pa["edge_linewidth_col"] != "select a column..":
                    edge_linewidth=[ float(i) for i in tmp[[pa["edge_linewidth_col"]]].dropna()[pa["edge_linewidth_col"]].tolist() ][0]
                else:
                    edge_linewidth=float(pa["edge_linewidth"])

                ax.scatter(x, y, \
                    marker=marker, \
                    edgecolor=edgecolor,\
                    linewidth=edge_linewidth,\
                    s=s,\
                    c=c,\
                    alpha=a,\
                    label=group)
            
            else:
                ax.scatter(x, y, \
                    label=group)

        if pa["show_legend"] != "off" :        
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., fontsize=pa["legend_font_size"])
    
    elif pa["groups_value"]=="None":

        if pa["markeralpha_col_value"] != "select a column..":
            markers_alpha=[ float(i) for i in df[pa["markeralpha_col_value"]].tolist() ]
            df["__alpha__"]=markers_alpha
        else:
            df["__alpha__"]=float(pa["marker_alpha"])

        if pa["markerstyles_col"] != "select a column..":
            markers=[ str(i) for i in df[pa["markerstyles_col"]].tolist() ]
            df["__marker__"]=markers
        else:
            df["__marker__"]=pa["marker"]
    
        for marker in list(OrderedDict.fromkeys(df["__marker__"].tolist())):
            tmp=df[df["__marker__"]==marker]

            for marker_alpha in list(OrderedDict.fromkeys(tmp["__alpha__"].tolist())):
                tmp_alpha=tmp[tmp["__alpha__"]==marker_alpha]

                x=tmp_alpha[pa["xvals"]].tolist()
                y=tmp_alpha[pa["yvals"]].tolist()

                if pa["markersizes_col"] != "select a column..":
                    s=[ float(i) for i in tmp[pa["markersizes_col"]].tolist() ]
                else:
                    s=float(pa["markers"])

                if pa["markerc_col"] != "select a column..":
                    c=[ GET_COLOR(i) for i in tmp[pa["markerc_col"]].tolist() ]
                    if not all(isinstance(i, str) for i in c) :
                        c=np.array(c)/255.0
                elif str(pa["markerc_write"]) != "":
                    c=GET_COLOR(pa["markerc_write"])
                    if type(c) == list:
                        c=np.array([c]*len(tmp_alpha))/255.0
                else:
                    c=pa["markerc"]

                if pa["edgecolor_col"] != "select a column..":
                    edgecolor=[ GET_COLOR(i) for i in tmp[[pa["edgecolor_col"]]].dropna()[pa["edgecolor_col"]].tolist()][0]
                    if type(edgecolor) == list:
                        edgecolor=np.array([edgecolor]*len(tmp))/255.0
                elif str(pa["edgecolor_write"]) != "":
                    edgecolor=GET_COLOR(pa["edgecolor_write"])
                    if type(edgecolor) == list:
                        edgecolor=np.array([edgecolor]*len(tmp))/255.0
                else:
                    edgecolor=pa["edgecolor"]

                if pa["edge_linewidth_col"] != "select a column..":
                    edge_linewidth=[ float(i) for i in tmp[[pa["edge_linewidth_col"]]].dropna()[pa["edge_linewidth_col"]].tolist() ][0]
                else:
                    edge_linewidth=float(pa["edge_linewidth"])

                ax.scatter(x, y, \
                    marker=marker, \
                    edgecolor=edgecolor,\
                    linewidth=edge_linewidth,\
                    s=s,\
                    c=c,\
                    alpha=marker_alpha)

                
    axes=plt.gca()

    for axis in ['top','bottom','left','right']:
        axes.spines[axis].set_linewidth(float(pa["axis_line_width"]))

    for axis,argv in zip(['top','bottom','left','right'], [pa["upper_axis"],pa["lower_axis"],pa["left_axis"],pa["right_axis"]]):
        if (argv =="on") | (argv ==".on"):
            axes.spines[axis].set_visible(True)
        else:
            axes.spines[axis].set_visible(False)

    ticks={}
    for axis,argv in zip(['top','bottom','left','right'], \
        [pa["tick_upper_axis"],pa["tick_lower_axis"],pa["tick_left_axis"],pa["tick_right_axis"]]):
        if (argv =="on") | (argv ==".on"):
            show=True
        else:
            show=False
        ticks[axis]=show

    axes.tick_params(right= ticks["right"],top=ticks["top"],\
        left=ticks["left"], bottom=ticks["bottom"])

    axes.tick_params(direction=pa["ticks_direction_value"], width=float(pa["axis_line_width"]),length=float(pa["ticks_length"]))  

    if (pa["x_lower_limit"]!="") or (pa["x_upper_limit"]!="") :
        xmin, xmax = axes.get_xlim()
        if pa["x_lower_limit"]!="":
            xmin=float(pa["x_lower_limit"])
        if pa["x_upper_limit"]!="":
            xmax=float(pa["x_upper_limit"])
        plt.xlim(xmin, xmax)

    if (pa["y_lower_limit"]!="") or (pa["y_upper_limit"]!="") :
        ymin, ymax = axes.get_ylim()
        if pa["y_lower_limit"]!="":
            ymin=float(pa["y_lower_limit"])
        if pa["y_upper_limit"]!="":
            ymax=float(pa["y_upper_limit"])
        plt.ylim(xmin, ymax)

    if pa["maxxticks"]!="":
        axes.xaxis.set_major_locator(plt.MaxNLocator(int(pa["maxxticks"])))

    if pa["maxyticks"]!="":
        axes.yaxis.set_major_locator(plt.MaxNLocator(int(pa["maxyticks"])))

    plt.title(pa['title'], fontsize=int(pa["titles"]))
    plt.xlabel(pa["xlabel"], fontsize=int(pa["xlabels"]))
    plt.ylabel(pa["ylabel"], fontsize=int(pa["ylabels"]))

    plt.xticks(fontsize=float(pa["xticks_fontsize"]), rotation=float(pa["xticks_rotation"]))
    plt.yticks(fontsize=float(pa["yticks_fontsize"]), rotation=float(pa["yticks_rotation"]))

    if pa["grid_value"] != "None":
        if pa["grid_color_text"]!="":
            grid_color=GET_COLOR(pa["grid_color_text"])
        else:
            grid_color=GET_COLOR(pa["grid_color_value"])

        axes.grid(axis=pa["grid_value"], color=grid_color, linestyle=pa["grid_linestyle_value"], linewidth=float(pa["grid_linewidth"]), alpha=float(pa["grid_alpha"]) )

    if pa["labels_col_value"] != "select a column..":
        tmp=df[[pa["xvals"],pa["yvals"],pa["labels_col_value"] ]].dropna()
        x=tmp[pa["xvals"]].tolist()
        y=tmp[pa["yvals"]].tolist()
        t=tmp[pa["labels_col_value"]].tolist()
        texts = [plt.text( x[i], y[i], t[i] , size=float(pa["labels_font_size"]), color=pa["labels_font_color_value"] ) for i in range(len(x))]
        if pa["labels_arrows_value"] != "None":
            adjust_text(texts, arrowprops=dict(arrowstyle=pa["labels_arrows_value"], color=pa['labels_colors_value'], lw=float(pa["labels_line_width"]), alpha=float(pa["labels_alpha"]) ))
        else:
            adjust_text(texts)

    plt.tight_layout()
    
    return fig

STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
ALLOWED_MARKERS=[".",",","o","v","^","<",">",\
            "1","2","3","4","8",\
            "s","p","*","h","H","+","x",\
            "X","D","d","|","_"]
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
        "fig_width":"6.0",\
        "fig_height":"6.0",\
        "title":'Scatter plot',\
        "title_size":STANDARD_SIZES,\
        "titles":"20",\
        "xcols":[],\
        "xvals":None,\
        "ycols":[],\
        "yvals":None,\
        "groups":["None"],\
        "groups_value":"None",\
        "groups_settings":[],\
        "show_legend":".on",\
        "legend_font_size":"14",\
        "markerstyles":ALLOWED_MARKERS,\
        "marker":".",\
        "markerstyles_cols":["select a column.."],\
        "markerstyles_col":"select a column..",\
        "marker_size":STANDARD_SIZES,\
        "markers":"50",\
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
        "grid_value":"None",\
        "grid_color_text":"",\
        "grid_colors":STANDARD_COLORS,\
        "grid_color_value":"black",\
        "grid_linestyle":['-', '--', '-.', ':'],\
        "grid_linestyle_value":'--',\
        "grid_linewidth":"1",\
        "grid_alpha":"0.1",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"scatterplot",\
        "session_downloadn":"MySession.scatter.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.scatter.plot",\
        "inputargumentsfile":"Select file.."
    }
    # grid colors not implemented in UI


    checkboxes=["left_axis","right_axis","upper_axis","lower_axis",\
            "tick_left_axis","tick_right_axis","tick_upper_axis","tick_lower_axis",\
            ,"show_legend"]

    # not update list
    notUpdateList=["inputsessionfile"]

    # lists without a default value on the arguments
    excluded_list=["groups_settings"]

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

    

    

    
    

        

            


