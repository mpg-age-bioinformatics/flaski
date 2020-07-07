import pandas as pd
import sys
from suds.client import Client as sudsclient
import ssl
from flaski.routines import fuzzy_search


david_categories = [
  'GOTERM_BP_FAT', 'GOTERM_CC_FAT', 'GOTERM_MF_FAT', 'KEGG_PATHWAY',
  'BIOCARTA', 'PFAM', 'PROSITE' ]

david_fields = [
  'categoryName', 'termName', 'listHits', 'percent',
  'ease', 'geneIds', 'listTotals', 'popHits', 'popTotals',
  'foldEnrichment', 'bonferroni', 'benjamini', 'afdr']
# include:
# 'fisher'
# 'termName' to 'term' and 'term_name'

DEBUG_GENES="ENSMUSG00000092622,ENSMUSG00000004415,ENSMUSG00000017144,ENSMUSG00000028972,ENSMUSG00000031026,ENSMUSG00000006360,ENSMUSG00000039106,ENSMUSG00000038932,\
ENSMUSG00000040629,ENSMUSG00000044254,ENSMUSG00000060675,ENSMUSG00000037465,ENSMUSG00000033998,ENSMUSG00000030785,ENSMUSG00000042808,ENSMUSG00000034612,ENSMUSG00000032883,\
ENSMUSG00000037820,ENSMUSG00000052955,ENSMUSG00000005892,ENSMUSG00000086228,ENSMUSG00000035504,ENSMUSG00000074063,ENSMUSG00000085682,ENSMUSG00000048376,ENSMUSG00000018865,\
ENSMUSG00000025104,ENSMUSG00000022763,ENSMUSG00000030800,ENSMUSG00000021226,ENSMUSG00000038188,ENSMUSG00000038507,ENSMUSG00000014776,ENSMUSG00000029151,ENSMUSG00000030549,\
ENSMUSG00000063430,ENSMUSG00000021194,ENSMUSG00000028836,ENSMUSG00000003849,ENSMUSG00000017493,ENSMUSG00000001506,ENSMUSG00000059991,ENSMUSG00000058454,ENSMUSG00000024962,\
ENSMUSG00000020042,ENSMUSG00000037035,ENSMUSG00000058301,ENSMUSG00000058741,ENSMUSG00000039814,ENSMUSG00000026807,ENSMUSG00000046607,ENSMUSG00000004341,ENSMUSG00000038291,\
ENSMUSG00000070000,ENSMUSG00000029718,ENSMUSG00000026114,ENSMUSG00000032946,ENSMUSG00000022505,ENSMUSG00000034450,ENSMUSG00000067261,ENSMUSG00000022432,ENSMUSG00000022048,\
ENSMUSG00000032494,ENSMUSG00000026418,ENSMUSG00000051455,ENSMUSG00000018411,ENSMUSG00000009596,ENSMUSG00000022469,ENSMUSG00000087283,ENSMUSG00000073779,ENSMUSG00000031379,\
ENSMUSG00000034573,ENSMUSG00000008090,ENSMUSG00000046500,ENSMUSG00000013418,ENSMUSG00000028760,ENSMUSG00000003848,ENSMUSG00000040428,ENSMUSG00000004891,ENSMUSG00000030350,\
ENSMUSG00000003037,ENSMUSG00000055553,ENSMUSG00000034112,ENSMUSG00000025196,ENSMUSG00000034324,ENSMUSG00000026775,ENSMUSG00000056537,ENSMUSG00000029168,ENSMUSG00000031410,\
ENSMUSG00000034880,ENSMUSG00000034731,ENSMUSG00000031584,ENSMUSG00000084807,ENSMUSG00000031861,ENSMUSG00000022265,ENSMUSG00000031438,ENSMUSG00000033658,ENSMUSG00000059456,\
ENSMUSG00000042249,ENSMUSG00000024331,ENSMUSG00000034807,ENSMUSG00000030747,ENSMUSG00000031660,ENSMUSG00000023800,ENSMUSG00000070880,ENSMUSG00000023045,ENSMUSG00000052724,\
ENSMUSG00000061815,ENSMUSG00000032068,ENSMUSG00000030310,ENSMUSG00000013766,ENSMUSG00000063903,ENSMUSG00000023951,ENSMUSG00000030137,ENSMUSG00000015994,ENSMUSG00000040624,\
ENSMUSG00000048644,ENSMUSG00000038840,ENSMUSG00000032015,ENSMUSG00000028949,ENSMUSG00000037971,ENSMUSG00000048371,ENSMUSG00000047264,ENSMUSG00000015243,ENSMUSG00000039865,\
ENSMUSG00000031683,ENSMUSG00000032643,ENSMUSG00000074593,ENSMUSG00000032540,ENSMUSG00000040280,ENSMUSG00000024036,ENSMUSG00000074365,ENSMUSG00000021266,ENSMUSG00000104968,\
ENSMUSG00000006205,ENSMUSG00000043419,ENSMUSG00000032020,ENSMUSG00000039395,ENSMUSG00000062939,ENSMUSG00000031985,ENSMUSG00000034486,ENSMUSG00000034863,ENSMUSG00000047502,\
ENSMUSG00000050737,ENSMUSG00000024012,ENSMUSG00000008892,ENSMUSG00000015652,ENSMUSG00000022178,ENSMUSG00000048373,ENSMUSG00000022292,ENSMUSG00000019312,ENSMUSG00000039831,\
ENSMUSG00000026458,ENSMUSG00000020122,ENSMUSG00000031924,ENSMUSG00000004565,ENSMUSG00000037669,ENSMUSG00000005267,ENSMUSG00000002949,ENSMUSG00000048988,ENSMUSG00000053856,\
ENSMUSG00000090363,ENSMUSG00000009670,ENSMUSG00000056515,ENSMUSG00000036442,ENSMUSG00000031751,ENSMUSG00000030263,ENSMUSG00000022040,ENSMUSG00000031749,ENSMUSG00000038742,\
ENSMUSG00000070780,ENSMUSG00000070708,ENSMUSG00000003808,ENSMUSG00000037997,ENSMUSG00000026773,ENSMUSG00000022099,ENSMUSG00000081593,ENSMUSG00000045467,ENSMUSG00000031509,\
ENSMUSG00000031672,ENSMUSG00000030413,ENSMUSG00000042757,ENSMUSG00000031508,ENSMUSG00000022180,ENSMUSG00000037355,ENSMUSG00000035561,ENSMUSG00000106647,ENSMUSG00000063049,\
ENSMUSG00000028785,ENSMUSG00000031453,ENSMUSG00000111147,ENSMUSG00000003283,ENSMUSG00000063488,ENSMUSG00000046774,ENSMUSG00000036054,ENSMUSG00000024042,ENSMUSG00000039157,\
ENSMUSG00000038060,ENSMUSG00000030283,ENSMUSG00000038521,ENSMUSG00000038393,ENSMUSG00000030772,ENSMUSG00000030428,ENSMUSG00000041180,ENSMUSG00000031729,ENSMUSG00000054850,\
ENSMUSG00000025931,ENSMUSG00000039384,ENSMUSG00000022479,ENSMUSG00000029287,ENSMUSG00000025743,ENSMUSG00000042386,ENSMUSG00000096210,ENSMUSG00000050288,ENSMUSG00000019261,\
ENSMUSG00000040537,ENSMUSG00000026185,ENSMUSG00000029761,ENSMUSG00000027071,ENSMUSG00000005705,ENSMUSG00000008450,ENSMUSG00000018604,ENSMUSG00000060038,ENSMUSG00000006585,\
ENSMUSG00000086236,ENSMUSG00000054408,ENSMUSG00000029122,ENSMUSG00000025742,ENSMUSG00000004319,ENSMUSG00000052675,ENSMUSG00000031948,ENSMUSG00000081044,ENSMUSG00000039830,\
ENSMUSG00000030411,ENSMUSG00000045010,ENSMUSG00000039616,ENSMUSG00000011837,ENSMUSG00000022211,ENSMUSG00000001472,ENSMUSG00000000738,ENSMUSG00000042659,ENSMUSG00000071076,\
ENSMUSG00000031838,ENSMUSG00000020256,ENSMUSG00000028017,ENSMUSG00000063659,ENSMUSG00000046718,ENSMUSG00000032715,ENSMUSG00000023495,ENSMUSG00000099370,ENSMUSG00000031486,\
ENSMUSG00000038292,ENSMUSG00000031760,ENSMUSG00000007950,ENSMUSG00000039617,ENSMUSG00000057672,ENSMUSG00000031622,ENSMUSG00000025432,ENSMUSG00000055835,ENSMUSG00000031665,\
ENSMUSG00000008206,ENSMUSG00000063018,ENSMUSG00000091568,ENSMUSG00000033931,ENSMUSG00000021701,ENSMUSG00000022016,ENSMUSG00000023995,ENSMUSG00000030630,ENSMUSG00000032796,\
ENSMUSG00000029603,ENSMUSG00000048126,ENSMUSG00000053604,ENSMUSG00000097757,ENSMUSG00000087084,ENSMUSG00000018796,ENSMUSG00000037103,ENSMUSG00000017652,ENSMUSG00000020184,\
ENSMUSG00000050914,ENSMUSG00000031765,ENSMUSG00000068758,ENSMUSG00000061126,ENSMUSG00000004952,ENSMUSG00000031731,ENSMUSG00000022754,ENSMUSG00000030523,ENSMUSG00000002668"
def debug_david(user,DEBUG_GENES=DEBUG_GENES, ids=None):
    ssl._create_default_https_context = ssl._create_unverified_context
    url = 'https://david.ncifcrf.gov/webservice/services/DAVIDWebService?wsdl'
    client = sudsclient(url)
    client.wsdl.services[0].setlocation('https://david.ncifcrf.gov/webservice/services/DAVIDWebService.DAVIDWebServiceHttpSoap11Endpoint/')
    client_auth = client.service.authenticate(user)
    if not ids:
      ids=DEBUG_GENES
    database="ENSEMBL_GENE_ID"
    name="target"
    categories="GOTERM_BP_FAT,GOTERM_CC_FAT,GOTERM_MF_FAT,PFAM,KEGG_PATHWAY,OMIM_DISEASE"
    p=0.1
    n=2
    size = client.service.addList(ids, database, name, 0) #| inputListIds,idType,listName,listType)
    client_categories = client.service.setCategories(categories)
    client_report = client.service.getChartReport(p, n)
    size_report = len(client_report)
    report="Success: "+str(size)+"; "+str(size_report)
    return report


