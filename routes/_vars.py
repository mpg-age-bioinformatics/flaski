import os

_PRIVATE_ROUTES=['alphafold', 'rnaseq', "atacseq", "chipseq", "cutandtag", "asplicing", "intronret", "irfinder", "circrna", "mirna", "sixteens", "varcal", "riboseq","gsea", "aadatalake", "aadatalake_prot", "methylclock", "crispr", "chatbot", "plotai", "neanderthalage", "protclock"]
_PUBLIC_VIEWS = ['alphafold', 'rnaseq', "atacseq", "chipseq", "cutandtag", "asplicing", "intronret", "irfinder", "circrna", "mirna", "sixteens", "varcal", "riboseq","gsea"] #, "cbioportal"]

if os.environ['FLASK_ENV'] != "development" :
    _DEV_ROUTES=[  "agebot" ]  #"cbioportal",
    _PRIVATE_ROUTES = _PRIVATE_ROUTES + _DEV_ROUTES

_META_TAGS=[{'name':'title', 'property':'og:title', 'content':'flaski' },\
{'name':'image','property':'og:image', 'content':'https://i.ibb.co/pRL0sM1/Flaski.jpg' },\
{'name':'description','property':'og:description', 'content':'Flaski is a myapp-based suite of web applications for data analysis and visualization in the life sciences, \
featuring built-in session management and versioning. It is designed to support seamless collaboration between users with and without programming experience: sessions \
created through the web interface can be opened in Python as standard Plotly objects—and vice versa. \
Flaski also streamlines troubleshooting: its error-reporting tools include a session-sharing option that enables fast and effective first-level support. \
Flaski is open-source and released under the MIT License.' },\
{'property':'og:url', 'content':os.getenv("APP_URL") },\
{'property':'og:image:width', 'content':'1200' },\
{'property':'og:image:height', 'content':'675' },\
{'property':'og:type', 'content':'website' }]


user_navbar_links={
    "Home":"/home/",\
    "Storage":"/storage/",\
    "separator_1":"-",\
    "General":"__title__",\
    "About":"/about/",\
    "Tutorials":"/ext/www.youtube.com/channel/UCQCHNHJ23FGyXo9usEC_TbA",\
    "Impressum":"/impressum/",\
    "Privacy":"/privacy/",\
    "Issues":"/ext/github.com/mpg-age-bioinformatics/flaski/issues",\
    "fixed_separator":"-",\
    "Configuration":"__title__", \
    "Settings":"/settings/",\
    "fixed_separator_2":"-",\
    "Logout":"/logout/"
}

# "KEGG":"/kegg/",\

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
                "PCA":"/pca/",\
                "MDS":"/mds/",\
                "t-SNE":"/tsne/",\
                "Lifespan":"/lifespan/",\
                "Datalake":"/aadatalake/",\
                "Datalake Proteomics":"/aadatalake_prot/",\
                "cBioPortal":"/cbioportal/",\
                "GTEx":"/gtex/",\
                # "AGE bot":"/agebot/",\
                "Neanderthal age":"/neanderthalage/",\
                "Proteomics Clock":"/protclock/",\
                "KEGG":"/kegg/",\
                "Chatbot AGE":"/chatbot/",\
                "Plot AI":"/plotai/",\
                "Version check":"/vcheck/",\
            }, \

    }, \
    { "Forms": \
            {
                "RNAseq":"/rnaseq/",\
                "ATACseq":"/atacseq/",\
                "ChIPseq":"/chipseq/",\
                "CutNTag":"/cutandtag/",\
                "Alternative Splicing":"/asplicing/",\
                "Intron Retention":"/intronret/",\
                "IRfinder":"/irfinder/",\
                "Circular RNA":"/circrna/",\
                "miRNA":"/mirna/",\
                "16S":"/sixteens/",\
                "Variant Calling":"/varcal/",\
                "Ribo-Seq":"/riboseq/",\
                "AlphaFold 3":"/alphafold/",\
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
