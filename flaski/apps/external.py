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
# ext_defaults_dic={"histogram":histogram_def}
#
# docker-compose.yml:
#   volumes:
#    - ~/histogram/route.py:/flaski/flaski/apps/routes/histogram.py
#    - ~/histogram/main.py:/flaski/flaski/apps/main/histogram.py
#    - ~/histogram/external.py:/flaski/flaski/apps/external.py
#
###########################################################################
EXTERNAL_APPS=[]
EXT_DEFAULTS_DIC={}