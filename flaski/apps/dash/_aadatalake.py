import pandas as pd
# from flaski.routines import fuzzy_search


path_to_files="/flaski_private/aarnaseqlake/"

def read_results_files(cache,path_to_files=path_to_files):
    @cache.memoize(60*2) # 2 hours
    def _read_results_files(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"files2ids.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_results_files())

def read_gene_expression(cache,path_to_files=path_to_files):
    @cache.memoize(60*2)
    def _read_gene_expression(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"gene_expression.tsv",sep="\t",index_col=[0])
        return df.to_json()
    return pd.read_json(_read_gene_expression())

def read_genes(cache,path_to_files=path_to_files):
    @cache.memoize(60*2)
    def _read_genes(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"genes.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_genes())

def read_significant_genes(cache, path_to_files=path_to_files):
    @cache.memoize(60*2)
    def _read_significant_genes(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"significant.genes.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_significant_genes())


def filter_samples(data_sets, reps, groups, cache):
    results_files=read_results_files(cache)
    selected_results_files=results_files[ ( results_files['Set'].isin( data_sets ) ) & \
                                    ( results_files['Reps'].isin( reps ) ) & \
                                    ( results_files['Group'].isin( groups ) ) ]
    nsets=list(set(selected_results_files['Set']))
    if nsets > 1: 
        selected_results_files["Labels"]=selected_results_files["Set"]+"_"+selected_results_files["Reps"]
    else:
        selected_results_files["Labels"]=selected_results_files["Reps"]

    ids2labels=selected_results_files[["IDs","Labels"]].drop_duplicates()
    ids2labels.index=ids2labels["IDs"].tolist()
    ids2labels=ids2labels[["Labels"]].to_dict()["Labels"]

    return selected_results_files, ids2labels

def filter_genes(selected_gene_names, selected_gene_ids, cache):
    selected_genes=read_genes(cache)
    if selected_gene_names:
        selected_genes=selected_genes[ selected_genes["gene_name"].isin(selected_gene_names) ]
    if selected_gene_ids:
        selected_genes=selected_genes[ selected_genes["gene_id"].isin(selected_gene_ids) ]
    return selected_genes

def filter_gene_expression(ids2labels,selected_genes,cache):
    gedf=read_gene_expression(cache)
    selected_ge=gedf[list(ids2labels.keys())]
    selected_ge=selected_ge.astype(float)
    cols=selected_ge.columns.tolist()
    selected_ge["sum"]=selected_ge.sum(axis=1)
    selected_ge=selected_ge[selected_ge["sum"]>0]
    selected_ge=selected_ge.drop(["sum"],axis=1)
    selected_ge=pd.merge(selected_genes, selected_ge, left_on=["name_id"], right_index=True,how="left")
    selected_ge=selected_ge.dropna(subset=cols,how="all")
    selected_ge=selected_ge.drop(["name_id"],axis=1)
    selected_ge.reset_index(inplace=True,drop=True)
    selected_ge.rename(columns=ids2labels,inplace=True)

    return selected_ge






        

