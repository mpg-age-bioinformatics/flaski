from myapp import app
import pandas as pd
from myapp.routes.apps._utils import make_table
from pyflaski.violinplot import figure_defaults
import json
from datetime import datetime
import os

PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)

path_to_files="/flaski_private/gtex/"

def read_menus(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2) # 2 hours
    def _read_menus(path_to_files=path_to_files):
        with open(f"{path_to_files}/menus.json", 'r') as json1_file:
            json1_str = json1_file.read()
            json1_data = json.loads(json1_str)
            return json1_data
    return _read_menus()

def read_data(cache, path_to_files=path_to_files):
    @cache.memoize(60*60*2) 
    def _read_data(path_to_files=path_to_files):
        df=pd.read_csv(f"{path_to_files}/data.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_data())

def read_significant(cache, path_to_files=path_to_files):
    @cache.memoize(60*60*2) 
    def _read_significant(path_to_files=path_to_files):
        df=pd.read_csv(f"{path_to_files}/sig.genes.tsv",sep="\t",dtype=str)
        df=df.rename(columns={"log2FoldChange":"log2(group_2/group_1)"})
        return df.to_json()
    return pd.read_json(_read_significant())

def gene_report(cache,gender,tissue,geneid,path_to_files=path_to_files):
    @cache.memoize(60*60*2) 
    def _gene_report(gender,tissue,geneid,path_to_files=path_to_files):

        metadata=pd.read_csv(f"{path_to_files}metadata.samples.tsv",sep="\t")

        if gender[0] == "male" :
            g=1
        elif gender[0] == "female":
            g=2

        samples=metadata[ (metadata["SMTS"].isin(tissue) ) & (metadata["SEX"]==g) ]
        samples_list=samples["SAMPID"].tolist()
        samples_dic=dict(zip(samples_list, samples["friendly_name"].tolist() ) )

        tissue_=tissue[0]
        gender_=gender[0]
        norm_counts_file=f"{path_to_files}{gender_}_{tissue_}.tissue.counts.tsv.deseq2.normcounts.tsv"

        ## Normcounts approach
        genes=pd.read_csv(norm_counts_file, sep="\t", usecols=[0])
        gene_index=genes.index.tolist()
        gene_index=gene_index.index(geneid)

        fileheader_size=0
        table_header=1
        skiprows=fileheader_size+table_header+gene_index

        df_head=pd.read_csv( norm_counts_file, nrows=1, sep="\t", header=None)
        df_head=pd.DataFrame(df_head.loc[0,])
        df_head_samples=df_head[0].tolist()
        # not all sample ids from counts seem to be on the tmp file (??) we therefore need the interception
        samples_list_=[ s.replace("-",".") for s in samples_list ]
  
        header=[ s for s in samples_list_  if s in df_head_samples ]
        df_head=df_head[ df_head[0].isin(header) ]
        header=df_head[0].tolist()
        header=[ s.replace(".","-") for s in header ]
        samples_index=df_head.index.tolist()

        df=pd.read_csv( norm_counts_file, skiprows=skiprows, nrows=1, usecols=[0]+samples_index , names=["Name"]+header , sep="\t", header=None)
        df=df.transpose()
        df.reset_index(inplace=True, drop=False)
        df=pd.merge(df, samples, left_on=["index"], right_on=["SAMPID"], how="left")


        ## TPM approach

        # genes=read_genes(cache)
        # gene_index=genes[genes["gene_id"]==geneid].index.tolist()[0]

        # fileheader_size=2
        # table_header=1
        # skiprows=fileheader_size+table_header+gene_index
        # df_head=pd.read_csv( f"{path_to_files}GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_tpm.gct", skiprows=2, nrows=1, sep="\t", header=None)
        # df_head=pd.DataFrame(df_head.loc[0,])
        # # not all sample ids from counts seem to be on the tmp file (??) we therefore need the interception
        # header=[ s for s in ["Name","Description"]+samples_list  if s in df_head[0].tolist() ]
        # df_head=df_head[ df_head[0].isin(header) ]
        # header=df_head[0].tolist()
        # samples_index=df_head.index.tolist()

        # df=pd.read_csv( f"{path_to_files}GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_tpm.gct", skiprows=skiprows, nrows=1, usecols=samples_index , names=header , sep="\t", header=None)
        # df=df.transpose()
        # df.reset_index(inplace=True, drop=False)
        # df=pd.merge(df, samples, left_on=["index"], right_on=["SAMPID"], how="left")

        return df.to_json()
    return pd.read_json(_gene_report(gender,tissue,geneid))

def read_genes(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2)
    def _read_genes(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"genes.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_genes())

def read_metadata(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2) # 2 hours
    def _read_metadata(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"metadata.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_metadata())


def change_table_minWidth(tb,minwidth):
    st=tb.style_table
    st["minWidth"]=minwidth
    tb.style_table=st
    return tb

def change_fig_minWidth(fig,minwidth):
    st=fig.style
    st["minWidth"]=minwidth
    fig.style=st
    return fig

def get_tables(cache,genders,tissues,groups,genenames,geneids):
    genes=read_genes(cache)
    data=read_data(cache)
    sigdf_=read_significant(cache)
    sigdf=sigdf_.drop(["file"],axis=1)

    if genders:
        data=data[data["gender"].isin(genders)]
        sigdf=sigdf[sigdf["gender"].isin(genders)]
        lgenders=len(genders)
    else:
        lgenders=0

    if tissues:
        data=data[data["tissue"].isin(tissues)]
        sigdf=sigdf[sigdf["tissue"].isin(tissues)]
        ltissues=len(tissues)
    else:
        ltissues=0

    if groups:
        data=data[ ( data["group_1"].isin(groups) ) | ( data["group_2"].isin(groups) )  ]
        sigdf=sigdf[ ( sigdf["group_1"].isin(groups) ) | ( sigdf["group_2"].isin(groups) )  ]

    if genenames or geneids :
        
        if genenames :
            lgenenames=len(genenames)
            sigdf_=sigdf[ ( sigdf["gene_name"].isin(genenames) ) ]
            genes_=genes[ ( genes["gene_name"].isin(genenames) ) ]
        else:
            lgenenames=0
            sigdf_=pd.DataFrame()
            genes_=pd.DataFrame()

        if geneids :
            lgeneids=len(geneids)
            sigdf__=sigdf[ ( sigdf["gene_id"].isin(geneids) ) ]
            genes__=genes[ ( genes["gene_id"].isin(geneids) ) ]
    
        else:
            lgeneids=0
            sigdf__=pd.DataFrame()
            genes__=pd.DataFrame()

        sigdf=pd.concat( [sigdf_, sigdf__ ] )
        sigdf=sigdf.drop_duplicates()

        genes=pd.concat( [genes_, genes__ ] )
        genes=genes.drop_duplicates()

    else:
        lgenenames=0
        lgeneids=0

    data=make_table(data,"data")
    sigdf=make_table(sigdf,"sigdf")

    if ( lgenders == 1 ) and ( ltissues == 1 ) and ( (lgenenames ==1 ) or (lgeneids == 1) ) :

        geneid=genes["gene_id"].tolist()[0]
        df=gene_report(cache, genders,tissues,geneid)
        df=df[["SAMPID","AGE","0","DTHHRDY", "SEX", "SMTS","SMTSD"]]
        df=df[2:]
        df["0"]=df["0"].astype(float)
        df=df.rename(columns={"0":"Normalized counts"})
        df=df.sort_values(by=["AGE","SMTSD"],ascending=True)

        pa=figure_defaults()

        gene_name=genes["gene_name"].tolist()[0]
        gender=genders[0]
        tissue=tissues[0]

        pa["style"]="Violinplot and Swarmplot"
        pa['title']=f'{gene_name}, {tissue}, {gender}'
        pa["x_val"]="AGE"
        pa["y_val"]="Normalized counts"
        pa["vals"]=[None]+df.columns.tolist()
        pa["xlabel"]="AGE"
        pa["ylabel"]="Normalized counts"    

        session_data={ "session_data": {"app": { "violinplot": {"filename":"<from.gtex.app>" ,'last_modified':datetime.timestamp( datetime.now()),"df":df.to_json(),"pa":pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        session_data["PYFLASKI_VERSION"]=PYFLASKI_VERSION

    else:

        df=None
        pa=None
        session_data=None

    return data, sigdf, df, pa, session_data
