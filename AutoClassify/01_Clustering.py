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
import pandas as pd
import numpy as np
import datetime
import os, warnings
from kmodes.kprototypes import KPrototypes
from kmodes.kmodes import KModes
from sklearn.cluster import KMeans
from sklearn_extra.cluster import KMedoids
from arguments import get_arguments
from preprocess import processing
from autoclassify import find_best_cluster
from output import plot_values, plot_object, output_log
warnings.filterwarnings("ignore")



def main():
    args = get_arguments()
    starttime = datetime.datetime.now()

    print()
    print("|"+"="*50+"|")
    print("|                Executing Program                 |")
    print("|"+"="*50+"|")
        
    #===========================================
    ### data clean
    df_preprocess, readcols, objectencoder = processing(args.category_path, args.category, args.filename, args.pma, \
                                                       args.rfm_level, args.select_rfm, args.select_two, args.verb)
    
    # remove mid, pma, rfm to cluster
    df_4cluster = df_preprocess.copy()
    if args.category is not None  and "rfm" in args.category:
        df_4cluster = df_4cluster.drop(["mid", "pma_no_fin", "rfm_recency", "rfm_frequency", "rfm_monetary"], axis = 1) 
    else:
        df_4cluster = df_4cluster.drop(["mid", "pma_no_fin"], axis = 1) 
    
    # get object columns and position
    catobj_Name = list(df_4cluster.select_dtypes("object").columns)
    catobj_Pos = [df_4cluster.columns.get_loc(col) for col in list(df_4cluster.select_dtypes("object").columns)]

    #===========================================
    ### mkdir      
    savedir = f"{args.savepath}/PMA-{args.pma}"
    
    # make and move directories
    if not os.path.isdir(savedir):
        os.makedirs(savedir)
        if args.verb:
            print("|"+"="*50+"|")
            print("|"+" "*9+"Create directory to save result"+" "*9+"|")
            print("|"+"-"*50+"|")  
            print("*"*5+" "*5+"path: "+savedir)
    else:
        if not args.ovr:
            gettime = os.path.getctime(savedir)
            datetimeObj = datetime.datetime.fromtimestamp(gettime)
            dateStr = datetimeObj.strftime("%Y%m%d_%H%M%S")
            os.makedirs(f"{savedir}/{dateStr}")
            
            #command line
            cmd = """
            mv %(savedir)s/Group* %(savedir)s/%(dateStr)s
            mv %(savedir)s/*.log %(savedir)s/%(dateStr)s
            mv %(savedir)s/*.png %(savedir)s/%(dateStr)s
            """%locals()
            os.system(cmd)
        
    #===========================================
    
    ### Find the best number of cluster
    if args.AutoCluster:
        numofCluster = find_best_cluster(args.method, df_4cluster, args.pma, savedir, catobj_Pos, \
                                        args.selectMethod, Gmin=args.Gmin, Gmax=args.Gmax, \
                                        weight=args.weight, verbose = args.verb)
    else:
        numofCluster = args.numofCluster
        if args.verb:
            print("|"+"="*50+"|")
            print("|"+" "*6+"Manually specify the number of group  "+" "*6+"|")
            print("|"+"-"*50+"|")
            print("*"*5+" "*5+"The number of cluster : " + str(numofCluster))
            print("|"+"="*50+"|")
            
    #===========================================
    ### Begining to classify 
    if args.verb:
        print("|"+"="*50+"|")
        print("|               Begining to classify               |")
        print("|"+"="*50+"|")
    
    df_label = df_preprocess.copy()
    
    # based on method
    if args.method == "KMeans":
        model_kmean = KMeans(n_clusters=numofCluster, random_state=50, max_iter = 100)
        result = model_kmean.fit(df_4cluster)
        df_label["label"] = result.labels_
        
    elif args.method == "WKMeans":
        model_kmean = KMeans(n_clusters=numofCluster, random_state=50, max_iter = 100)
        result = model_kmean.fit(df_4cluster, sample_weight = df_4cluster[args.weight])
        df_label["label"] = result.labels_    
        
    elif args.method == "KPrototypes":
        model_kproto = KPrototypes(n_clusters=numofCluster, init="Huang", random_state=50, n_jobs=-1, max_iter = 100)
        df_label["label"] = model_kproto.fit_predict(df_4cluster.to_numpy(), categorical=catobj_Pos)
        
    elif args.method == "KMedoids":    
        model_kmedoids = KMedoids(n_clusters=numofCluster, random_state=50, max_iter = 100)
        result = model_kmedoids.fit(df_4cluster)
        df_label["label"] = result.labels_
        
    elif args.method == "KModes":   
        model_kmodes = KModes(n_clusters=numofCluster, random_state=50, n_jobs=-1, max_iter = 100)
        result = model_kmodes.fit(df_4cluster)
        df_label["label"] = result.labels_

    #===========================================
    ### Save overall results
    # specify log filename 
    logfile = f"{savedir}/pma_{args.pma}.log"
    
    # export log file (pma_??.log) to record the setting 
    output_log(logfile, df_label, starttime, args.pma, args.category, args.AutoCluster, args.method, args.selectMethod, numofCluster)
    
    # save figure (pma_??_Overall.png) with "values"
    plot_key = readcols["key"][readcols["fmt"]=="values"].tolist()
    plot_values(df_label, savedir, args.pma, numofCluster, plot_key, args.pmapath)

    #===========================================
    ### Save results of each group 
    for i in range(numofCluster):
        
        str_group = str(i).zfill(2)
        
        # specify folder 
        savegroupdir = f"{savedir}/Group_{str_group}"
        if not os.path.isdir(savegroupdir):
            os.makedirs(savegroupdir)
        
        df_group = df_label[df_label["label"]==i]
        
        # reverse label encoder
        for objkey in readcols["key"][readcols["fmt"]=="object"]:
            try:
                if "area" not in objkey:
                    df_group[objkey] =objectencoder[objkey][0].inverse_transform(df_group[objkey].astype(int))
            except:
                pass
        if "rfm_level" in df_group.keys():
            df_group["rfm_level"] = objectencoder["rfm"][0].inverse_transform(df_group["rfm_level"].astype(int))
        
        
        # save descriptive statistics of each column
        df_group_describe = df_group.describe()
        df_group_describe = df_group_describe.drop(labels="count")
        df_group_describe = df_group_describe.drop(columns="label")
        df_group_describe = df_group_describe.drop(columns="pma_no_fin")
        df_group_describe.to_csv(f"{savegroupdir}/00.Descriptive_statistics_G{str_group}.csv")
        
        # save figure (pma_??_Overall.png) with "values"
        plot_key = readcols["key"][readcols["fmt"]=="object"].tolist()
        if len(plot_key) -2 > 0:
            plot_object(df_group, savegroupdir, args.pma, str_group, plot_key, args.pmapath)
        else:
            if args.verb:
                print("*"*5+" "*5+"Because the analyzing column does not contain `object`, " +
                        "figures for each group are not saved.")
        
        # save results with compelet columns and mid 
        df_group.to_csv(f"{savegroupdir}/02.Detail_info_mid.csv", index=False)


    if args.verb:
        print("|"+"="*50+"|")
        print("|"+" "*5+"Saving descriptive statistics of dataset"+" "*5+"|")
        print("|"+"-"*50+"|")
        print("*"*5+" "*5+"filename path : "+savedir+" "*5)
        
    endtime = datetime.datetime.now()
    execution_time = endtime-starttime

    print()
    print()
    print(f"A total of {len(df_label)} records were processed in {execution_time.total_seconds()} seconds in PMA: {args.pma}")
    print()
    print()

if __name__ == "__main__":

    # Run main program
    main()
     