def run_david(pa, path_to_ensembl_maps="/flaski/data"):


    #database, categories, user, ids, ids_bg = None, name = '', name_bg = '', verbose = False, p = 0.1, n = 2):
    # Modified from https://david.ncifcrf.gov/content.jsp?file=WS.html
    # by courtesy of HuangYi @ 20110424

    """Queries the DAVID database for an enrichment analysis
    Check https://david.ncifcrf.gov/content.jsp?file=DAVID_API.html for database == "type" tag and categories ==  "annot" tag.

    Args:
        pa (dict): A dictionary of the style { "argument":"value"} as outputted by `figure_defaults`.

    Returns:
        None if no ids match the queried database, or a  Pandas DataFrame with results.

    """

    database=pa["database_value"]
    categories_=[ s for s in list( pa.keys() ) ]
    categories_=[ s for s in categories_ if "categories_" in s ]
    categories_=[ s for s in categories_ if "_value" in s ]
    categories=[]
    for k in categories_:
        categories=categories+pa[k]
    categories=",".join(categories)
    user=pa["user"]
    ids=pa["ids"].split("\n")
    ids=[ s.rstrip("\r").strip(" ") for s in ids if s != " "]
    ids=[ s for s in ids if s != " "]
    ids=[ s for s in ids if len(s) > 0 ]
    ids=[ s.split("\t") for s in ids ]
    idsdf=pd.DataFrame(ids)

    names_dbs=["name_hsa_ensembl", "name_mus_ensembl", "name_cel_ensembl","name_dros_ensembl" ]
    if database in names_dbs:
      file_dic={"name_hsa_ensembl":"Homo_sapiens.GRCh38.92.tsv", "name_mus_ensembl":"Mus_musculus.GRCm38.92.tsv", "name_cel_ensembl":"Caenorhabditis_elegans.WBcel235.92.tsv","name_dros_ensembl":"Drosophila_melanogaster.BDGP6.28.92.tsv"}
      id_name=pd.read_csv(path_to_ensembl_maps+"/"+file_dic[database],sep="\t")
      db_names=id_name["gene_name"].tolist()
      query_names=idsdf[0].tolist()
      query_names=",".join(query_names)
      found_values, emsg=fuzzy_search(query_names,db_names)
      if emsg:
        return None, None, emsg
      newcol=idsdf.columns.tolist()[-1]+1
      id_name["gene_name"]=id_name["gene_name"].apply(lambda x: str(x).lower() )
      id_name.index=id_name["gene_name"].tolist()
      id_name=id_name.to_dict()["gene_id"]
      idsdf[newcol]=idsdf[0]
      idsdf[0]=idsdf[0].apply(lambda x: id_name[ str(x).lower() ])


    # insert mapping of ensembl gene name to gene id here

    annotations=idsdf.columns.tolist()
    ids=idsdf[0].tolist()
    ids_map={}
    if len(annotations) > 1:
      idsdf[0]=idsdf[0].apply(lambda x: x.upper() )
      idsdf.index=idsdf[0].tolist()
      idsdf=idsdf.drop([0],axis=1)
      ids_map=idsdf.to_dict()
  
    if " ".join( pa["ids_bg"].split(" ")[:12] ) != "Leave empty if you want to use all annotated genes for your":
      ids_bg=pa["ids_bg"].split("\n")
      ids_bg=[ s.rstrip("\r").strip(" ") for s in ids_bg ]
      ids_bg=[ s for s in ids_bg if s != " "]
      ids_bg=[ s for s in ids_bg if len(s) > 0 ]
      if len(ids_bg) == 0:
        ids_bg = None
      else:
          if database in names_dbs:
            file_dic={"name_hsa_ensembl":"Homo_sapiens.GRCh38.92.tsv", "name_mus_ensembl":"Mus_musculus.GRCm38.92.tsv", "name_cel_ensembl":"Caenorhabditis_elegans.WBcel235.92.tsv","name_dros_ensembl":"Drosophila_melanogaster.BDGP6.92.tsv"}
            id_name=pd.read_csv(path_to_ensembl_maps+file_dic[database],sep="\t")
            id_name_=id_name.copy()
            db_names=id_name["gene_name"].tolist()
            query_names=",".join(ids_bg)
            found_values, emsg=fuzzy_search(query_names,db_names)
            if emsg:
              return None, None, emsg
            id_name["gene_name"]=id_name["gene_name"].apply(lambda x: str(x).lower() )
            id_name.index=id_name["gene_name"].tolist()
            id_name=id_name.to_dict()["gene_id"]
            ids_bg=[ id_name[ str(x).lower() ] for x in ids_bg  ]
            id_name_=id_name_[ id_name_["gene_id"].isin(ids_bg) ]
            id_name_["gene_id"]=id_name_["gene_id"].apply(lambda x: str(x).upper() )
            id_name_.index=id_name_["gene_id"].tolist()
            id_name_=id_name_.to_dict()["gene_name"]
          else:
            id_name_=None

            # bg_gene_names= keep on here

    else:
      ids_bg=None
    name=pa["name"]
    if ids_bg is not None:
      name_bg=pa["name_bg"]
    else:
      name_bg=""

    p=pa["p"]
    n=pa["n"]    
    #, categories, user, ids, ids_bg = None, name = '', name_bg = '', verbose = False, p = 0.1, n = 2

    verbose=False
    ids = ','.join([str(i) for i in ids])
    use_bg = 0

    if database in names_dbs:
      database="ENSEMBL_GENE_ID"


    # print("Testing")
    # test=debug_david(pa["user"],ids=ids)
    # print(test)

    if ids_bg:
      ids_bg = ','.join([str(i) for i in ids_bg])


    ssl._create_default_https_context = ssl._create_unverified_context
    url = 'https://david.ncifcrf.gov/webservice/services/DAVIDWebService?wsdl'
    try:
      client = sudsclient(url)
    except:
      return None, None, "Could not connect to DAVID. Server might be down."

    client.wsdl.services[0].setlocation('https://david.ncifcrf.gov/webservice/services/DAVIDWebService.DAVIDWebServiceHttpSoap11Endpoint/')
    try:
      client_auth = client.service.authenticate(user)
    except:
      return None, None, "Could not connect to DAVID. Server might be down."
    
    if str(client_auth) == "Failed. For user registration, go to http://david.abcc.ncifcrf.gov/webservice/register.htm" :
      return None, None, str(client_auth)
    if verbose:
      print('User Authentication:', client_auth)
      sys.stdout.flush()

    # if ids_bg :
    #   size = client.service.addList(ids_bg, database, name, 0)
    #   if float(size) > float(0):
    #     client_report=client.service.getListReport()
    #     bg_mapped=[]
    #     for r in client_report:
    #         d = dict(r)
    #         bg_mapped.append(d["values"][0])
    #     bg_not_mapped=[ s for s in ids_bg.split(",") if s not in bg_mapped ]

    size = client.service.addList(ids, database, name, 0) #| inputListIds,idType,listName,listType)
    report_stats=[['Mapping rate of ids: ', str(size)]]
    if verbose:
      print('Mapping rate of ids: ', str(size))
      sys.stdout.flush()
    if float(size) <= float(0):
      msg='Mapping rate of ids: %s.' %str(size)
      return None, None, msg

    # client_report=client.service.getListReport()
    # mapped=[]
    # for r in client_report:
    #     d = dict(r)
    #     mapped.append(d["values"][0])
    # not_mapped=[ s for s in ids.split(",") if s not in mapped ]

    #print("Finished retrieving list report.")
    #sys.stdout.flush()

    if ids_bg:
      #print("User given BG.")
      #sys.stdout.flush()
      size_bg = client.service.addList(ids_bg, database, name_bg, 1)
      report_stats.append(['Mapping rate of background ids: ', str(size_bg)])
      if verbose:
        print('Mapping rate of background ids: ', str(size_bg))
        sys.stdout.flush()
        if float(size_bg) <= float(0):
          msg='Mapping rate of background ids: %s' %str(size_bg)
          return None, None, msg

    client_categories = client.service.setCategories(categories)
    report_stats.append(['Categories used: ', client_categories])
    if verbose:
      print('Categories used: ', client_categories)
      sys.stdout.flush()
    client_report = client.service.getChartReport(p, n)
    size_report = len(client_report)
    report_stats.append(['Records reported: ', str(size_report)])
    if verbose:
      print('Records reported: ', str(size_report))
      sys.stdout.flush()

    def get_map(x,ids_map):
      genes=x.split(", ")
      genes=[ str(ids_map[gene.upper()]) for gene in genes ]
      genes=", ".join(genes)
      return genes

    if size_report > 0:
        df = []
        for r in client_report:
            d = dict(r)
            line = []
            for f in david_fields:
                line.append(str(d[f]).encode('ascii','ignore'))
            df.append(line)
        df = pd.DataFrame(df)
        df.columns=david_fields
        for col in david_fields:
            df[col] = df[col].apply(lambda x: x.decode())

        df.columns=["Category","Term","Count","%","PValue","Genes","List Total","Pop Hits","Pop Total","Fold Enrichment","Bonferroni","Benjamini","FDR"]
        
        # insert ensembl gene name to gene id here 
        
        if len(list(ids_map.keys())) > 0:
          for annotation in list(ids_map.keys()):
            genes_to_annotation=ids_map[annotation]
            df["annotation_%s" %str(annotation)]=df["Genes"].apply(lambda x:get_map(x,ids_map=genes_to_annotation) )
    
    else:
        df=pd.DataFrame(columns=["Category","Term","Count","%","PValue","Genes","List Total","Pop Hits","Pop Total","Fold Enrichment","Bonferroni","Benjamini","FDR"])

    # mapped=pd.DataFrame({ "target_mapped":mapped })
    # not_mapped=pd.DataFrame({ "target_not_mapped": not_mapped })

    # insert ensembl gene name to gene id here 

    # if len(list(ids_map.keys())) > 0:

      # for annotation in list(ids_map.keys()):
      #   genes_to_annotation=ids_map[annotation]
        # mapped["target_mapped_annotation_%s" %str(annotation)]=mapped["target_mapped"].apply(lambda x:get_map(x,ids_map=genes_to_annotation) )
        # not_mapped["target_not_mapped_annotation_%s" %str(annotation)]=not_mapped["target_not_mapped"].apply(lambda x:get_map(x,ids_map=genes_to_annotation) )

    # mapped=pd.concat([mapped,not_mapped],axis=1)

    # if ids_bg:
    #   bg_mapped=pd.DataFrame({ "bg_mapped":bg_mapped })
    #   bg_not_mapped=pd.DataFrame({ "bg_not_mapped": bg_not_mapped })
    #   if id_name_:
    #     bg_mapped["bg_mapped_name"]=bg_mapped["bg_mapped"].apply(lambda x: id_name_[x] )
    #     bg_not_mapped["bg_not_mapped_name"]=bg_not_mapped["bg_not_mapped"].apply(lambda x: id_name_[x] )

    #   # insert ensembl gene name to gene id here 

    #   # if len(list(ids_map.keys())) > 0:
    #   #     for annotation in list(ids_map.keys()):
    #   #       genes_to_annotation=ids_map[annotation]
    #   #       bg_mapped["bg_mapped_annotation_%s" %str(annotation)]=bg_mapped["bg_mapped"].apply(lambda x:get_map(x,ids_map=genes_to_annotation) )
    #   #       bg_not_mapped["bg_not_mapped_annotation_%s" %str(annotation)]=bg_not_mapped["bg_not_mapped"].apply(lambda x:get_map(x,ids_map=genes_to_annotation) )
      
    #   mapped=pd.concat([mapped,bg_mapped],axis=1)
    #   mapped=pd.concat([mapped,bg_not_mapped],axis=1)

    report_stats=pd.DataFrame(report_stats,columns=["Field","Value"])

    return df, report_stats, None

