#from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib


matplotlib.use('agg')

def make_figure(df,pa):
    x=df[pa["xvals"]].tolist()
    y=df[pa["yvals"]].tolist()

    # MAIN FIGURE
    #fig = Figure()
    fig=plt.figure(figsize=(6,6))
    plt.scatter(x, y, \
        marker=pa["marker"], \
        s=int(pa["markers"]),\
        c=pa["markerc"])

    plt.title(pa['title'], fontsize=int(pa["titles"]))
    plt.xlabel(pa["xlabel"], fontsize=int(pa["xlabels"]))
    plt.ylabel(pa["ylabel"], fontsize=int(pa["ylabels"]))

    return fig

STANDARD_SIZES=[ str(i) for i in list(range(101)) ]
ALLOWED_MARKERS=[".",",","o","v","^","<",">",\
            "1","2","3","4","8",\
            "s","p","*","h","H","+","x",\
            "X","D","d","|","_"]


def figure_defaults():
    
    # https://matplotlib.org/3.1.1/api/markers_api.html
    # https://matplotlib.org/2.0.2/api/colors_api.html

   

    markers_i

    # lists allways need to have thee default value after the list
    # eg.:
    # "title_size":standard_sizes,\
    # "titles":"20"

    plot_arguments={
        "title":'Scatter plot',\
        "title_size":STANDARD_SIZES,\
        "titles":"20",\
        "xcols":[],\
        "xvals":None,\
        "ycols":[],\
        "yvals":None,\
        "markerstyles":ALLOWED_MARKERS,\
        "marker":".",\
        "marker_size":STANDARD_SIZES,\
        "markers":"50",\
        "marker_color":["blue","green","red","cyan","magenta","yellow","black","white"],\
        "markerc":"black",\
        "xlabel":"x",\
        "xlabel_size":STANDARD_SIZES,\
        "xlabels":"14",\
        "ylabel":"y",\
        "ylabel_size":STANDARD_SIZES,\
        "ylabels":"14",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"scatterplot",\
        "session_downloadn":"MySession.scatter.plot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.scatter.plot",\
        "inputargumentsfile":"Select file.."
    }
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

    return plot_arguments, lists, notUpdateList

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

    

    

    
    

        

            


