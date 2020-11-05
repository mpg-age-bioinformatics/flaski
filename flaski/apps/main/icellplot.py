import pandas as pd
import plotly.express as px
import numpy as np


CHECKBOXES=["log10transform","xaxis_line","topxaxis_line","yaxis_line","rightyaxis_line","grid","reverse_color_scale"]


def make_figure(david_df, ge_df, pa,checkboxes=CHECKBOXES):
    """Generates figure.

    Args:
        david_df (pandas.core.frame.DataFrame): Pandas DataFrame containing the output of a DAVID query.
        ge_df (pandas.core.frame.DataFrame): Pandas DataFrame containing the gene expression values or other values to be mapped for each gene in `david_df`.

    Returns:
        A Plotly figure.

    """

    pa_={}
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



    david_df=david_df[ david_df[ pa["categories_column"] ].isin( pa["categories_to_plot_value"] ) ]

    david_df=david_df[0: int(pa["number_of_terms"]) ]

    if pa["annotation_column_value"]=="none":
        gedic=ge_df[[ pa["gene_identifier"] , pa["expression_values"] ]]
        gedic.loc[:, pa["gene_identifier"] ]=gedic.loc[:, pa["gene_identifier"] ].apply(lambda x: str(x).upper() )
        gedic.index=gedic[ pa["gene_identifier"] ].tolist()
        gedic=gedic.to_dict()[ pa["expression_values"] ]
    else:
        gedic=david_df[ [ pa["david_gene_ids"], pa["annotation_column_value"] ]]
        gedic_keys=gedic[pa["david_gene_ids"]].tolist()
        gedic_value=gedic[pa["annotation_column_value"]].tolist()
        gedic_keys=", ".join(gedic_keys).split(", ")
        gedic_value=", ".join(gedic_value).split(", ")
        gedic=pd.DataFrame({0:gedic_keys,1:gedic_value})
        gedic[1]=gedic[1].apply(lambda x: float(str(x).replace(",",".")) )
        gedic=gedic.drop_duplicates()
        gedic.index=gedic[0].tolist()
        gedic=gedic.to_dict()[ 1 ]

    if pa["annotation2_column_value"]=="none":
        namesdic=ge_df[[ pa["gene_identifier"] , pa["gene_name"] ]]
        namesdic.loc[:, pa["gene_identifier"] ]=namesdic.loc[:, pa["gene_identifier"] ].apply(lambda x: str(x).upper() )
        namesdic.index=namesdic[ pa["gene_identifier"] ].tolist()
        namesdic=namesdic.to_dict()[ pa["gene_name"] ]
    else:
        namesdic=david_df[ [ pa["david_gene_ids"], pa["annotation2_column_value"] ]]
        namesdic_keys=namesdic[pa["david_gene_ids"]].tolist()
        namesdic_value=namesdic[pa["annotation2_column_value"]].tolist()
        namesdic_keys=", ".join(namesdic_keys).split(", ")
        namesdic_value=", ".join(namesdic_value).split(", ")
        namesdic=pd.DataFrame({0:namesdic_keys,1:namesdic_value})
        namesdic=namesdic.drop_duplicates()
        namesdic.index=namesdic[0].tolist()
        namesdic=namesdic.to_dict()[ 1 ]

    if pa_["log10transform"]:
        david_df[pa["plotvalue"]]=david_df[ pa["plotvalue"] ].apply(lambda x: np.log10(float(x))*-1)

    plotdf=pd.DataFrame()
    for term in david_df[ pa["terms_column"]  ].tolist():
        tmp=david_df[david_df[ pa["terms_column"] ]==term]
        plotvalue=float(tmp.iloc[0,tmp.columns.tolist().index( pa["plotvalue"] )])
        # log10p=float(tmp.iloc[0,tmp.columns.tolist().index(pa["plotvalue"])])
        genes=tmp.iloc[0,tmp.columns.tolist().index( pa["david_gene_ids"] )].split(", ")
        tmp=pd.DataFrame({"term":term,"genes":genes})
        tmp["expression"]=tmp["genes"].apply(lambda x: float( gedic.get(x.upper())  ) )
        tmp["gene_name"]=tmp["genes"].apply(lambda x: namesdic.get(x.upper()) )
        tmp["n_genes"]=len(genes)
        tmp=tmp.sort_values(by=["expression"], ascending=True)
        tmp.reset_index(inplace=True, drop=True)
        frac=plotvalue/len(genes)
        tmp[pa["plotvalue"]]=frac
        if plotvalue < 0.001:
            plotvalue="{:.3e}".format(plotvalue)
        tmp["term value"]=plotvalue
        plotdf=pd.concat([plotdf,tmp])
    plotdf.reset_index(inplace=True, drop=True)

    expression=plotdf["expression"].tolist()

    if pa["lower_expression_percentile"]=="":
        pa_["lower_expression_percentile"]=0
    else:
        pa_["lower_expression_percentile"]=pa["lower_expression_percentile"]

    if pa["upper_expression_percentile"]=="":
        pa_["upper_expression_percentile"]=100
    else:
        pa_["upper_expression_percentile"]=pa["upper_expression_percentile"]

    low=np.percentile(expression, float( pa_["lower_expression_percentile"] ) )
    high=np.percentile(expression, float(pa["upper_expression_percentile"] ))

    if pa_["reverse_color_scale"]:
        pa_["color_scale_value"]=pa["color_scale_value"]+"_r"
    else:
        pa_["color_scale_value"]=pa["color_scale_value"]

    if pa["color_continuous_midpoint"]=="":
        pa_["color_continuous_midpoint"]=np.mean([low,high])
    else:
        pa_["color_continuous_midpoint"]=float(pa["color_continuous_midpoint"])
   

    selfdefined_cmap=True
    for value in ["lower_value","center_value","upper_value","lower_color","center_color","upper_color"]:
        if pa[value]=="":
            selfdefined_cmap=False
            break
    if selfdefined_cmap:
        range_diff=float(pa["upper_value"]) - float(pa["lower_value"])
        center=float(pa["center_value"]) - float(pa["lower_value"])
        center=center/range_diff

        color_continuous_scale=[ [0, pa["lower_color"]],\
            [center, pa["center_color"]],\
            [1, pa["upper_color"] ]]

        fig = px.bar( plotdf, y="term", x=pa["plotvalue"], color="expression", orientation="h",
                color_continuous_scale=color_continuous_scale, \
                hover_name="gene_name", hover_data=["expression", "term value","n_genes"],\
                range_color=[float(pa["lower_value"]),float(pa["upper_value"])],\
                title=pa["title"],\
                width=pa_["width"],\
                height=pa_["height"] )
 
    else:
        color_continuous_scale=pa_["color_scale_value"]
        if pa["color_continuous_midpoint"]!="":
            fig = px.bar( plotdf, y="term", x=pa["plotvalue"], color="expression", orientation="h",
                    color_continuous_scale=color_continuous_scale, \
                    hover_name="gene_name", hover_data=["expression", "term value","n_genes"],\
                    title=pa["title"],\
                    color_continuous_midpoint=pa_["color_continuous_midpoint"],
                    width=pa_["width"],\
                    height=pa_["height"] )
        else:
            fig = px.bar( plotdf, y="term", x=pa["plotvalue"], color="expression", orientation="h",
                    color_continuous_scale=color_continuous_scale, \
                    hover_name="gene_name", hover_data=["expression", "term value","n_genes"],\
                    title=pa["title"],\
                    range_color=[low,high],\
                    width=pa_["width"],\
                    height=pa_["height"] )

    # fig.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)',
    #                 marker_line_width=1.5, opacity=0.6)

    fig.update_traces(marker_line_width=0)

    if pa["xaxis_label"]!="":
        fig.update_layout(xaxis_title=pa["xaxis_label"])
    fig.update_layout(xaxis_title={ "font.size":int(pa["xaxis_label_size"])} )
    if pa["yaxis_label"]!="":
        fig.update_layout(yaxis_title=pa["yaxis_label"])
    fig.update_layout(yaxis_title={ "font.size":int(pa["yaxis_label_size"])} )

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

    fig.update_xaxes(showline=pa_["xaxis_line"], linewidth=float(pa["yaxis_linewidth"]), linecolor='black', mirror=pa_["topxaxis_line"])
    fig.update_yaxes(showline=pa_["yaxis_line"], linewidth=float(pa["yaxis_linewidth"]), linecolor='black', mirror=pa_["rightyaxis_line"])
    fig.update_xaxes(ticks="outside", tickwidth=float(pa["xaxis_tickwidth"]), tickcolor='black', ticklen=float(pa["xaxis_ticklen"]) )
    print("!!", pa["xaxis_side"])
    import sys
    sys.stdout.flush()
    fig.update_xaxes( side=pa["xaxis_side"] )
    # 'layout': {'xaxis': {'range': [40, 0], 'side': 'top'}

    fig.update_layout(xaxis_showgrid=pa_["grid"], font_color="black")

    return fig

