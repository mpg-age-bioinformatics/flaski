import pandas as pd
import plotly.express as px
import numpy as np

def make_figure(david_df, ge_df, pa):

    pa_={}
    checkboxes=["xaxis_line","yaxis_line","topxaxis_line","rightyaxis_line", "grid"] # "robust"
    for c in checkboxes:
        if (pa[c] =="on") | (pa[c] ==".on"):
            pa_[c]=True
        else:
            pa_[c]=False

    nones=["width","height"]
    for n in nones:
        if pa[n] == "":
            pa_[n]=None
        else:
            pa_[n]=float(pa[n])

    gedic=ge_df[[ pa["gene_identifier"] , pa["expression_values"] ]]
    gedic.loc[:, pa["gene_identifier"] ]=gedic.loc[:, pa["gene_identifier"] ].apply(lambda x: str(x).upper() )
    gedic.index=gedic[ pa["gene_identifier"] ].tolist()
    gedic=gedic.to_dict()[ pa["expression_values"] ]

    namesdic=ge_df[[ pa["gene_identifier"] , pa["gene_name"] ]]
    namesdic.loc[:, pa["gene_identifier"] ]=namesdic.loc[:, pa["gene_identifier"] ].apply(lambda x: str(x).upper() )
    namesdic.index=namesdic[ pa["gene_identifier"] ].tolist()
    namesdic=namesdic.to_dict()[ pa["gene_name"] ]

    david_df=david_df[0: int(pa["number_of_terms"]) ]
    david_df["-log10(p value)"]=david_df[ pa["pvalue"] ].apply(lambda x: np.log10(x)*-1)

    plotdf=pd.DataFrame()
    for term in david_df[ pa["terms_column"]  ].tolist():
        tmp=david_df[david_df[ pa["terms_column"] ]==term]
        pvalue=tmp.iloc[0,tmp.columns.tolist().index( pa["pvalue"] )]
        log10p=tmp.iloc[0,tmp.columns.tolist().index("-log10(p value)")]
        genes=tmp.iloc[0,tmp.columns.tolist().index( pa["david_gene_ids"] )].split(", ")
        tmp=pd.DataFrame({"term":term,"genes":genes})
        tmp["expression"]=tmp["genes"].apply(lambda x: gedic.get(x.upper()) )
        tmp["gene_name"]=tmp["genes"].apply(lambda x: namesdic.get(x.upper()) )
        tmp["n_genes"]=len(genes)
        tmp=tmp.sort_values(by=["expression"], ascending=True)
        tmp.reset_index(inplace=True, drop=True)
        frac=log10p/len(genes)
        tmp["-log10(p value)"]=frac
        if pvalue < 0.001:
            pvalue="{:.3e}".format(pvalue)
        tmp["term p value"]=pvalue
        plotdf=pd.concat([plotdf,tmp])
    plotdf.reset_index(inplace=True, drop=True)

    expression=plotdf["expression"].tolist()
    low=np.percentile(expression, float( pa["lower_expression_percentile"] ) )
    high=np.percentile(expression, float(pa["upper_expression_percentile"] ))

    fig = px.bar( plotdf, y="term", x="-log10(p value)", color="expression", orientation="h",
             color_continuous_scale=pa["color_scale_value"], \
             hover_name="gene_name", hover_data=["expression", "term p value","n_genes"],\
             title=pa["title"],\
             range_color=[low,high],\
             width=pa_["width"],\
             height=pa_["height"] )

    fig.update_layout({"yaxis":{"tickfont":{"size": float(pa["yaxis_font_size"]) }}, "xaxis":{"tickfont":{"size":float(pa["xaxis_font_size"])}} })

    fig.update_layout(title={"font":{"size": float(pa["title_font_size"]) }})

    fig.update_layout(coloraxis_colorbar=dict(
        title={'text': pa["color_bar_title"], "font":{"size": float(pa["color_bar_title_font_size"]) }},
        thicknessmode="pixels",
        ticks="outside",
        tickwidth=float(pa["color_bar_tickwidth"]),
        tickfont={"size":float(pa["color_bar_tickfont"])},
        ticklen=float(pa["color_bar_ticklen"])
    ))

    fig["data"][0]['hovertemplate']='<b>%{hovertext}</b><br>'+pa["expression_values"]+'=%{marker.color}<br><br>term: %{y}<br>term p value=%{customdata[1]}<br>n genes=%{customdata[2]}'
    fig.update_layout(template='plotly_white')

    fig.update_xaxes(showline=pa_["xaxis_line"], linewidth=float(pa["xaxis_linewidth"]), linecolor='black', mirror=pa_["topxaxis_line"])
    fig.update_yaxes(showline=pa_["yaxis_line"], linewidth=float(pa["yaxis_linewidth"]), linecolor='black', mirror=pa_["rightyaxis_line"])
    fig.update_xaxes(ticks="outside", tickwidth=float(pa["xaxis_tickwidth"]), tickcolor='black', ticklen=float(pa["xaxis_ticklen"]) )
    fig.update_layout(xaxis_showgrid=pa_["grid"])

    return fig

