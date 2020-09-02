###########################################################################
#
# example of Apps imported as plugin through docker-compose.yml mapping
#
# external.py (this file):
# from flaski.apps.routes import histogram
# EXTERNAL_APPS=[{ "name":"Histogram", "id":'histogram_more',"link":'histogram' ,"java":"javascript:ReverseDisplay('histogram_more')", "description":"A histogram."}]
#
# docker-compose.yml:
#   volumes:
#    - ~/histogram/route.py:/flaski/flaski/apps/routes/histogram.py
#    - ~/histogram/main.py:/flaski/flaski/apps/main/histogram.py
#    - ~/histogram/external.py:/flaski/flaski/apps/external.py
#
###########################################################################
EXTERNAL_APPS=[]