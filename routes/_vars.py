import os

_PRIVATE_ROUTES=['alphafold', 'rnaseq', "atacseq", "chipseq", "asplicing", "intronret", "irfinder", "circrna", "mirna", "sixteens", "varcal", "riboseq","gsea",'aadatalake', "methylclock", "crispr"]
_PUBLIC_VIEWS=['alphafold', 'rnaseq', "atacseq", "chipseq", "asplicing", "intronret", "irfinder", "circrna", "mirna", "sixteens", "varcal", "riboseq","gsea"]

if os.environ['FLASK_ENV'] != "development" :
    _DEV_ROUTES=[  ] 
    _PRIVATE_ROUTES = _PRIVATE_ROUTES + _DEV_ROUTES

_META_TAGS=[{'property':'og:title', 'content':'Flaski' },\
{'property':'og:image', 'content':'https://i.ibb.co/9pJr1cb/dog-solid.png' },\
{'property':'og:description', 'content':'A collection of web apps for life sciences.' },\
{'property':'og:url', 'content':'https://flaski.age.mpg.de' },\
{'property':'og:image:width', 'content':'512' },\
{'property':'og:image:height', 'content':'481' },\
{'property':'og:type', 'content':'website' }]

user_navbar_links={
    "Home":"/home/",\
    "Storage":"/storage/",\
    "separator_1":"-",\
    "General":"__title__",\
    "About":"/about/",\
    "Impressum":"/impressum/",\
    "Privacy":"/privacy/",\
    "Issues":"https://github.com/mpg-age-bioinformatics/flaski/issues",\
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
                "t-SNE":"/tsne/",\
                "Lifespan":"/lifespan/",\
                "Datalake":"/aadatalake/",\
                "Version check":"/vcheck/",\
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
                "GSEA":"/gsea/",\
                "CRISPR" : "/crispr/"
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