# from flaski.apps.dash import dashapp, rnaseq, asplicing, intronret, circrna, \
#     mirna,sixteens ,irfinder, chip, atac, varcal, , gsea, riboseq
from flaski.apps.dash import motifenr
EXTERNAL_APPS=[ {"name":"Motif enrichment analysis", 
        "id":'motifenr_more',
        "link":'motifenr' ,
        "java":"javascript:ReverseDisplay('motifenr_more')", 
        "description":"Motif enrichment analysis submission form.", "submission":"yes"}]
                
EXT_DEFAULTS_DIC={}
