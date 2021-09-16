from flaski.apps.routes import scatterplot, iscatterplot, heatmap, iheatmap, venndiagram, icellplot, david, aarnaseqlake, pca, histogram, violinplot, iviolinplot
from flaski.apps.routes import mds, tsne, kegg, ihistogram, lifespan, submissions, circularbarplots, threeDscatterplot, igseaplot
from flaski.apps.dash import aadatalake

from flaski.apps.external import *

FREEAPPS=[{ "name":"Scatter plot","id":'scatterplot_more', "link":'scatterplot' , "java":"javascript:ReverseDisplay('scatterplot_more')", "description":"A static scatterplot app." },\
        { "name":"iScatter plot", "id":'iscatterplot_more',"link":'iscatterplot' ,"java":"javascript:ReverseDisplay('iscatterplot_more')", "description":"An intreactive scatterplot app."},\
        { "name":"3D iscatter plot", "id":'threeDscatterplot_more',"link":'threeDscatterplot' ,"java":"javascript:ReverseDisplay('threeDscatterplot_more')", "description":"A 3D interactive scatter plot app."},\
        { "name":"Heatmap", "id":'heatmap_more',"link":'heatmap' ,"java":"javascript:ReverseDisplay('heatmap_more')", "description":"An heatmap plotting app."},\
        { "name":"iHeatmap", "id":'iheatmap_more',"link":'iheatmap' ,"java":"javascript:ReverseDisplay('iheatmap_more')", "description":"An interactive heatmap plotting app."},\
        { "name":"iDendrogram", "id":'idendrogram_more',"link":'idendrogram' ,"java":"javascript:ReverseDisplay('idendrogram_more')", "description":"An interactive Dendrogram app."},\
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
        { "name":"Circular bars plot", "id":'circularbarplots_more',"link":'circularbarplots' ,"java":"javascript:ReverseDisplay('circularbarplots_more')", "description":"A Circular bars plot app."},\
        { "name":"iGSEA plot", "id":'igseaplot_more',"link":'igseaplot' ,"java":"javascript:ReverseDisplay('igseaplot_more')", "description":"An app to customize GSEA plots."} ]

FREEAPPS=FREEAPPS+EXTERNAL_APPS


# this next sections is required to ensure that session from old App version can be loaded into new App versions

from flaski.apps.main.threeDscatterplot import figure_defaults as threeDscatterplot_def
from flaski.apps.main.circularbarplots import figure_defaults as circularbarplots_def
from flaski.apps.main.david import figure_defaults as david_def
from flaski.apps.main.heatmap import figure_defaults as heatmap_def
from flaski.apps.main.histogram import figure_defaults as histogram_def
from flaski.apps.main.icellplot import figure_defaults as icellplot_def
from flaski.apps.main.idendrogram import figure_defaults as idendrogram_def
from flaski.apps.main.iheatmap import figure_defaults as iheatmap_def
from flaski.apps.main.ihistogram import figure_defaults as ihistogram_def
from flaski.apps.main.iscatterplot import figure_defaults as iscatterplot_def
from flaski.apps.main.iviolinplot import figure_defaults as iviolinplot_def
from flaski.apps.main.kegg import figure_defaults as kegg_def
from flaski.apps.main.lifespan import figure_defaults as lifespan_def
from flaski.apps.main.mds import figure_defaults as mds_def
from flaski.apps.main.pca import figure_defaults as pca_def
from flaski.apps.main.scatterplot import figure_defaults as scatterplot_def
# from flaski.apps.main.submissions import figure_defaults as submissions
from flaski.apps.main.tsne import figure_defaults as tsne_def
from flaski.apps.main.venndiagram import figure_defaults as venndiagram_def
from flaski.apps.main.violinplot import figure_defaults as violinplot_def
from flaski.apps.main.igseaplot import figure_defaults as igseaplot_def


defaults_dic={"rnaseqlake":dict,\
    "circularbarplots":circularbarplots_def,\
    "david":david_def,\
    "heatmap":heatmap_def,\
    "histogram":histogram_def,\
    "icellplot":icellplot_def,\
    "idendrogram":idendrogram_def,\
    "iheatmap":iheatmap_def,\
    "ihistogram":ihistogram_def,\
    "iscatterplot":iscatterplot_def,\
    "iviolinplot":iviolinplot_def,\
    "kegg":kegg_def,\
    "lifespan":lifespan_def,\
    "mds":mds_def,\
    "pca":pca_def,\
    "scatterplot":scatterplot_def,\
    "tsne":tsne_def,\
    "venndiagram":venndiagram_def,\
    "violinplot":violinplot_def,\
    "threeDscatterplot":threeDscatterplot_def,\
    "igseaplot":igseaplot_def
}

defaults_dic.update(EXT_DEFAULTS_DIC)