def figure_defaults(checkboxes=CHECKBOXES):
    """Generates default figure arguments.

    Returns:
        dict: A dictionary of the style { "argument":"value"}
    """

    plot_arguments={
        "width":"1000",\
        "height":"600",\
        "david_cols":[],\
        "david_cols_value":"",\
        "ge_cols":[],\
        "ge_cols_value":"",\
        "gene_identifier":"ensembl_gene_id",\
        "expression_values":"log2FoldChange",\
        "gene_name":"gene_name",\
        "plotvalue":"PValue",\
        "log10transform":".on",\
        "number_of_terms":"20",\
        "terms_column":"Term",\
        "categories_column":"Category",\
        "categories_to_plot":[],\
        "categories_to_plot_value":[],\
        "david_gene_ids":"Genes",\
        "annotation_column":[],\
        "annotation_column_value":"none",\
        "annotation2_column_value":"none",\
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
        "color_continuous_midpoint":"",\
        "reverse_color_scale":".off",\
        "lower_value":"",\
        "center_value":"",\
        "upper_value":"",\
        "lower_color":"",\
        "center_color":"",\
        "upper_color":"",\
        "title":"Cell plot",\
        "xaxis_label":"",\
        "xaxis_label_size":"14",\
        "yaxis_label":"",\
        "yaxis_label_size":"14",\
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
        "xaxis_side_opt":["bottom","top"],\
        "xaxis_side":"bottom",\
        "yaxis_line":".on",\
        "yaxis_linewidth":"2",\
        "rightyaxis_line":".on",\
        "xaxis_tickwidth":"2",\
        "xaxis_ticklen":"5",\
        "grid":".on",\
        "download_format":["png","pdf","svg"],\
        "downloadf":"pdf",\
        "downloadn":"icellplot",\
        "session_downloadn":"MySession.icellplot",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.icellplot",\
        "inputargumentsfile":"Select file.."}    
        
    return plot_arguments

