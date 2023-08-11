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
"""

Module containing the main utility functions used in the `Clustering` scripts
that accompany this package.

"""
# -*- coding: utf-8 -*-
from argparse import ArgumentParser
from numpy import nan
import glob, os 
import pandas as pd

def get_arguments(argv = None):
    
    parser = ArgumentParser(
        usage = "python %(prog)s --file [filename] --pma [no.] -N [number]/-A [options]",
        description = "")
        
        
    # General Settings    
    parser.add_argument(
        "-f", "-F", "--file",
        action = "store",
        type = str,
        dest = "filename",
        default = None,
        required = True, 
        help = "Specify the file you input.")    
    parser.add_argument(
        "--pma", "--PMA",
        action = "store",
        type = int,
        dest = "pma",
        default = None,
        required = True, 
        help = "Specify the PMA number to classify.")     
    parser.add_argument(
        "-c", "-C", "--category",
        action = "store",
        type = str,
        dest = "category",
        default = None,
        help = "Select one or more features you want to include to classify. " +
        "Options include: 'all', 'personal', 'rfm', 'area', " +
        "'purchasetime', 'prefer', 'calculated'. [Default is None]")     
    parser.add_argument(
        "-o", "-O", "--overwrite",
        action = "store_true",
        dest = "ovr",
        default = False,
        help = "Force the overwriting of pre-existing results. " +
        "Default behaviour prompts for those that " +
        "already exist. Selecting overwrite and skip (ie, both flags) " +
        "negate each other, and both are set to " +
        "false (every repeat is prompted). [Default is False]")  
    parser.add_argument(
        "-v", "-V", "--verbose",
        action = "store_true",
        dest = "verb",
        default = False,
        help = "Specify to increase verbosity. [Default is False]")       
        
    # Method Settings   
    MethodGroup = parser.add_argument_group(
        title = "Cluster method",
        description = "***** Choosing one method to classify dataset. ")
    MethodGroup.add_argument(
        "-m", "-M", "--method",
        action = "store",
        type = str,
        dest = "method",
        default = "KMeans",
        help = "Choose the method to classify. Options include: " +
        "'KMeans', 'KPrototypes', 'KMedoids', 'KModes', 'WKMeans'. " +
        "For large dataset, 'KMeans' is faster than other methods. [Default is 'KMeans']")
    MethodGroup.add_argument(
        "-w", "-W", "--weight",
        action = "store",
        type = str,
        dest = "weight",
        default = None,
        help = "When selecting 'WKMeans', one column in the dataset must" +
        " be chosen as the weighting factor. [Default is None]")   


    # Auto/Manual Settings
    AutoGroup = parser.add_argument_group(
        title = "Auto Classify Settings",
        description = "***** Settings associated with searching the best number of clusters")
    AutoGroup.add_argument(
         "-n", "-N", "--num",
        action = "store",
        type = int,
        dest = "numofCluster",
        default = None,
        help = "Manunally specify the number of group. [Default is None]")
    AutoGroup.add_argument(
        "-a", "-A", "--auto", 
        action = "store_true",
        dest = "AutoCluster",
        default = False,
        help = "If select this option, it will automatically search the " +
        "best number of clusters. [Default is False]")
    AutoGroup.add_argument(
        "--auto-method",
        action = "store",
        type = str,
        dest = "selectMethod",
        default = "elbow",
        help = "Choose method to find the best number of cluster. Options include: " +
        "'elbow', 'calinski-harabasz', 'davies-bouldin', 'silhouette'. Detail setting from website: "+
        "https://reurl.cc/M8mr9K [Default is 'elbow']")
    AutoGroup.add_argument(
         "--Gmin",
        action = "store",
        type = int,
        dest = "Gmin",
        default = 5,
        help = "Specify the minimum group of grid search. [Default is 5]") 
    AutoGroup.add_argument(
         "--Gmax",
        action = "store",
        type = int,
        dest = "Gmax",
        default = 20,
        help = "Specify the maximum group of grid search. [Default is 20]")        

    # RFM Settings
    RFMGroup = parser.add_argument_group(
        title = "RFM level",
        description = "***** If 'rfm' in category, settings how to distinguish the RFM level")
    RFMGroup.add_argument(
        "--rfm-level",
        action = "store",
        type = str,
        dest = "rfm_level",
        default = "mode",
        help = "Selecting how to distinguish the level. " +
        "Options include: 'median', 'mode', 'average'. [Default is 'mode']")
    RFMGroup.add_argument(
        "--rfm-select",
        action = "store_true",
        dest = "select_rfm",
        default = False,
        help = "Choosing whether three elements to classify or not. [Default is False]")            
    RFMGroup.add_argument(
        "--rfm-select-two",
        action = "store",
        type = str,
        dest = "select_two",
        default = None,
        help = "Choosing whether two elements to classify." +
        "Options include: 'r', 'f', 'm'. [Default is None]")       
        
    # Path Settings
    PathGroup = parser.add_argument_group(
        title = "Path",
        description = "***** Settings path associated with files.")
    PathGroup.add_argument(
        "-cp", "-CP", "--catepath",
        action = "store",
        type = str,
        dest = "category_path",
        default = "category_config.json",
        help = "Specify .json file to read the categories and corresponding items. " +
        "[Default is './category_config.json']")   
    PathGroup.add_argument(
        "-pp", "-PP", "--pmapath",
        action = "store",
        type = str,
        dest = "pmapath",
        default = "pma_config.csv",
        help = "Specify .csv file to read the no. and corresponding PMA name. " +
        "The header includes 'pma_no', 'pma_name'. " +
        "[Default is './pma_config.csv']")           
    PathGroup.add_argument(
        "-sp", "-SP", "--savepath",
        action = "store",
        type = str,
        dest = "savepath",
        default = ".",
        help = "The path to save the clustering results. [Default is the path of this code]")  
        
    args  =  parser.parse_args(argv)  
    
    #==========================================================================================
    #==========================================================================================
    #==========================================================================================
    ### Fool Proofing
    
    if len(args.filename) > 1:
        try:
            ifglob = len(glob.glob(args.filename))
            if ifglob < 1:
                parser.error(f"Cannot glob the file {args.filename}")
            else:
                df = pd.read_csv(args.filename, nrows = 5)
                try:
                    for mustkey in ["mid", "pma_no_fin", "qty", "avg_qty"]:
                        if mustkey not in df.keys():
                            parser.error("***The file must contain columns: "+
                                            "mid, pma_no_fin, qty, avg_qty")
                except:
                    parser.error("***The file must contains columns: " +
                                "mid, pma_no_fin, qty, avg_qty")
        except:
            parser.error(f"Cannot glob the file {args.filename}, please use --file = *.csv")
    else:
        parser.error(f"***MUST input the file, please use --file = *.csv")
    
    dpma = pd.read_csv(args.pmapath)  

    if args.pma == None: 
        parser.error("***MUST select one PMA number") 
    else:
        dtemp = dpma[dpma["pma_no"] == args.pma]
        if len(dtemp) == 0: 
            parser.error(f"PMA: {args.pma} is not efficient pma. ")

        
    if args.category is not None:
        args.category = args.category.split(",")
        if "all" in args.category:
            df_cate = pd.read_json(args.category_path)
            args.category = list(df_cate.keys())

    if args.method not in ["KMeans", "KPrototypes", "KMedoids", "KModes", "WKMeans"]:
        parser.error(f"Method: {args.method} is not in our options. Options include: " +
        "'KMeans', 'KPrototypes', 'KMedoids', 'KModes', 'WKMeans'")
    elif args.method == "WKMeans" and args.weight is None:
        parser.error(f"WKMeans should set the weight factor (option: --weight)")
    
    if args.weight == "rfm":
        args.weight = "rfm_level"
    elif args.weight in ["mid", "pma_no_fin"]:
        parser.error(f"The column: {args.weight} is not effective. ")
    
        
    if args.AutoCluster and args.numofCluster is not None:
        parser.error(f"Please select -a or -n [number] to analyze. ")
    elif args.AutoCluster == False and args.numofCluster is None:
        parser.error(f"Please select -a or -n [number] to analyze. ")
        
    if args.selectMethod not in ["elbow", "calinski-harabasz", "davies-bouldin", "silhouette"]:
        parser.error(f"Please check the option: --auto-method = {args.selectMethod}")
        
    if args.rfm_level not in ["median", "mode", "average"]:
        parser.error(f"Please check the option: --rfm-level = {args.rfm_level}")
    
    if args.select_rfm == True and args.select_two is None:
        parser.error("Please select two elemets (option: --rfm-select-two)")
    elif args.select_rfm == True and args.select_two is not None:     
        args.select_two = args.select_two.rsplit(",")     
        if len(args.select_two) != 2 :
            parser.error(f"Please select two elemets from 'r', 'f', 'm', "+
                            "you set {len(args.select_two)} elemets")
        elif len(args.select_two) == 2 :
            if args.select_two[0] not in ["r", "f", "m"]:
                parser.error("Please select two elemets from 'r', 'f', 'm'")
            elif args.select_two[1] not in ["r", "f", "m"]:
                parser.error("Please select two elemets from 'r', 'f', 'm'")

    
    if len(args.category_path) > 1:
        df_cate = pd.read_json(args.category_path)
        if "key" not in df_cate.index:
            parser.error(f"{args.category_path} must contain 'key'")
        elif "format" not in df_cate.index:
            parser.error(f"{args.category_path} must contain 'format'")
        elif args.category is not None:
            for inputcate in args.category:
                if inputcate not in df_cate.keys():
                    parser.error(f"The column '{inputcate}' is not in {args.category_path}")
    else:
        parser.error(f"Cannot glob {args.category_path}")     
    
    if len(args.pmapath) > 1: 
        try:
            tryglob = glob.glob(args.pmapath)      
        except:
            parser.error(f"Cannot glob {args.pmapath}") 
            
    if args.savepath == ".":
        args.savepath = os.getcwd() 

    return args
