# from flaski.apps.dash import dashapp, rnaseq, asplicing, intronret, circrna, \
#     mirna,sixteens ,irfinder, chip, atac, varcal, , gsea, riboseq
from flaski.apps.dash import motifenr, dashapp

EXTERNAL_APPS=[ {"name":"Motif enrichment analysis", 
        "id":'motifenr_more',
        "link":'motifenr' ,
        "java":"javascript:ReverseDisplay('motifenr_more')", 
        "description":"Motif enrichment analysis submission form.", "submission":"yes"},\
        { "name":"Dash demo plot", 
        "id":'dashapp_more',
        "link":'dashapp' ,
        "java":"javascript:ReverseDisplay('dashapp_more')", 
        "description":"A demo App for Flaski-Dash integration"},\
        { "name":"Methylation Clock", 
        "id":'methylclock_more',
        "link":'methylclock' ,
        "java":"javascript:ReverseDisplay('methylclock_more')", 
        "description":"Methylation clock submission form.", "submission":"yes"},\
         { "name":"Data Lake", 
        "id":'aadatalake_more',
        "link":'aadatalake' ,
        "java":"javascript:ReverseDisplay('aadatalake_more')", 
        "description":"An RNAseq data lake."}
        ]
                
EXT_DEFAULTS_DIC={}
