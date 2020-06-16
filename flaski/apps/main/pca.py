from scipy import stats
from sklearn import preprocessing
from sklearn.decomposition import PCA
import pandas as pd
import math


def make_figure(df,pa):
    df_pca=df.copy()
    df_pca.index=df_pca[pa["xvals"]].tolist()
    df_pca=df_pca[pa["yvals"]]
    df_pca=df_pca.T

    #if pa["zscore_value"] == "row":
    #    df_pca=pd.DataFrame(stats.zscore(df_pca, axis=1, ddof=1),columns=df_pca.columns.tolist(), index=df_pca.index.tolist())
    #elif pa["zscore_value"] == "columns":
    #    df_pca=pd.DataFrame(stats.zscore(df_pca, axis=0, ddof=1),columns=df_pca.columns.tolist(), index=df_pca.index.tolist())

    pca = PCA(copy=True, iterated_power='auto', n_components=int(pa["ncomponents"]), random_state=None, svd_solver='auto', tol=0.0, whiten=False)
    if pa["scale"] in [".on","on"]:
        df_pca_scaled = preprocessing.scale(df_pca)
    else:
        df_pca_scaled = df_pca.as_matrix()
    projected=pca.fit_transform(df_pca_scaled)

    def get_important_features(transformed_features, components_, columns):
        """
        This function will return the most "important" 
        features so we can determine which have the most
        effect on multi-dimensional scaling
        """
        num_columns = len(columns)

        components_=pd.DataFrame(components_)
        components_=components_.T

        for c in components_.columns.tolist():
            components_[c]=components_[c]*max(transformed_features[:,c])
        
        cols=components_.columns.tolist()
        cols=["c"+str(c+1) for c in cols ]
        components_.columns=cols
        components_.index=columns

        def calc_feature(df,c1,c2):
            val1=df[c1]
            val2=df[c2]
            val=math.sqrt(val1**2 + val2**2)
            return val

        for c in cols:
            vals=components_[c].tolist()
            vals=[min(vals),max(vals)]
            components_.loc[ components_[c].isin(vals) , "key "+c] = "yes"

        sort_by=[]
        ready_features=[]
        for c1 in cols:
            for c2 in cols:
                if c1 != c2:
                    if  ( [c1, c2] not in ready_features ) & ( [c2, c1] not in ready_features ):
                        components_[c1+"x"+c2]=components_.apply(calc_feature, args=(c1,c2) ,axis=1 )
                        sort_by.append(c1+"x"+c2)
                        ready_features.append([c1, c2])

        components_=components_.sort_values(by=sort_by,ascending=False) 
        components_.reset_index(inplace=True, drop=False)
        cols=components_.columns.tolist()
        cols[0]="row"
        components_.columns=cols
        # print(components_.head())           

        # # Scale the principal components by the max value in
        # # the transformed set belonging to that component
        # xvector = components_[0] * max(transformed_features[:,0])
        # yvector = components_[1] * max(transformed_features[:,1])

        # # Sort each column by it's length. These are your *original*
        # # columns, not the principal components.
        # important_features = { columns[i] : math.sqrt(xvector[i]**2 + yvector[i]**2) for i in range(num_columns) }
        # important_features = sorted(zip(important_features.values(), important_features.keys()), reverse=True)
        # return important_features,xvector,yvector
        return components_

    #important_features,xvector,yvector=get_important_features(projected, pca.components_, df_pca.columns.values)

    features=get_important_features(projected, pca.components_, df_pca.columns.values)

    #print(important_features[:10], xvector[:10])

    projected=pd.DataFrame(projected)
    cols=projected.columns.tolist()
    cols=[ "Component "+str(c+1)+" - "+str(pca.explained_variance_ratio_[c]*100)+"%" for c in cols ]
    projected.columns=cols
    projected.index=df_pca.index.tolist()
    projected.reset_index(inplace=True, drop=False)
    projected.columns=["row"]+cols

    #components = pd.DataFrame(pca.components_, columns = df_pca.columns, index=[ s+1 for s in range(len(pca.components_)) ])

    return projected, features

def figure_defaults():
    """Generates default figure arguments.

    Returns:
        dict: A dictionary of the style { "argument":"value"}
    """
    plot_arguments={
        "xcols":[],\
        "xvals":"",\
        "ycols":[],\
        "yvals":"",\
        "ncomponents":"2",\
        "percvar":"100",\
        "scale":".on",\
        "download_format":["tsv","xlsx"],\
        "downloadf":"xlsx",\
        "downloadn":"PCA",\
        "session_downloadn":"MySession.PCA",\
        "inputsessionfile":"Select file..",\
        "session_argumentsn":"MyArguments.PCA",\
        "inputargumentsfile":"Select file.."}

    return plot_arguments