def figure_defaults():
    """Generates default DAVID query arguments.

    :param database: A string for the database to query, e.g. 'WORMBASE_GENE_ID'
    :param categories: A comma separated string with databases
    :param user: A user ID registered at DAVID for querying
    :param ids: A list with identifiers
    :param name: A string with the name for the query set
    :param ids_bg: A list with the background identifiers to enrich against,
      'None' for whole set
    :param name_bg: A string with the name for the background set
    :param p: Maximum p value for enrichment of a term
    :param n: Minimum number of genes within a term

    Returns:
        dict: A dictionary of the style { "argument":"value"}
    """

    # 'GENE_SYMBOL',
    plot_arguments={
        "database":['AFFYMETRIX_3PRIME_IVT_ID', 'AFFYMETRIX_EXON_GENE_ID',
          'AFFYMETRIX_SNP_ID', 'AGILENT_CHIP_ID',
          'AGILENT_ID', 'AGILENT_OLIGO_ID',
          'ENSEMBL_GENE_ID',"name_hsa_ensembl", "name_mus_ensembl", "name_cel_ensembl","name_dros_ensembl", 'ENSEMBL_TRANSCRIPT_ID',
          'ENTREZ_GENE_ID', 'FLYBASE_GENE_ID',
          'FLYBASE_TRANSCRIPT_ID','GENBANK_ACCESSION',
          'GENPEPT_ACCESSION', 'GENOMIC_GI_ACCESSION',
          'PROTEIN_GI_ACCESSION', 'ILLUMINA_ID',
          'IPI_ID', 'MGI_ID', 'PFAM_ID',
          'PIR_ACCESSION','PIR_ID','PIR_NREF_ID', 'REFSEQ_GENOMIC',
          'REFSEQ_MRNA','REFSEQ_PROTEIN','REFSEQ_RNA','RGD_ID',
          'SGD_ID','TAIR_ID','UCSC_GENE_ID','UNIGENE',
          'UNIPROT_ACCESSION','UNIPROT_ID','UNIREF100_ID','WORMBASE_GENE_ID',
          'WORMPEP_ID','ZFIN_ID'],\
        "database_value":'ENSEMBL_GENE_ID',\
        "categories_gene_ontology":['GOTERM_BP_1', 'GOTERM_BP_2', 'GOTERM_BP_3', 'GOTERM_BP_4',
                 'GOTERM_BP_5', 'GOTERM_BP_ALL', 'GOTERM_BP_FAT', 'GOTERM_CC_1',
                 'GOTERM_CC_2', 'GOTERM_CC_3', 'GOTERM_CC_4', 'GOTERM_CC_5',
                 'GOTERM_CC_ALL', 'GOTERM_CC_FAT', 'GOTERM_MF_1', 'GOTERM_MF_2',
                 'GOTERM_MF_3', 'GOTERM_MF_4', 'GOTERM_MF_5', 'GOTERM_MF_ALL',
                 'GOTERM_MF_FAT'],\
        "categories_gene_ontology_value": ['GOTERM_BP_FAT','GOTERM_CC_FAT','GOTERM_MF_FAT'],\
        "categories_gene_domains":['BLOCKS_ID', 'COG', 'INTERPRO', 'PDB_ID',
                   'PFAM', 'PIR_ALN','PIR_HOMOLOGY_DOMAIN', 'PIR_SUPERFAMILY',
                   'PRINTS', 'PRODOM', 'PROSITE', 'SCOP_ID',
                   'SMART', 'TIGRFAMS'],\
        "categories_gene_domains_value":["PFAM"],\
        "categories_pathways":['BBID', 'BIOCARTA', 'EC_NUMBER', 'KEGG_COMPOUND', 'KEGG_PATHWAY','KEGG_REACTION'],\
        "categories_pathways_value":['KEGG_PATHWAY'],\
        "categories_general_annotations":['ALIAS_GENE_SYMBOL', 'CHROMOSOME', 'CYTOBAND', 'GENE', 'GENE_SYMBOL', 
                        'HOMOLOGOUS_GENE', 'LL_SUMMARY', 'OMIM_ID', 'PIR_SUMMARY', 'PROTEIN_MW',
                        'REFSEQ_PRODUCT', 'SEQUENCE_LENGTH'],\
        "categories_general_annotations_value":[],\
        "categories_functional_categories":['CGAP_EST_QUARTILE', 'CGAP_EST_RANK', 'COG_ONTOLOGY', 
                          'PIR_SEQ_FEATURE', 'SP_COMMENT_TYPE', 'SP_PIR_KEYWORDS'],\
        "categories_functional_categories_value":[],\
        "categories_protein_protein_interactions":['BIND', 'DIP', 'HIV_INTERACTION_CATEGORY', 
                                 'HIV_INTERACTION', 'MINT', 'NCICB_CAPATHWAY'],\
        "categories_protein_protein_interactions_value":[],\
        "categories_literature":['GENERIF_SUMMARY','HIV_INTERACTION_PUBMED_ID','PUBMED_ID'],\
        "categories_literature_value":[],\
        "categories_disease":['GENETIC_ASSOCIATION_DB_DISEASE', 'OMIM_DISEASE'],\
        "categories_disease_value":['OMIM_DISEASE'],\
        "user":"",\
        "ids":"Enter target genes here...",\
        "ids_bg":"Leave empty if you want to use all annotated genes for your organism",\
        "name":"target list",\
        "name_bg":"background list",\
        "p":"0.1",\
        "n":"2",\
        "download_format":["tsv","xlsx"],\
        "download_format_value":"xlsx",\
        "download_name":"DAVID",\
        "session_download_name":"MySession.DAVID",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.DAVID",\
        "inputargumentsfile":"Select file.."}

    return plot_arguments