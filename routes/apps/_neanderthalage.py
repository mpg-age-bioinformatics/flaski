import os
import pandas as pd
import matplotlib.pyplot as plt

path_to_files="/flaski_private/neanderthalage/"

def read_agegene(cache, path_to_files=path_to_files):  #cache
    #@cache.memoize(60*60*2) # 2 hours
    def _read_agegene(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"age.gene.altai_20240625.tsv",sep="\t", dtype=str)
        return df.to_json(orient='records', default_handler=str )
    return pd.read_json(_read_agegene(), dtype=str)


def read_drug(cache,path_to_files=path_to_files):
    #@cache.memoize(60*60*2) # 2 hours
    def _read_drug(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"drug.masterTable_20240702.tsv",sep="\t", dtype=str)
        return df.to_json(orient='records', default_handler=str )
    return pd.read_json(_read_drug(), dtype=str)


def read_agedist(cache,path_to_files=path_to_files):
    #@cache.memoize(60*60*2) # 2 hours
    def _read_agedist(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"mutation_age_distribution_20240625.tsv",sep="\t", dtype=str)
        return df.to_json(orient='records', default_handler=str )
    return pd.read_json(_read_agedist(), dtype=str)





