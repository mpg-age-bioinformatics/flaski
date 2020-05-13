import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pylab as plt
from matplotlib_venn import venn2, venn3, venn2_circles, venn3_circles
import sys
matplotlib.use('agg')

def GET_COLOR(x):
    if str(x)[:3].lower() == "rgb":
        vals=x.split("rgb(")[-1].split(")")[0].split(",")
        vals=[ float(s.strip(" ")) for s in vals ]
        #vals=tuple(vals)
        return vals
    else:
        return str(x)


def make_figure(pa):

    #fig=plt.figure(figsize=(float(pa["fig_width"]),float(pa["fig_height"])))
    fig, axes = plt.subplots(1, 1,figsize=(float(pa["fig_width"]),float(pa["fig_height"])))


    pa_={}
    sets={}

    for set_index in ["set1","set2","set3"]:

        if pa["%s_values" %set_index] != "":
            set_values=pa["%s_values" %set_index].split("\n")
            set_values=[ s.rstrip("\r") for s in set_values ]
            set_values=[ s for s in set_values if s != "" ]
            sets[set_index]=set(set_values)

        if pa[ "%s_color_rgb" %set_index] != "":
            pa_["%s_color_value" %set_index ] = GET_COLOR( pa[ "%s_color_rgb" %set_index ] )
        else:
            pa_["%s_color_value" %set_index ] = pa["%s_color_value" %set_index ]

        if pa[ "%s_line_rgb" %set_index] != "":
            pa_["%s_line_color" %set_index ] = GET_COLOR( pa[ "%s_line_rgb" %set_index ] )
        else:
            pa_["%s_line_color" %set_index ] = pa["%s_line_color" %set_index ]


    if len( list(sets.keys()) ) == 2:
        set1=list(sets.keys())[0]
        set2=list(sets.keys())[1]
        venn2( [ sets[set1], sets[set2] ], \
                ( pa[ "%s_name" %(set1)], pa[ "%s_name" %(set2) ] ), \
                set_colors=( pa_[ "%s_color_value" %(set1)], pa_[ "%s_color_value" %(set2) ]),\
                alpha=float( pa["fill_alpha"] ),\
                ax=axes)
        venn=venn2_circles( [ sets[set1], sets[set2] ], alpha=0.5, linestyle="dashed", linewidth=1, color="black",ax=axes)

        venn[0].set_lw( float(pa[ "%s_linewidth" %(set1) ]))
        venn[1].set_lw( float(pa[ "%s_linewidth" %(set2) ]))

        venn[0].set_linestyle(pa[ "%s_linestyle_value" %(set1)])
        venn[1].set_linestyle(pa[ "%s_linestyle_value" %(set2)])

        venn[0].set_alpha(float(pa[ "%s_line_alpha" %(set1)]))
        venn[1].set_alpha(float(pa[ "%s_line_alpha" %(set2)]))

        venn[0].set_color(pa_[ "%s_line_color" %(set1)])
        venn[1].set_color(pa_[ "%s_line_color" %(set2)])


    elif len( list(sets.keys()) ) == 3:
        set1=list(sets.keys())[0]
        set2=list(sets.keys())[1]
        set3=list(sets.keys())[2]
        venn3( [ sets[set1], sets[set2], sets[set3]  ], \
                ( pa[ "%s_name" %(set1)], pa[ "%s_name" %(set2)], pa[ "%s_name" %(set3) ]),\
                set_colors=( pa_[ "%s_color_value" %(set1)], pa_[ "%s_color_value" %(set2)], pa_[ "%s_color_value" %(set3) ]),\
                alpha=float( pa["fill_alpha"] ))
        venn=venn3_circles( [ sets[set1], sets[set2], sets[set3] ], \
                        alpha=0.5, \
                        linestyle="dashed", \
                        linewidth=1, \
                        color="k")

        venn[0].set_lw( float(pa[ "%s_linewidth" %(set1)] ) ) 
        venn[1].set_lw( float(pa[ "%s_linewidth" %(set2)] ) )
        venn[2].set_lw( float(pa[ "%s_linewidth" %(set3)] ) )

        venn[0].set_linestyle(pa[ "%s_linestyle_value" %(set1)])
        venn[1].set_linestyle(pa[ "%s_linestyle_value" %(set2)])
        venn[2].set_linestyle(pa[ "%s_linestyle_value" %(set2)])

        venn[0].set_alpha( float(pa[ "%s_line_alpha" %(set1)]))
        venn[1].set_alpha( float(pa[ "%s_line_alpha" %(set2)]))
        venn[2].set_alpha( float(pa[ "%s_line_alpha" %(set3)]))

        venn[0].set_color(pa_[ "%s_line_color" %(set1)])
        venn[1].set_color(pa_[ "%s_line_color" %(set2)])
        venn[2].set_color(pa_[ "%s_line_color" %(set3)])   

    all_values=[]
    for set_index in list( sets.keys() ):
        all_values=all_values+ list(sets[set_index])
    df=pd.DataFrame(index=list(set(all_values)))
    for set_index in list( sets.keys() ):
        tmp=pd.DataFrame( { pa[ "%s_name" %(set_index)]:list(sets[set_index]) } ,index=list(sets[set_index]) )
        df=pd.merge(df,tmp,how="left",left_index=True, right_index=True)

    plt.title(pa["title"], fontsize=float(pa["title_size_value"]))

    if pa["population_size"]!="":
        pvalues={}
        from scipy.stats import hypergeom
        def hypergeomtest(set_1,set_2):
            M=float(pa["population_size"]) # total number of geness
            n=len(sets[set_1]) # genes in group I
            N=len(sets[set_2]) # genes in group II
            x=len( [ s for s in list(sets[set_1]) if s in list(sets[set_2]) ] ) # intersect
            p=hypergeom.sf(x-1, M,n,N)
            return p, M, n, N, x
        p, M, n, N, x = hypergeomtest("set1","set2")
        pvalues["%s vs. %s" %(pa["set1_name"],pa["set2_name"])]={"n %s" %pa["set1_name"]:n,"n %s" %pa["set2_name"]:N,"common":x,"total":M,"p value":str(p)}

        if len( list(sets.keys()) ) == 3:
            p, M, n, N, x=hypergeomtest("set1","set3")
            pvalues["%s vs. %s" %(pa["set1_name"],pa["set3_name"])]={"n %s" %pa["set1_name"]:n,"n %s" %pa["set3_name"]:N,"common":x,"total":M,"p value":str(p)}

            p, M, n, N, x=hypergeomtest("set2","set3")
            pvalues["%s vs. %s" %(pa["set2_name"],pa["set3_name"])]={"n %s" %pa["set2_name"]:n,"n %s" %pa["set3_name"]:N,"common":x,"total":M,"p value":str(p)}

    else:
        pvalues=None

    return fig, df, pvalues

STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
STANDARD_COLORS=["blue","green","red","cyan","magenta","yellow","black","white"]
LINE_STYLES=["solid","dashed","dashdot","dotted","None"]

def figure_defaults():
    plot_arguments={
        "fig_width":"6.0",\
        "fig_height":"6.0",\
        "title":'Venn diagram',\
        "title_size":STANDARD_SIZES,\
        "title_size_value":"20",\
        "set1_name":"set1",\
        "set2_name":"set2",\
        "set3_name":"set3",\
        "set1_values":"",\
        "set2_values":"",\
        "set3_values":"",\
        "colors":STANDARD_COLORS,\
        "set1_color_value":"red",\
        "set2_color_value":"blue",\
        "set3_color_value":"green",\
        "set1_color_rgb":"",\
        "set2_color_rgb":"",\
        "set3_color_rgb":"",\
        "fill_alpha":"0.5",\
        "set1_linewidth":"0.2",\
        "set2_linewidth":"0.2",\
        "set3_linewidth":"0.2",\
        "linestyles":LINE_STYLES,\
        "set1_linestyle_value":"",\
        "set2_linestyle_value":"",\
        "set3_linestyle_value":"",\
        "set1_line_alpha":"0.8",\
        "set2_line_alpha":"0.8",\
        "set3_line_alpha":"0.8",\
        "set1_line_color":"red",\
        "set2_line_color":"blue",\
        "set3_line_color":"green",\
        "set1_line_rgb":"",\
        "set2_line_rgb":"",\
        "set3_line_rgb":"",\
        "population_size":"",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"scatterplot",\
        "session_downloadn":"MySession.scatter.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.scatter.plot",\
        "inputargumentsfile":"Select file.."
    }
    # grid colors not implemented in UI


    checkboxes=[]

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