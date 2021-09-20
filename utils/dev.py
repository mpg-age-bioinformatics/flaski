from flaski.apps.dash import dashapp, rnaseq

EXTERNAL_APPS=[ { "name":"Dash demo plot", 
                "id":'dashapp_more',
                "link":'dashapp' ,
                "java":"javascript:ReverseDisplay('dashapp_more')", 
                "description":"A demo App for Flaski-Dash integration"},
                { "name":"RNAseq submisssion", 
                "id":'rnaseq_more',
                "link":'rnaseq' ,
                "java":"javascript:ReverseDisplay('rnaseq_more')", 
                "description":"RNAseq submission form."} ]
                
EXT_DEFAULTS_DIC={}
