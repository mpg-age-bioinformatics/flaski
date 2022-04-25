import os

_PRIVATE_ROUTES=[]
_PUBLIC_VIEWS=[]

if os.environ['FLASK_ENV'] != "development" :
    _DEV_ROUTES=[ "heatmap", "circularbarplots","gseaplot","venndiagram", "dendrogram", "threeDscatterplot"]
    _PRIVATE_ROUTES = _PRIVATE_ROUTES + _DEV_ROUTES

user_navbar_links={
    "Home":"/home/",\
    "Storage":"/storage/",\
    "separator_1":"-",\
    "General":"__title__",\
    "About":"/about/",\
    "Impressum":"/impressum/",\
    "Privacy":"/privacy/",\
    "fixed_separator":"-",\
    "Configuration":"__title__", \
    "Settings":"/settings/",\
    "fixed_separator_2":"-",\
    "Logout":"/logout/"
}

other_nav_dropdowns =[ 
    { \
        "Apps": \
            {
                "Scatter plot":"/scatterplot/",\
                "Line plot":"/lineplot/",\
                "Heatmap":"/heatmap/",\
                "Violin plot":"/violinplot/",\
                #"Venndiagram":"/venndiagram/",\
                "Cell plot":"/cellplot/",\
                "GSEA plot":"/gseaplot/",\
                "DAVID":"/david/",\
                "Circular bar plot":"/circularbarplots/",\
                "Dendrogram":"/dendrogram/",\
                "3D Scatter plot":"/threeDscatterplot/",\

            } \
    } \
]
###################################
# _PRIVATE_ROUTES=['home'] ## only users added to this route on the admin board / User model will have access
# _PUBLIC_VIEWS=[] ## can be used to set specific rights within the app eg. deactiva Submit buttons.
# other_nav_dropdowns =[ 
#     { \
#         "Eg. DropDown": \
#             {
#                 "Home":"/home/",\
#                 "separator_1":"-",\
#                 "General":"__title__",\
#                 "About":"/about/",\
#                 "Impressum":"/impressum/",\
#                 "Privacy":"/privacy/",\
#                 "fixed_separator":"-",\
#                 "Configuration":"__title__", \
#                 "Settings":"/settings/",\
#                 "Logout":"/logout/"
#             } \
#     } \
# ]
###################################