#!/usr/bin/env python
# Copyright 2023 Jing-Hui Tong, Data Center, President Information Corporation
#
# This file is part of Clustering.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -*- coding: utf-8 -*-
"""

The codes mainly refer from 
https://github.com/smazzanti/are_you_still_using_elbow_method/blob/main/are-you-still-using-elbow-method.ipynb

"""
import pandas as pd
import numpy as np
import datetime, math
import os, warnings
from collections import defaultdict
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import sklearn.metrics as sklearn_metrics
from sklearn_extra.cluster import KMedoids
from kmodes.kprototypes import KPrototypes
from kmodes.kmodes import KModes
from sklearn.metrics import silhouette_score
from kneed import KneeLocator
warnings.filterwarnings("ignore")



def calinski_harabasz_score(X, labels):
    """
    
    Wrapper function of Scikit-learn's calinski_harabasz_score. 
    The only difference is it doesn't throw an error where there is only one label.
    
    """
    if len(set(labels)) == 1:
        return float("NaN")
    else:
        return sklearn_metrics.calinski_harabasz_score(X, labels)


def davies_bouldin_score(X, labels):
    """
    
    Wrapper function of Scikit-learn's davies_bouldin_score. 
    The only difference is it doesn't throw an error where there is only one label.
    
    """
    if len(set(labels)) == 1:
        return float("NaN")
    else:
        return sklearn_metrics.davies_bouldin_score(X, labels)


def silhouette_score(X, labels):
    """
    
    Wrapper function of Scikit-learn's silhouette_score. 
    The only difference is it doesn't throw an error where there is only one label.
    
    Note: This algorithm spends a looooooot of time. 
    
    """
    if len(set(labels)) == 1:
        return float("NaN")
    else:
        return sklearn_metrics.silhouette_score(X, labels)


