from myapp import app
import pandas as pd
from myapp.routes.apps._utils import make_table
import json
from io import StringIO
from datetime import datetime
import os

PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)

path_to_files="/flaski_private/kegg/"

def read_compound_pathway(cache, path_to_files=path_to_files):
    @cache.memoize(60*60*2) 
    def _read_compound_pathway(path_to_files=path_to_files):
        df=pd.read_csv(f"{path_to_files}/compound_pathway.tsv", sep="\t", names=['compound_id', 'compound_name', 'pathways'])
        return df.to_json()
    return pd.read_json(StringIO(_read_compound_pathway()))

def read_pathway(cache, path_to_files=path_to_files):
    @cache.memoize(60*60*2) 
    def _read_pathway(path_to_files=path_to_files):
        df=pd.read_csv(f"{path_to_files}/pathway_list.tsv", sep="\t", names=['pathway_id', 'pathway_name'])
        return df.to_json()
    return pd.read_json(StringIO(_read_pathway()))

def compound_options(cache):
    compound_pathway_data=read_compound_pathway(cache)
    return [{'label': f"{cid}: {cname}", 'value': cid} for cid, cname in zip(compound_pathway_data['compound_id'], compound_pathway_data['compound_name'])]

def pathway_options(cache, compound_list):
    compound_pathway_data=read_compound_pathway(cache)
    pathway_data=read_pathway(cache)

    cp_row=compound_pathway_data[compound_pathway_data['compound_id'].isin(compound_list)]
    pathways_values = cp_row['pathways'].tolist()
    if not pathways_values or pathways_values==[None]:
        return None
    pathways_list = list(set([path.strip() for sublist in pathways_values for path in sublist.split(',')]))
    pw_rows = pathway_data[pathway_data['pathway_id'].isin(pathways_list)]
    
    return [{'label': f"{pid}: {pname}", 'value': pid} for pid, pname in zip(pw_rows['pathway_id'], pw_rows['pathway_name'])]

