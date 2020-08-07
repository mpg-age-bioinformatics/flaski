# from scipy import stats
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter
import math
import seaborn as sns
from functools import reduce
import matplotlib.pyplot as plt
from collections import OrderedDict

marker_dict={'point':'.',\
             'pixel':',',\
             'circle':'o',\
             'triangle_down':'v',\
             'triangle_up':'^',\
             'triangle_left':'<',\
	         'triangle_right':'>',\
	         'tri_down': '1',\
	         'tri_up': '2',\
	         'tri_left': '3',\
	         'tri_right': '4',\
	         'square': 's',\
	         'pentagon': 'p',\
	         'star': '*',\
	         'hexagon1': 'h',\
	         'hexagon2': 'H',\
	         'plus': '+',\
	         'x': 'x',\
	         'diamond': 'D',\
             'thin_diamond':'d',\
             'vline':'|',\
             'hline':'_'}

def make_figure(df,pa):
    df_ls=df.copy()
    
    durations=df_ls[pa["xvals"]]
    event_observed=df_ls[pa["yvals"]]

    km = KaplanMeierFitter() ## instantiate the class to create an object

    fig = plt.figure(frameon=False, figsize=(float(pa["fig_width"]),float(pa["fig_height"])))

    ## Fit the data into the model

    if str(pa["groups_value"]) == "None":
        km.fit(durations, event_observed,label='Kaplan Meier Estimate')

        df_survival=km.survival_function_
        df_conf=km.confidence_interval_
        df_event=km.event_table

        df=pd.merge(df_survival,df_conf, how='left', left_index=True, right_index=True)
        df=pd.merge(df,df_event, how='left', left_index=True, right_index=True)

        df['time']=df.index.tolist()
        df=df.reset_index(drop=True)
        df=df[["time","at_risk","removed","observed","censored","entrance","Kaplan Meier Estimate","Kaplan Meier Estimate_lower_0.95","Kaplan Meier Estimate_upper_0.95"]]
    
        pa_={}
        for arg in ["Conf_Interval","show_censors","ci_legend","ci_force_lines","left_axis", "right_axis" , "upper_axis", "lower_axis","tick_left_axis","tick_right_axis","tick_upper_axis","tick_lower_axis"]:
            if pa[arg] in ["off", ".off"]:
                pa_[arg]=False
            else:
                pa_[arg]=True

        if str(pa["markerc_write"]) != "":
            pa_["marker_fc"]=pa["markerc_write"]
        else:
            pa_["marker_fc"]=pa["markerc"]

        if str(pa["edgecolor_write"]) != "":
            pa_["marker_ec"]=pa["edgecolor_write"]
        else:
            pa_["marker_ec"]=pa["edgecolor"]

        if str(pa["grid_color_text"]) != "":
            pa_["grid_color_write"]=pa["grid_color_text"]
        else:
            pa_["grid_color_write"]=pa["grid_color_value"]

        pl=km.plot(show_censors=pa_["show_censors"], \
                censor_styles={"marker":marker_dict[pa["censor_marker_value"]], "markersize":float(pa["censor_marker_size_val"]), "markeredgecolor":pa_["marker_ec"], "markerfacecolor":pa_["marker_fc"], "alpha":float(pa["marker_alpha"])}, \
               ci_alpha=float(pa["ci_alpha"]), \
               ci_force_lines=pa_["ci_force_lines"], \
               ci_show=pa_["Conf_Interval"], \
               ci_legend=pa_["ci_legend"], \
               linestyle=pa["linestyle_value"], \
               linewidth=float(pa["linewidth"]))

        pl.spines['right'].set_visible(pa_["right_axis"])
        pl.spines['top'].set_visible(pa_["upper_axis"])
        pl.spines['left'].set_visible(pa_["left_axis"])
        pl.spines['bottom'].set_visible(pa_["lower_axis"])

        pl.spines['right'].set_linewidth(pa["axis_line_width"])
        pl.spines['left'].set_linewidth(pa["axis_line_width"])
        pl.spines['top'].set_linewidth(pa["axis_line_width"])
        pl.spines['bottom'].set_linewidth(pa["axis_line_width"])
        
        pl.tick_params(axis="both", direction=pa["ticks_direction_value"], length=float(pa["ticks_length"]))

        pl.tick_params(axis='x',which='both',bottom=pa_["tick_lower_axis"],top=pa_["tick_upper_axis"],labelbottom=pa_["lower_axis"], 
                       labelrotation=float(pa["xticks_rotation"]), labelsize=float(pa["xticks_fontsize"]))
                       
        pl.tick_params(axis='y',which='both',left=pa_["tick_left_axis"],right=pa_["tick_right_axis"],labelleft=pa_["left_axis"], 
                       labelrotation=float(pa["yticks_rotation"]), labelsize=float(pa["yticks_fontsize"]))

        if str(pa["grid_value"]) != "None":
            pl.grid(True, which='both',axis=pa["grid_value"], color=pa_["grid_color_write"], linewidth=float(pa["grid_linewidth"]))
                       
        if str(pa["x_lower_limit"]) != "" and str(pa["x_upper_limit"]) != "":
            pl.set_xlim(float(pa["x_lower_limit"]),float(pa["x_upper_limit"]))
        if str(pa["y_lower_limit"]) != "" and str(pa["y_upper_limit"]) != "":
            pl.set_ylim(float(pa["y_lower_limit"]),float(pa["y_upper_limit"])) 

        pl.set_title(pa["title"], fontdict={'fontsize':float(pa['titles'])})
        pl.set_xlabel(pa["xlabel"], fontdict={'fontsize':float(pa['xlabels'])})
        pl.set_ylabel(pa["ylabel"], fontdict={'fontsize':float(pa['ylabels'])})

        return df, pl

    elif str(pa["groups_value"]) != "None":
        groups = df_ls[pa["groups_value"]]
        tmp=[]
        for cond in list(set(df_ls[pa["groups_value"]].tolist())):
            ix = (groups == cond)
            km.fit(durations[ix], event_observed[ix], label=cond)

            df_survival=km.survival_function_
            df_conf=km.confidence_interval_
            df_event=km.event_table
            
            df=pd.merge(df_survival,df_conf, how='left', left_index=True, right_index=True)
            df=pd.merge(df,df_event, how='left', left_index=True, right_index=True)

            df['time']=df.index.tolist()
            df=df.reset_index(drop=True)
            df=df.rename(columns={"at_risk":cond+"_at_risk",
                                 "removed":cond+"_removed",
                                 "observed":cond+"_observed",
                                 "censored":cond+"_censored",
                                 "entrance":cond+"_entrance",
                                 cond:cond+"_KMestimate"})
            df=df[["time",cond+"_at_risk",cond+"_removed",cond+"_observed",cond+"_censored",cond+"_entrance",cond+"_KMestimate",cond+"_lower_0.95",cond+"_upper_0.95"]]
            tmp.append(df)

            df=reduce(lambda df1,df2: pd.merge(df1,df2,on='time'), tmp)

            pa_={}
            for arg in ["Conf_Interval","show_censors","ci_legend","ci_force_lines", "left_axis", "right_axis" , "upper_axis", "lower_axis","tick_left_axis","tick_right_axis","tick_upper_axis","tick_lower_axis"]:
                if pa[arg] in ["off", ".off"]:
                    pa_[arg]=False
                else:
                    pa_[arg]=True

                if str(pa["markerc_write"]) != "":
                    pa_["marker_fc"]=pa["markerc_write"]
                else:
                    pa_["marker_fc"]=pa["markerc"]

                if str(pa["edgecolor_write"]) != "":
                    pa_["marker_ec"]=pa["edgecolor_write"]
                else:
                    pa_["marker_ec"]=pa["edgecolor"]

                if str(pa["grid_color_text"]) != "":
                    pa_["grid_color_write"]=pa["grid_color_text"]
                else:
                    pa_["grid_color_write"]=pa["grid_color_value"]

            pl=km.plot(show_censors=pa_["show_censors"], \
                censor_styles={"marker":marker_dict[pa["censor_marker_value"]], "markersize":float(pa["censor_marker_size_val"]), "markeredgecolor":pa_["marker_ec"], "markerfacecolor":pa_["marker_fc"], "alpha":float(pa["marker_alpha"])}, \
               ci_alpha=float(pa["ci_alpha"]), \
               ci_force_lines=pa_["ci_force_lines"], \
               ci_show=pa_["Conf_Interval"], \
               ci_legend=pa_["ci_legend"], \
               linestyle=pa["linestyle_value"], \
               linewidth=float(pa["linewidth"]))

            pl.spines['right'].set_visible(pa_["right_axis"])
            pl.spines['top'].set_visible(pa_["upper_axis"])
            pl.spines['left'].set_visible(pa_["left_axis"])
            pl.spines['bottom'].set_visible(pa_["lower_axis"])

            pl.spines['right'].set_linewidth(pa["axis_line_width"])
            pl.spines['left'].set_linewidth(pa["axis_line_width"])
            pl.spines['top'].set_linewidth(pa["axis_line_width"])
            pl.spines['bottom'].set_linewidth(pa["axis_line_width"])

            pl.tick_params(axis="both", direction=pa["ticks_direction_value"], length=float(pa["ticks_length"]))

            pl.tick_params(axis='x',which='both',bottom=pa_["tick_lower_axis"],top=pa_["tick_upper_axis"],labelbottom=pa_["lower_axis"], 
                           labelrotation=float(pa["xticks_rotation"]), labelsize=float(pa["xticks_fontsize"]))
       
            pl.tick_params(axis='y',which='both',left=pa_["tick_left_axis"],right=pa_["tick_right_axis"],labelleft=pa_["left_axis"], 
                           labelrotation=float(pa["yticks_rotation"]), labelsize=float(pa["yticks_fontsize"]))

            if str(pa["grid_value"]) != "None":
                pl.grid(True, which='both',axis=pa["grid_value"], color=pa_["grid_color_write"], linewidth=float(pa["grid_linewidth"]))

            if str(pa["x_lower_limit"]) != "" and str(pa["x_upper_limit"]) != "":       
                pl.set_xlim(float(pa["x_lower_limit"]),float(pa["x_upper_limit"]))
            if str(pa["y_lower_limit"]) != "" and str(pa["y_upper_limit"]) != "":  
                pl.set_ylim(float(pa["y_lower_limit"]),float(pa["y_upper_limit"]))    

            pl.set_title(pa["title"], fontdict={'fontsize':float(pa['titles'])})
            pl.set_xlabel(pa["xlabel"], fontdict={'fontsize':float(pa['xlabels'])})
            pl.set_ylabel(pa["ylabel"], fontdict={'fontsize':float(pa['ylabels'])})

        return df, pl