def bic_score(X: np.ndarray, labels: np.array):
    """
    
    BIC score for the goodness of fit of clusters.
    This Python function is translated from the Golang implementation by the author of the paper. 
    The original code is available here: 
        https://github.com/bobhancock/goxmeans/blob/a78e909e374c6f97ddd04a239658c7c5b7365e5c/km.go#L778
    
    Note: This algorithm spends a looooooot of time. 
    
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


def find_best_cluster(method, df, pma, savedir, object_position, selectMethod, Gmin=5, Gmax=20, weight=None, verbose=False):
    """
    
    Automatically find the best number of groups 

    Parameters
    ----------
    method : str
        Specify clustering algorithm
    df : :class:`~pandas.DataFrame`
        Data processed for analyzed
    pma : int
        Specify number of pma
    savedir : int
        Path of saving grid-search results as a figure      
    object_position : list
        The object postion derived from main program (L66)
    selectMethod : str
        Specify method algorithm to decide clustering numbers
    Gmin : int
        Specify the minimum group of grid search. [Default is 5]
    Gmax : int
        Specify the maximum group of grid search. [Default is 20]
    weight : str
        If method = "WKMeans", specify the column as weighting factor 
    verbose : boolean
        Verbosity

    Returns
    -------
    num : int
        The best number of groups
    
    """
    
    # Bounds on search
    range_cluster = range(Gmin, Gmax+1)

    
    if verbose:
        print("|"+"="*50+"|")
        print("|"+" "*4+"Automatically find the best number of group"+" "*3+"|")
        print("|"+"-"*50+"|")
        print("*"*5+" "*5+"Clustering method: "+method)
        print("*"*5+" "*5+"The method to choose : "+selectMethod)
        
    ### begin to do grid-search     
    scores = defaultdict(list)    
    bestscores = defaultdict(list)  
     
    # KMeans refers from :
    # https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html#sklearn.cluster.KMeans
    if method == "KMeans":
        for n_clusters in range_cluster:
            if verbose:
                print("*"*5+" "*5+"For loop .... "+str(n_clusters))
            km = KMeans(n_clusters=n_clusters,  random_state=50)
            labels = km.fit_predict(df)
            
            scores["elbow"].append(km.inertia_)
            scores["calinski-harabasz"].append(calinski_harabasz_score(df, labels))
            scores["davies-bouldin"].append(davies_bouldin_score(df, labels))
            if selectMethod == 'silhouette':
                scores["silhouette"].append(silhouette_score(df, labels))
            # scores["bic"].append(bic_score(np.array(df), labels))

    # KMedoids refers from :
    # https://scikit-learn-extra.readthedocs.io/en/stable/generated/sklearn_extra.cluster.KMedoids.html 
    elif method == "KMedoids":
        for n_clusters in range_cluster:
            if verbose:
                print("*"*5+" "*5+"For loop .... "+str(n_clusters))
            km = KMedoids(n_clusters=n_clusters, random_state=50, max_iter = 10, n_jobs=-1,)
            labels = km.fit_predict(df)
            
            scores["elbow"].append(km.inertia_)
            scores["calinski-harabasz"].append(calinski_harabasz_score(df, labels))
            scores["davies-bouldin"].append(davies_bouldin_score(df, labels))
            if selectMethod == 'silhouette':
                scores["silhouette"].append(silhouette_score(df, labels))
            # scores["bic"].append(bic_score(np.array(df), labels))

    # KPrototypes refers from :
    # https://github.com/nicodv/kmodes/blob/master/kmodes/kprototypes.py    
    elif  method == "KPrototypes":
        for n_clusters in range_cluster:
            if verbose:
                print("*"*5+" "*5+"For loop .... "+str(n_clusters))
            kproto = KPrototypes(n_clusters=n_clusters, init="Huang", max_iter=10,  random_state=50, n_jobs=-1)
            labels = kproto.fit_predict(df.to_numpy(), categorical=object_position)
            
            scores["elbow"].append(kproto.cost_)
            scores["calinski-harabasz"].append(calinski_harabasz_score(df, labels))
            scores["davies-bouldin"].append(davies_bouldin_score(df, labels))
            if selectMethod == 'silhouette':
                scores["silhouette"].append(silhouette_score(df, labels))
            # scores["bic"].append(bic_score(np.array(df), labels))
   
    # KModes refers from :
    # https://github.com/nicodv/kmodes/blob/master/kmodes/kmodes.py        
    elif method == "KModes":
        for n_clusters in range_cluster:
            if verbose:
                print("*"*5+" "*5+"For loop .... "+str(n_clusters))
            kmodes = KModes(n_clusters=n_clusters, init = "Huang", random_state=50, max_iter=10, n_init=3)
            labels = kmodes.fit_predict(df)
            
            scores["elbow"].append(kmodes.cost_)
            scores["calinski-harabasz"].append(calinski_harabasz_score(df, labels))
            scores["davies-bouldin"].append(davies_bouldin_score(df, labels))
            if selectMethod == 'silhouette':
                scores["silhouette"].append(silhouette_score(df, labels))
            # scores["bic"].append(bic_score(np.array(df), labels))

    # WKMeans refers from :
    # https://stackoverflow.com/questions/50789660/weighted-k-means-in-python
    # https://zerowithdot.com/weighted-k-means-clustering-example/             
    elif method == "WKMeans":
        for n_clusters in range_cluster:
            if verbose:
                print("*"*5+" "*5+"For loop .... "+str(n_clusters))
            km = KMeans(n_clusters=n_clusters,  random_state=50)
            labels = km.fit_predict(df, sample_weight = df[weight])
            
            scores["elbow"].append(km.inertia_)
            scores["calinski-harabasz"].append(calinski_harabasz_score(df, labels))
            scores["davies-bouldin"].append(davies_bouldin_score(df, labels))
            if selectMethod == 'silhouette':
                scores["silhouette"].append(silhouette_score(df, labels))
            # scores["bic"].append(bic_score(np.array(df), labels))

    ### find best scores 
    bestscores["elbow"].append(KneeLocator(range_cluster,scores["elbow"], curve="convex", direction="decreasing").knee)
    bestscores["calinski-harabasz"].append(range_cluster[np.nanargmax(scores["calinski-harabasz"])])
    bestscores["davies-bouldin"].append(range_cluster[np.nanargmin(scores["davies-bouldin"])])
    if selectMethod == 'silhouette':
        bestscores["silhouette"].append(range_cluster[np.nanargmax(scores["silhouette"])])
    # bestscores["bic"].append(range_cluster[np.nanargmax(scores["bic"])])

    ### Figure handle
    fig, axs = plt.subplots(len(bestscores.keys()), 1, figsize=(6,10))
        
    for m, automethod in enumerate(bestscores.keys()):
        # plot grid search results
        axs[m].scatter(range_cluster, scores[automethod], color="k")
        axs[m].text(range_cluster[-1], max(scores[automethod]), s=automethod, ha="right", va="top")
        # plot best score
        axs[m].scatter(bestscores[automethod], scores[automethod][bestscores[automethod][0]-Gmin], \
                        color="r", marker="*")
        axs[m].set_xticks(range_cluster)
        axs[m].set_xticklabels(size = 9, labels = range_cluster)
        axs[m].set_yticklabels(size = 9, labels = [])
    
    plt.savefig(f"{savedir}/pma_{pma}_{method}_auto_cluster.png", dpi = 150, bbox_inches="tight")
    plt.close()
    
    num = bestscores[selectMethod][0]
    
    if verbose:
        print("*"*5+" "*5+"The best number of cluster : "+str(num))
        print("*"*5+" "*5+"The analysis result path : "+savedir)
        print("|"+"="*50+"|")
    

    return num