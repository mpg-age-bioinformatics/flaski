import pandas as pd
#import sys
#import os
# cwd = os.getcwd()

def make_figure(pa, path_to_data="/flaski/data/kegg"):
    kegg2map=pd.read_csv(path_to_data+"/kegg_long.tsv",sep="\t")
    hmdb2kegg=pd.read_csv(path_to_data+"/hmbd2kegg.tsv", sep="\t")
    maps_names=pd.read_csv(path_to_data+"/maps_names.tsv", sep="\t")

    # pa["ids"]="HMDB00001\tred\nHMDB0004935\tred"
    # pa["species"]="mmu"

    ids=pa["ids"].split("\n")
    ids=[ s.rstrip("\r").strip(" ") for s in ids if s != " "]
    ids=[ s for s in ids if s != " "]
    ids=[ s for s in ids if len(s) > 0 ]
    ids=[ s.split("\t") for s in ids ]
    idsdf=pd.DataFrame(ids)

    if len(idsdf.columns.tolist()) > 2:
        ancols=idsdf.columns.tolist()[2:]
        for i in idsdf.index.tolist():
            hmdbid=idsdf.loc[i,0]+":"
            for c in ancols:
                text=str(idsdf.loc[i,c])
                hmdbid=hmdbid+" "+text+","
            hmdbid=hmdbid[:-1]
            idsdf.loc[i,"___annotations___"]=hmdbid
    else:
        idsdf["___annotations___"]=idsdf[0]
            
    hmdb2kegg=pd.merge(idsdf,hmdb2kegg,left_on=[0],right_on=["HMDB ID"],how='left')
    hmdb2kegg=hmdb2kegg.dropna(subset=["KEGG ID"])
    hmdb2kegg=hmdb2kegg.drop([0],axis=1)
    hmdb2kegg["____html_color____"]=hmdb2kegg["KEGG ID"]+"%09"+hmdb2kegg[1]+","+hmdb2kegg[1]

    BASEURL="https://www.kegg.jp/kegg-bin/show_pathway?"

    kegg2map=pd.merge(hmdb2kegg,kegg2map,on=["KEGG ID"],how="left")
    kegg2map=kegg2map.dropna(subset=["MAPs"])

    maps_names=maps_names[[ "id", "map map id", "map map name", "%s map id" %pa["species"], "%s map name" %pa["species"] ]]

    kegg2map=pd.merge(kegg2map,maps_names,left_on=["MAPs"],right_on=["map map id"],how="left")

    report=pd.DataFrame()

    for keggmap in list(set(kegg2map["map map id"].tolist())):
        tmp=kegg2map[kegg2map["map map id"]==keggmap]
        tmp=tmp.drop_duplicates(subset=["KEGG ID"])

        html_color=tmp['____html_color____'].tolist()
        html_color="/".join(html_color)

        refname=list(tmp["map map name"])[0]
        refurl=BASEURL+keggmap+"/default%3snocolor/"+html_color

        speciesname=list(tmp[ "%s map name" %pa["species"] ])[0]
        speciesurl=BASEURL+keggmap.replace("map",pa["species"])+"/default%3snocolor/"+html_color

        if str(speciesname) == "nan" :
            speciesname=""
            speciesurl=""

        annotations=tmp["___annotations___"].tolist()
        annotations="; ".join(annotations)

        # excel_entry='=HYPERLINK("%s", "%s")' %(refurl,refname) +"; "+'=HYPERLINK("%s", "%s")' %(speciesurl,speciesname)  
        # text_entry=refname+": "+refurl+"; "+speciesname+": "+speciesurl
        # text_entry_ref=refname+": "+refurl
        # text_entry_spe=speciesname+": "+speciesurl

        #<a href="http://google.com">Cell 2</a>
        html_entry_ref='<a href="%s">%s</a>'%(refurl,refname)
        html_entry_spe='<a href="%s">%s</a>'%(speciesurl,speciesname)

        # html_entry_ref='<a href="http://google.com">Cell 2</a>'

        tmp=pd.DataFrame( { "Reference pathway":[refname], "Species pathway":[speciesname], "query":[annotations], "ref_link":[refurl], "species_link":[speciesurl]}) # "links":[excel_entry], "ref_link":[html_entry_ref],"species_link":[html_entry_spe],

        # s="https://www.kegg.jp/kegg-bin/show_pathway?map02010/default%3snocolor/C00378%09red,red/C00387%09red,red/C00294%09red,red/C00120%09red,red/C00315%09blue,blue/C00212%09blue,blue/C00114%09green,green/C00135%09green,green/C00148%09green,green/C00079%09green,green/C00047%09black,black"
        # w=20
        # ns=[s[i:i + w] for i in range(0, len(s), w)]
        # print(ns)

        report=pd.concat([report,tmp])
    
    report.reset_index(inplace=True, drop=True)
    # print(report.head())

    return report, None

def figure_defaults():
    pa={"ids":"",\
    "species":"hsa",\
    "species_options":["hsa","mmu","cel","dme"],\
    "download_format":["tsv","xlsx"],\
    "download_format_value":"xlsx",\
    "download_name":"KEGG",\
    "session_download_name":"MySession.KEGG",\
    "inputsessionfile":"Select file..",\
    "session_argumentsn":"MyArguments.KEGG",\
    "inputargumentsfile":"Select file.."}
    return pa