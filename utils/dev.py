from flaski.apps.dash import dashapp, rnaseq, asplicing, intronret, circrna, mirna,sixteens ,irfinder, chip, atac, varcal

EXTERNAL_APPS=[ { "name":"Dash demo plot", 
                "id":'dashapp_more',
                "link":'dashapp' ,
                "java":"javascript:ReverseDisplay('dashapp_more')", 
                "description":"A demo App for Flaski-Dash integration"},
                { "name":"RNAseq submission", 
                "id":'rnaseq_more',
                "link":'rnaseq' ,
                "java":"javascript:ReverseDisplay('rnaseq_more')", 
                "description":"RNAseq submission form."},
                { "name":"Alternative splicing submission", 
                "id":'asplicing_more',
                "link":'asplicing' ,
                "java":"javascript:ReverseDisplay('asplicing_more')", 
                "description":"Alt. splicing submission form."},
                { "name":"Intron retention submission", 
                "id":'intronret_more',
                "link":'intronret' ,
                "java":"javascript:ReverseDisplay('intronret_more')", 
                "description":"Intron retention submission form."} ,
                { "name":"Circular RNA submission", 
                "id":'circrna_more',
                "link":'circrna' ,
                "java":"javascript:ReverseDisplay('circrna_more')", 
                "description":"Circular RNA submission form."} ,
                { "name":"miRNA submission", 
                "id":'mirna_more',
                "link":'mirna' ,
                "java":"javascript:ReverseDisplay('mirna_more')", 
                "description":"miRNA submission form."} ,
                { "name":"16S submission", 
                "id":'sixteens_more',
                "link":'sixteens' ,
                "java":"javascript:ReverseDisplay('sixteens_more')", 
                "description":"16S submission form."},
                { "name":"IRfinder submission", 
                "id":'irfinder_more',
                "link":'irfinder' ,
                "java":"javascript:ReverseDisplay('irfinder_more')", 
                "description":"IRfinder submission form."},
                { "name":"ChIP submission", 
                "id":'chip_more',
                "link":'chip' ,
                "java":"javascript:ReverseDisplay('chip_more')", 
                "description":"ChIP submission form."},
                { "name":"ATACseq submission", 
                "id":'atac_more',
                "link":'atac' ,
                "java":"javascript:ReverseDisplay('atac_more')", 
                "description":"ATACseq submission form."},
                { "name":"Variant calling submission", 
                "id":'varcal_more',
                "link":'varcal' ,
                "java":"javascript:ReverseDisplay('varcal_more')", 
                "description":"Variant calling submission form."} ]
                
EXT_DEFAULTS_DIC={}
