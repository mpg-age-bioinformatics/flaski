from flaski.apps.dash import dashapp

EXTERNAL_APPS=[ { "name":"Dash demo plot", 
                "id":'dashapp_more',
                "link":'dashapp' ,
                "java":"javascript:ReverseDisplay('dashapp_more')", 
                "description":"A demo App for Flaski-Dash integration"},
                { "name":"Data lake", 
                "id":'aadatalake_more',
                "link":'aadatalake' ,
                "java":"javascript:ReverseDisplay('aadatalake_more')", 
                "description":"An RNAseq data lake"}  ]
                
EXT_DEFAULTS_DIC={}