# ALLOWED_MARKERS=['circle', 'circle-open', 'circle-dot', 'circle-open-dot', 'square', 'square-open', 
# 'square-dot', 'square-open-dot', 'diamond', 'diamond-open', 'diamond-dot', 'diamond-open-dot', 
# 'cross', 'cross-open', 'cross-dot', 'cross-open-dot', 'x', 'x-open', 'x-dot', 'x-open-dot', 
# 'triangle-up', 'triangle-up-open', 'triangle-up-dot', 'triangle-up-open-dot', 'triangle-down', 
# 'triangle-down-open', 'triangle-down-dot', 'triangle-down-open-dot', 'triangle-left', 'triangle-left-open', 
# 'triangle-left-dot', 'triangle-left-open-dot', 'triangle-right', 'triangle-right-open', 'triangle-right-dot', 
# 'triangle-right-open-dot', 'triangle-ne', 'triangle-ne-open', 'triangle-ne-dot', 'triangle-ne-open-dot', 
# 'triangle-se', 'triangle-se-open', 'triangle-se-dot', 'triangle-se-open-dot', 'triangle-sw', 
# 'triangle-sw-open', 'triangle-sw-dot', 'triangle-sw-open-dot', 'triangle-nw', 'triangle-nw-open',
# 'triangle-nw-dot', 'triangle-nw-open-dot', 'pentagon', 'pentagon-open', 'pentagon-dot', 'pentagon-open-dot', 
# 'hexagon', 'hexagon-open', 'hexagon-dot', 'hexagon-open-dot', 'hexagon2', 'hexagon2-open', 'hexagon2-dot',
# 'hexagon2-open-dot', 'octagon', 'octagon-open', 'octagon-dot', 'octagon-open-dot', 'star', 'star-open', 
# 'star-dot', 'star-open-dot', 'hexagram', 'hexagram-open', 'hexagram-dot', 'hexagram-open-dot', 
# 'star-triangle-up', 'star-triangle-up-open', 'star-triangle-up-dot', 'star-triangle-up-open-dot', 
# 'star-triangle-down', 'star-triangle-down-open', 'star-triangle-down-dot', 'star-triangle-down-open-dot', 
# 'star-square', 'star-square-open', 'star-square-dot', 'star-square-open-dot', 'star-diamond', 
# 'star-diamond-open', 'star-diamond-dot', 'star-diamond-open-dot', 'diamond-tall', 'diamond-tall-open', 
# 'diamond-tall-dot', 'diamond-tall-open-dot', 'diamond-wide', 'diamond-wide-open', 'diamond-wide-dot', 
# 'diamond-wide-open-dot', 'hourglass', 'hourglass-open', 'bowtie', 'bowtie-open', 'circle-cross', 
# 'circle-cross-open', 'circle-x', 'circle-x-open', 'square-cross', 'square-cross-open', 'square-x', 
# 'square-x-open', 'diamond-cross', 'diamond-cross-open', 'diamond-x', 'diamond-x-open', 'cross-thin', 
# 'cross-thin-open', 'x-thin', 'x-thin-open', 'asterisk', 'asterisk-open', 'hash', 'hash-open', 
# 'hash-dot', 'hash-open-dot', 'y-up', 'y-up-open', 'y-down', 'y-down-open', 'y-left', 'y-left-open', 
# 'y-right', 'y-right-open', 'line-ew', 'line-ew-open', 'line-ns', 'line-ns-open', 'line-ne', 
# 'line-ne-open', 'line-nw', 'line-nw-open']
ALLOWED_MARKERS=['point','pixel','circle','triangle_down','triangle_up','triangle_left','triangle_right','tri_down','tri_up',
'tri_left','tri_right','square','pentagon','star','hexagon1','hexagon2','plus','x','diamond','thin_diamond','vline','hline']
STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
STANDARD_COLORS=["blue","green","red","cyan","magenta","yellow","black","white",None]
LINE_STYLES=["solid","dashed","dashdot","dotted"]
HIST_TYPES=['bar', 'barstacked', 'step',  'stepfilled']
STANDARD_ORIENTATIONS=['vertical','horizontal']
STANDARD_ALIGNMENTS=['left','right','mid']
TICKS_DIRECTIONS=["in","out", "inout"]
LEGEND_LOCATIONS=['best','upper right','upper left','lower left','lower right','right','center left','center right','lower center','upper center','center']
LEGEND_FONTSIZES=['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large']
MODES=["expand",None]


