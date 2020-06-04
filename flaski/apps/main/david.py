import pandas as pd
import sys
from suds.client import Client as sudsclient
import ssl

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

def run_david(pa):
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
      ids_bg=None
    name=pa["name"]
    if ids_bg is not None:
      name_bg=pa["name_bg"]
    else:
      name_bg=""

    p=pa["p"]
    n=pa["n"]    
    #, categories, user, ids, ids_bg = None, name = '', name_bg = '', verbose = False, p = 0.1, n = 2

    verbose=True
    ids = ','.join([str(i) for i in ids])
    use_bg = 0

    if ids_bg is not None:
      ids_bg = ','.join([str(i) for i in ids_bg])
    ssl._create_default_https_context = ssl._create_unverified_context
    url = 'https://david.ncifcrf.gov/webservice/services/DAVIDWebService?wsdl'
    client = sudsclient(url)
    client.wsdl.services[0].setlocation('https://david.ncifcrf.gov/webservice/services/DAVIDWebService.DAVIDWebServiceHttpSoap11Endpoint/')
    client_auth = client.service.authenticate(user)
    
    if str(client_auth) == "Failed. For user registration, go to http://david.abcc.ncifcrf.gov/webservice/register.htm" :
      return None, None
      
    if verbose:
      print('User Authentication:', client_auth)
      sys.stdout.flush()
    size = client.service.addList(ids, database, name, 0) #| inputListIds,idType,listName,listType)
    report_stats=[['Mapping rate of ids: ', str(size)]]
    if verbose:
      print('Mapping rate of ids: ', str(size))
      sys.stdout.flush()
    if not float(size) > float(0):
      return None
    if ids_bg is not None:
      size_bg = client.service.addList(ids_bg, database, name_bg, 1)
      report_stats.append(['Mapping rate of background ids: ', str(size_bg)])
      if verbose:
        print('Mapping rate of background ids: ', str(size_bg))
        sys.stdout.flush()
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
        if len(list(ids_map.keys())) > 0:
          def get_map(x,ids_map):
            genes=x.split(", ")
            genes=[ str(ids_map[gene.upper()]) for gene in genes ]
            genes=", ".join(genes)
            return genes
          for annotation in list(ids_map.keys()):
            genes_to_annotation=ids_map[annotation]
            df["annotation_%s" %str(annotation)]=df["Genes"].apply(lambda x:get_map(x,ids_map=genes_to_annotation) )
    else:
        df=pd.DataFrame()
    report_stats=pd.DataFrame(report_stats,columns=["Field","Value"])

    return df, report_stats

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

    plot_arguments={
        "database":['AFFYMETRIX_3PRIME_IVT_ID', 'AFFYMETRIX_EXON_GENE_ID',
          'AFFYMETRIX_SNP_ID', 'AGILENT_CHIP_ID',
          'AGILENT_ID', 'AGILENT_OLIGO_ID',
          'ENSEMBL_GENE_ID', 'ENSEMBL_TRANSCRIPT_ID',
          'ENTREZ_GENE_ID', 'FLYBASE_GENE_ID',
          'FLYBASE_TRANSCRIPT_ID','GENBANK_ACCESSION',
          'GENPEPT_ACCESSION', 'GENOMIC_GI_ACCESSION',
          'PROTEIN_GI_ACCESSION', 'ILLUMINA_ID',
          'IPI_ID', 'MGI_ID', 'GENE_SYMBOL', 'PFAM_ID',
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