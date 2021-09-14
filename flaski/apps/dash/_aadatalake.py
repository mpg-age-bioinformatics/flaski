import pandas as pd
# from flaski.routines import fuzzy_search


path_to_files="/flaski_private/aarnaseqlake/"

def read_results_files(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2) # 2 hours
    def _read_results_files(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"files2ids.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_results_files())

def read_gene_expression(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2)
    def _read_gene_expression(path_to_files=path_to_files):
        print("GE!!!")
        import sys
        sys.stdout.flush()
        df=pd.read_csv(path_to_files+"gene_expression.tsv",sep="\t",index_col=[0])
        return df.to_json()
    return pd.read_json(_read_gene_expression())

def read_genes(cache,path_to_files=path_to_files):
    @cache.memoize(60*60*2)
    def _read_genes(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"genes.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_genes())

def read_significant_genes(cache, path_to_files=path_to_files):
    @cache.memoize(60*60*2)
    def _read_significant_genes(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"significant.genes.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_significant_genes())


def nFormat(x):
    if float(x) == 0:
        return str(x)
    elif ( float(x) < 0.01 ) & ( float(x) > -0.01 ) :
        return str('{:.3e}'.format(float(x)))
    else:
        return str('{:.3f}'.format(float(x)))

def filter_samples(datasets=None, reps=None, groups=None, cache=None):
    results_files=read_results_files(cache)

    # print(datasets)
    # import sys
    # sys.stdout.flush()

    if datasets:
        results_files=results_files[ results_files['Set'].isin( datasets ) ]

    if reps:
        results_files=results_files[ results_files['Reps'].isin( reps ) ]

    if groups:
        results_files=results_files[ results_files['Group'].isin( groups ) ]

    nsets=len(list(set(results_files['Set'])))
    if nsets > 1: 
        results_files["Labels"]=results_files["Set"]+"_"+results_files["Reps"]
    else:
        results_files["Labels"]=results_files["Reps"]

    ids2labels=results_files[["IDs","Labels"]].drop_duplicates()
    ids2labels.index=ids2labels["IDs"].tolist()
    ids2labels=ids2labels[["Labels"]].to_dict()["Labels"]

    return results_files, ids2labels

def filter_genes(selected_gene_names, selected_gene_ids, cache):
    selected_genes=read_genes(cache)
    if selected_gene_names:
        selected_genes=selected_genes[ selected_genes["gene_name"].isin(selected_gene_names) ]
    if selected_gene_ids:
        selected_genes=selected_genes[ selected_genes["gene_id"].isin(selected_gene_ids) ]
    return selected_genes

def filter_gene_expression(ids2labels, selected_gene_names, selected_gene_ids, cache):
    @cache.memoize(60*60*2)
    def _filter_gene_expression(ids2labels, selected_gene_names, selected_gene_ids):
        gedf=read_gene_expression(cache)
        selected_genes=filter_genes(selected_gene_names, selected_gene_ids, cache)
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
        for c in selected_ge.columns.tolist()[2:]:
            selected_ge[c]=selected_ge[c].apply(lambda x: nFormat(x) )
        rename=selected_ge.columns.tolist()[2:]
        rename=[ s.replace("_", " ")  for s in rename ]
        rename=selected_ge.columns.tolist()[:2]+rename
        selected_ge.columns=rename
        return selected_ge.to_json()
    return pd.read_json(_filter_gene_expression(ids2labels, selected_gene_names, selected_gene_ids))

# def read_metadata():
def read_metadata(cache,path_to_files=path_to_files):
    # @cache.memoize(60*60*2) # 2 hours
    def _read_metadata(path_to_files=path_to_files):
        df=pd.read_csv(path_to_files+"metadata.tsv",sep="\t")
        return df.to_json()
    return pd.read_json(_read_metadata())

def read_dge(dataset, groups, cache, out="html",path_to_files=path_to_files):
    # @cache.memoize(60*60*2) # 2 hours
    def _read_dge(dataset,groups,cache, out, path_to_files=path_to_files):
        metadata=read_metadata(cache)
        # print(metadata.head(),dataset,groups )
        metadata=metadata[ (metadata["Set"] == dataset ) & \
            (metadata["Group_1"].isin(groups) ) & \
            (metadata["Group_2"].isin(groups) ) ]
        dge_file=metadata["File"].tolist()[0]
        selected_dge=pd.read_csv(path_to_files+"pairwise/"+dge_file,sep="\t")
        selected_dge["padj"]=selected_dge["padj"].astype(float)
        selected_dge=selected_dge.sort_values(by=["padj"],ascending=True)
        cols=selected_dge.columns.tolist()
        if out == "html":
            for c in cols[2:]:
                selected_dge[c]=selected_dge[c].apply(lambda x: nFormat(x) )
        cols=[ s.replace("_", " ") for s in cols ]
        selected_dge.columns=cols
        mapcols={"baseMean":"base Mean","log2FoldChange":"log2 FC","lfcSE":"lfc SE","pvalue":"p value"}
        selected_dge=selected_dge.rename(columns=mapcols)
        return selected_dge.to_json()
    return pd.read_json(_read_dge(dataset,groups,cache,out=out))





        