def figure_defaults():
    """Generates default figure arguments.

    Returns:
        dict: A dictionary of the style { "argument":"value"}
    """
    plot_arguments={
        "fig_width":"8.0",\
        "fig_height":"6.0",\
        "title":'Survival Analysis',\
        "title_size":STANDARD_SIZES,\
        "titles":"20",\
        "xcols":[],\
        "xvals":"",\
        "ycols":[],\
        "yvals":"",\
        "groups":["None"],\
        "groups_value":"",\
        "list_of_groups":[],\
        "Conf_Interval":".on",\
        "show_censors":".off",\
        "ci_legend":".off",\
        "ci_force_lines":".off",\
        "censor_marker":ALLOWED_MARKERS,\
        "censor_marker_value":"x",\
        "censor_marker_size":STANDARD_SIZES,\
        "censor_marker_size_val":"4",\
        "marker_color":STANDARD_COLORS,\
        "markerc":"black",\
        "markerc_write":"",\
        "ci_alpha":"0.3",\
        "colors":STANDARD_COLORS,\
        "linestyles":LINE_STYLES,\
        "linestyle_value":"solid",\
        "linewidth":"1.0",\
        "line_color":STANDARD_COLORS,\
        "line_color_value":"blue",\
        "edge_linewidths":STANDARD_SIZES,\
        "edge_linewidth":"0",\
        "edge_colors":STANDARD_COLORS,\
        "edgecolor":"black",\
        "edgecolor_write":"",\
        "marker_alpha":"1",\
        "xlabel":"x",\
        "xlabel_size":STANDARD_SIZES,\
        "xlabels":"14",\
        "ylabel":"y",\
        "ylabel_size":STANDARD_SIZES,\
        "ylabels":"14",\
        "axis_line_width":"1.0",\
        "left_axis":".on",\
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
        "download_format":["tsv","xlsx"],\
        "downloadf":"xlsx",\
        "download_fig_format":["png","pdf","svg"], \
        "download_fig":"pdf", \
        "downloadn":"LifeSpan",\
        "session_downloadn":"MySession.LifeSpan",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.LifeSpan",\
        "inputargumentsfile":"Select file.."}

    return plot_arguments