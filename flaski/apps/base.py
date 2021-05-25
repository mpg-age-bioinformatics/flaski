from flaski.apps.routes import scatterplot, iscatterplot, heatmap, iheatmap, venndiagram, icellplot, david, aarnaseqlake, pca, histogram, violinplot, iviolinplot, mds, tsne, kegg, ihistogram, lifespan, submissions, circularbarplots
from flaski.apps.external import *

FREEAPPS=[{ "name":"Scatter plot","id":'scatterplot_more', "link":'scatterplot' , "java":"javascript:ReverseDisplay('scatterplot_more')", "description":"A static scatterplot app." },\
        { "name":"iScatter plot", "id":'iscatterplot_more',"link":'iscatterplot' ,"java":"javascript:ReverseDisplay('iscatterplot_more')", "description":"An intreactive scatterplot app."},\
        { "name":"Heatmap", "id":'heatmap_more',"link":'heatmap' ,"java":"javascript:ReverseDisplay('heatmap_more')", "description":"An heatmap plotting app."},\
        { "name":"iHeatmap", "id":'iheatmap_more',"link":'iheatmap' ,"java":"javascript:ReverseDisplay('iheatmap_more')", "description":"An interactive heatmap plotting app."},\
        { "name":"Venn diagram", "id":'venndiagram_more',"link":'venndiagram' ,"java":"javascript:ReverseDisplay('venndiagram_more')", "description":"A venn diagram plotting app."},\
        { "name":"DAVID", "id":'david_more',"link":'david' ,"java":"javascript:ReverseDisplay('david_more')", "description":"A DAVID querying plot."},\
        { "name":"iCell plot", "id":'icellplot_more',"link":'icellplot' ,"java":"javascript:ReverseDisplay('icellplot_more')", "description":"A DAVID reporting plot."},\
        { "name":"PCA", "id":'pca_more',"link":'pca' ,"java":"javascript:ReverseDisplay('pca_more')", "description":"A PCA app."},\
        { "name":"MDS", "id":'mds_more',"link":'mds' ,"java":"javascript:ReverseDisplay('mds_more')", "description":"A MultiDimensional Scaling app."},\
        { "name":"tSNE", "id":'tsne_more',"link":'tsne' ,"java":"javascript:ReverseDisplay('tsne_more')", "description":"A tSNE app."},\
        { "name":"Histogram", "id":'histogram_more',"link":'histogram' ,"java":"javascript:ReverseDisplay('histogram_more')", "description":"A histogram."},\
        { "name":"iHistogram", "id":'ihistogram_more',"link":'ihistogram' ,"java":"javascript:ReverseDisplay('iHistogram_more')", "description":"An interactive Histogram app."},\
        { "name":"Violin plot", "id":'violinplot_more',"link":'violinplot' ,"java":"javascript:ReverseDisplay('violinplot_more')", "description":"A Violin plot app. including box and swarm plots."},\
        { "name":"iViolin plot", "id":'iviolinplot_more',"link":'iviolinplot' ,"java":"javascript:ReverseDisplay('iviolinplot_more')", "description":"An interactive violin plot including box and swarm plots."},\
        { "name":"KEGG", "id":'kegg_more',"link":'kegg' ,"java":"javascript:ReverseDisplay('kegg_more')", "description":"A KEGG mapping and plotting app."} ,\
        { "name":"Life Span", "id":'lifespan_more',"link":'lifespan' ,"java":"javascript:ReverseDisplay('lifespan_more')", "description":"A Survival Analysis app."},\
        { "name":"Circular bars plot", "id":'circularbarplots_more',"link":'circularbarplots' ,"java":"javascript:ReverseDisplay('circularbarplots_more')", "description":"A Circular bars plot app."}]  #,\

FREEAPPS=FREEAPPS+EXTERNAL_APPS