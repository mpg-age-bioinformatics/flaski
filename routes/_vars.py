import os

_PRIVATE_ROUTES=['aadatalake', 'alphafold', 'rnaseq', "atacseq", "chipseq", "asplicing", "intronret", "irfinder", "circrna", "mirna", "sixteens", "varcal", "riboseq", "methylclock"]
_PUBLIC_VIEWS=['alphafold', 'rnaseq', "atacseq", "chipseq", "asplicing", "intronret", "irfinder", "circrna", "mirna", "sixteens", "varcal", "riboseq", "methylclock"]

if os.environ['FLASK_ENV'] != "development" :
    _DEV_ROUTES=[ "lifespan" ] 
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
                "3D Scatter plot":"/threeDscatterplot/",\
                "Line plot":"/lineplot/",\
                "Histogram":"/histogram/",\
                "Heatmap":"/heatmap/",\
                "Violin plot":"/violinplot/",\
                "Circular bar plot":"/circularbarplots/",\
                "Dendrogram":"/dendrogram/",\
                "Venn diagram":"/venndiagram/",\
                "GSEA plot":"/gseaplot/",\
                "DAVID":"/david/",\
                "Cell plot":"/cellplot/",\
                "KEGG":"/kegg/",\
                "PCA":"/pca/",\
                "MDS":"/mds/",\
                "tSNE":"/tsne/",\
                "Lifespan":"/lifespan/",\
                "Datalake":"/aadatalake/" 
            }, \

    }, \
    { "Forms": \
            {
                "RNAseq":"/rnaseq/",\
                "ATACseq":"/atacseq/",\
                "ChIPseq":"/chipseq/",\
                "Alternative Splicing":"/asplicing/",\
                "Intron Retention":"/intronret/",\
                "IRfinder":"/irfinder/",\
                "Circular RNA":"/circrna/",\
                "miRNA":"/mirna/",\
                "16S":"/sixteens/",\
                "Variant Calling":"/varcal/",\
                "Ribo-Seq":"/riboseq/",\
                "AlphaFold":"/alphafold/",\
                "Methylation Clock":"/methylclock/",\
            } \
    }
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
#     }, \
#     { \
#         "Eg. DropDown 2": \
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
#     }
# ]
###################################