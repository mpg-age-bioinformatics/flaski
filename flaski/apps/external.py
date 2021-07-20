###########################################################################
#
# example of Apps imported as plugin through docker-compose.yml mapping
#
# external.py (this file):
#
# from flaski.apps.routes import histogram
# EXTERNAL_APPS=[{ "name":"Histogram", "id":'histogram_more',"link":'histogram' ,"java":"javascript:ReverseDisplay('histogram_more')", "description":"A histogram."}]
#
# from flaski.apps.main.histogram import figure_defaults as histogram_def
# EXT_DEFAULTS_DIC={"histogram":histogram_def}
#
# docker-compose.yml:
#   volumes:
#    - ~/histogram/route.py:/flaski/flaski/apps/routes/histogram.py
#    - ~/histogram/main.py:/flaski/flaski/apps/main/histogram.py
#    - ~/histogram/external.py:/flaski/flaski/apps/external.py
#
###########################################################################
# from flaski.apps.routes import igseaplot
 
# EXTERNAL_APPS=[{ "name":"iGSEA plot", "id":'igseaplot_more',"link":'igseaplot' ,"java":"javascript:ReverseDisplay('igseaplot_more')", "description":"An app to customize GSEA plots."}]

# from flaski.apps.main.igseaplot import figure_defaults as igseaplot_def
# EXT_DEFAULTS_DIC={"igseaplot":igseaplot_def}

# docker-compose.yml:
#     volumes:
#         - ~/histogram/route.py:/flaski/flaski/apps/routes/igseaplot.py
#         - ~/histogram/main.py:/flaski/flaski/apps/main/igseaplot.py
#         - ~/histogram/external.py:/flaski/flaski/apps/igseaplot.py

EXTERNAL_APPS=[]
EXT_DEFAULTS_DIC={}