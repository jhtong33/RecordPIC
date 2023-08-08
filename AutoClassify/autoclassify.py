import pandas as pd
import numpy as np
import datetime, math
import sys, os, warnings
from kmodes.kprototypes import KPrototypes
from sklearn.metrics import silhouette_score
from sklearn.cluster import KMeans
from kmodes.kmodes import KModes
from sklearn_extra.cluster import KMedoids
import matplotlib.pyplot as plt
import sklearn.metrics as sklearn_metrics
from kneed import KneeLocator
from collections import defaultdict

"""
The code comes from 
https://github.com/smazzanti/are_you_still_using_elbow_method/blob/main/are-you-still-using-elbow-method.ipynb
"""


def calinski_harabasz_score(X, labels):
    """Wrapper function of Scikit-learn's calinski_harabasz_score. 
    The only difference is it doesn't throw an error where there is only one label."""
    if len(set(labels)) == 1:
        return float("NaN")
    else:
        return sklearn_metrics.calinski_harabasz_score(X, labels)


def davies_bouldin_score(X, labels):
    """Wrapper function of Scikit-learn's davies_bouldin_score. 
    The only difference is it doesn't throw an error where there is only one label."""
    if len(set(labels)) == 1:
        return float("NaN")
    else:
        return sklearn_metrics.davies_bouldin_score(X, labels)


def silhouette_score(X, labels):
    """Wrapper function of Scikit-learn's silhouette_score. 
    The only difference is it doesn't throw an error where there is only one label."""
    if len(set(labels)) == 1:
        return float("NaN")
    else:
        return sklearn_metrics.silhouette_score(X, labels)


def bic_score(X: np.ndarray, labels: np.array):
    """
      BIC score for the goodness of fit of clusters.
      This Python function is translated from the Golang implementation by the author of the paper. 
      The original code is available here: https://github.com/bobhancock/goxmeans/blob/a78e909e374c6f97ddd04a239658c7c5b7365e5c/km.go#L778
    """
    n_points = len(labels)
    n_clusters = len(set(labels))
    n_dimensions = X.shape[1]
    n_parameters = (n_clusters - 1) + (n_dimensions * n_clusters) + 1
    loglikelihood = 0
    for label_name in set(labels):
        X_cluster = X[labels == label_name]
        n_points_cluster = len(X_cluster)
        if n_points_cluster == 1:
            return float("NaN")
        else:
            centroid = np.mean(X_cluster, axis=0)
            variance = np.sum((X_cluster - centroid) ** 2) / (len(X_cluster) - 1)
            loglikelihood += n_points_cluster * np.log(n_points_cluster) \
                  - n_points_cluster * np.log(n_points) \
                  - n_points_cluster * n_dimensions / 2 * np.log(2 * math.pi * variance) \
                  - (n_points_cluster - 1) / 2

            bic = loglikelihood - (n_parameters / 2) * np.log(n_points)
            return bic

