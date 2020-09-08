from flaski.apps.routes import ihistogram, lifespan, idendrogram, kegg

EXTERNAL_APPS=[{ "name":"iHistogram", "id":'ihistogram_more',"link":'ihistogram' ,"java":"javascript:ReverseDisplay('iHistogram_more')", "description":"An interactive Histogram app."},\
            { "name":"LifeSpan", "id":'lifespan_more',"link":'lifespan' ,"java":"javascript:ReverseDisplay('lifespan_more')", "description":"A Survival Analysis app."},\
            { "name":"iDendrogram", "id":'idendrogram_more',"link":'idendrogram' ,"java":"javascript:ReverseDisplay('idendrogram_more')", "description":"An interactive Dendrogram app."},\
            {"name":"KEGG", "id":'kegg_more',"link":'kegg' ,"java":"javascript:ReverseDisplay('kegg_more')", "description":"A KEGG mapping and plotting app."}] #,\ #,\