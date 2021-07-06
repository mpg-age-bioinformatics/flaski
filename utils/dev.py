from flaski.apps.routes import igseaplot
 
EXTERNAL_APPS=[{ "name":"iGSEA plot", "id":'igseaplot_more',"link":'igseaplot' ,"java":"javascript:ReverseDisplay('igseaplot_more')", "description":"An app to customize GSEA plots."}]

from flaski.apps.main.igseaplot import figure_defaults as igseaplot_def
EXT_DEFAULTS_DIC={"igseaplot":igseaplot_def}