def find_best_cluster(method, df_4cluster, pma, savedir, catobj_Pos, selectMethod, Gmin=5, Gmax=20, weight=None, verbose=False):
    range_cluster = range(Gmin, Gmax+1)
    fig, axs = plt.subplots(3, 1, figsize=(6,10))
    if verbose:
        print("|"+"="*50+"|")
        print("|"+" "*4+"Automatically find the best number of group"+" "*3+"|")
        print("|"+"-"*50+"|")
        print("*"*5+" "*5+"Clustering method: "+method)
        print("*"*5+" "*5+"The method to choose : "+selectMethod)
        
    scores = defaultdict(list)    
    bestscores = defaultdict(list)    
    
    if method.casefold() == "KMeans".casefold():
        for n_clusters in range_cluster:
            if verbose:
                print("*"*5+" "*5+"For loop .... "+str(n_clusters))
            km = KMeans(n_clusters=n_clusters,  random_state=50)
            labels = km.fit_predict(df_4cluster)
            scores["elbow"].append(km.inertia_)
            scores["calinski-harabasz"].append(calinski_harabasz_score(df_4cluster, labels))
            scores["davies-bouldin"].append(davies_bouldin_score(df_4cluster, labels))
            scores["silhouette"].append(silhouette_score(df_4cluster, labels))
            # scores["bic"].append(bic_score(np.array(df_4cluster), labels))
    elif method.casefold() == "KMedoids".casefold():
        for n_clusters in range_cluster:
            if verbose:
                print("*"*5+" "*5+"For loop .... "+str(n_clusters))
            km = KMedoids(n_clusters=n_clusters, random_state=50, max_iter = 10, n_jobs=-1,)
            labels = km.fit_predict(df_4cluster)
            scores["elbow"].append(km.inertia_)
            scores["calinski-harabasz"].append(calinski_harabasz_score(df_4cluster, labels))
            scores["davies-bouldin"].append(davies_bouldin_score(df_4cluster, labels))
            scores["silhouette"].append(silhouette_score(df_4cluster, labels))
            # scores["bic"].append(bic_score(np.array(df_4cluster), labels))

    elif  method.casefold() == "KPrototypes".casefold():
        for n_clusters in range_cluster:
            if verbose:
                print("*"*5+" "*5+"For loop .... "+str(n_clusters))
            kproto = KPrototypes(n_clusters=n_clusters, init="Huang", max_iter=10,  random_state=50, n_jobs=-1)
            labels = kproto.fit_predict(df_4cluster.to_numpy(), categorical=catobj_Pos)
            scores["elbow"].append(kproto.cost_)
            scores["calinski-harabasz"].append(calinski_harabasz_score(df_4cluster, labels))
            scores["davies-bouldin"].append(davies_bouldin_score(df_4cluster, labels))
            scores["silhouette"].append(silhouette_score(df_4cluster, labels))
            # scores["bic"].append(bic_score(np.array(df_4cluster), labels))
            
    elif method.casefold() == "KModes".casefold():
        for n_clusters in range_cluster:
            if verbose:
                print("*"*5+" "*5+"For loop .... "+str(n_clusters))
            kmodes = KModes(n_clusters=n_clusters, init = "Huang", random_state=50, max_iter=10, n_init=3)
            labels = kmodes.fit_predict(df_4cluster)
            scores["elbow"].append(kmodes.cost_)
            scores["calinski-harabasz"].append(calinski_harabasz_score(df_4cluster, labels))
            scores["davies-bouldin"].append(davies_bouldin_score(df_4cluster, labels))
            scores["silhouette"].append(silhouette_score(df_4cluster, labels))
            # scores["bic"].append(bic_score(np.array(df_4cluster), labels))
    elif method.casefold() == "WKMeans".casefold():
        for n_clusters in range_cluster:
            if verbose:
                print("*"*5+" "*5+"For loop .... "+str(n_clusters))
            km = KMeans(n_clusters=n_clusters,  random_state=50)
            labels = km.fit_predict(df_4cluster, sample_weight = df_4cluster[weight])
            scores["elbow"].append(km.inertia_)
            scores["calinski-harabasz"].append(calinski_harabasz_score(df_4cluster, labels))
            scores["davies-bouldin"].append(davies_bouldin_score(df_4cluster, labels))
            scores["silhouette"].append(silhouette_score(df_4cluster, labels))
            # scores["bic"].append(bic_score(np.array(df_4cluster), labels))

            
    bestscores["elbow"].append(KneeLocator(range_cluster,scores["elbow"], curve="convex", direction="decreasing").knee)
    bestscores["calinski-harabasz"].append(range_cluster[np.nanargmax(scores["calinski-harabasz"])])
    bestscores["davies-bouldin"].append(range_cluster[np.nanargmin(scores["davies-bouldin"])])
    bestscores["silhouette"].append(range_cluster[np.nanargmax(scores["silhouette"])])
    # bestscores["bic"].append(range_cluster[np.nanargmax(scores["bic"])])

    for m, automethod in enumerate(bestscores.keys()):
        axs[m].scatter(range_cluster, scores[automethod], color="k")
        axs[m].text(range_cluster[-1], max(scores[automethod]), s=automethod, ha="right", va="top")
        axs[m].scatter(bestscores[automethod], scores[automethod][bestscores[automethod][0]-Gmin], color="r", marker="*")
        axs[m].set_xticks(range_cluster)
        axs[m].set_xticklabels(size=9, labels=range_cluster)
        axs[m].set_yticklabels(size=9, labels=[])
    
    numofCluster = bestscores[selectMethod][0]
    if verbose:
        print("*"*5+" "*5+"The best number of cluster : "+str(numofCluster))
        print("*"*5+" "*5+"The analysis result path : "+savedir)
        print("|"+"="*50+"|")
    plt.savefig(f"{savedir}/pma_{pma}_{method}_auto_cluster.png", dpi = 150, bbox_inches="tight")
    plt.close()
    return numofCluster