def figure_defaults():
    plot_arguments={
        "width":"",\
        "height":"",\
        "david_cols":[],\
        "david_cols_value":"",\
        "ge_cols":[],\
        "ge_cols_value":"",\
        "gene_identifier":"ensembl_gene_id",\
        "expression_values":"log2FoldChange",\
        "gene_name":"gene_name",\
        "pvalue":"ease",\
        "number_of_terms":"20",\
        "terms_column":"termName",\
        "david_gene_ids":"geneIds",\
        "lower_expression_percentile":"5",\
        "upper_expression_percentile":"95",\
        "color_scale":['aggrnyl','agsunset','blackbody','bluered','blues','blugrn','bluyl','brwnyl',\
                'bugn','bupu','burg','burgyl','cividis','darkmint','electric','emrld','gnbu',\
                'greens','greys','hot','inferno','jet','magenta','magma','mint','orrd','oranges',\
                'oryel','peach','pinkyl','plasma','plotly3','pubu','pubugn','purd','purp','purples',\
                'purpor','rainbow','rdbu','rdpu','redor','reds','sunset','sunsetdark','teal',\
                'tealgrn','viridis','ylgn','ylgnbu','ylorbr','ylorrd','algae','amp','deep','dense',\
                'gray','haline','ice','matter','solar','speed','tempo','thermal','turbid','armyrose',\
                'brbg','earth','fall','geyser','prgn','piyg','picnic','portland','puor','rdgy',\
                'rdylbu','rdylgn','spectral','tealrose','temps','tropic','balance','curl','delta',\
                'edge','hsv','icefire','phase','twilight','mrybm','mygbm'],\
        "color_scale_value":"bluered",\
        "title":"Cell plot",\
        "yaxis_font_size":"10",\
        "xaxis_font_size":"10",\
        "title_font_size":"20",\
        "color_bar_title":"color bar",\
        "color_bar_title_font_size":"10",\
        "color_bar_tickwidth":"2",\
        "color_bar_tickfont":"10",\
        "color_bar_ticklen":"5",\
        "xaxis_line":".on",\
        "xaxis_linewidth":"2",\
        "topxaxis_line":".on",\
        "yaxis_line":".on",\
        "yaxis_linewidth":"2",\
        "rightyaxis_line":".on",\
        "xaxis_tickwidth":"2",\
        "xaxis_ticklen":"5",\
        "grid":".on",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"heatmap",\
        "session_downloadn":"MySession.icellplot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.icellplot",\
        "inputargumentsfile":"Select file.."}    

    checkboxes=["xaxis_line","topxaxis_line","yaxis_line","rightyaxis_line","grid"]

    # not update list
    notUpdateList=["inputsessionfile"]

    # lists without a default value on the arguments
    excluded_list=[]

    # lists with a default value on the arguments
    allargs=list(plot_arguments.keys())

    # dictionary of the type 
    # {"key_list_name":"key_default_value"} 
    # eg. {"marker_size":"markers"}
    lists={} 
    for i in range(len(allargs)):
        if type(plot_arguments[allargs[i]]) == type([]):
            if allargs[i] not in excluded_list:
                lists[allargs[i]]=allargs[i+1]

    return plot_arguments, lists, notUpdateList, checkboxes

