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
import statistics
from sklearn.preprocessing import LabelEncoder
from collections import defaultdict

### pre-processing 
def processing(path, category, filename, pma, rfm_level, select_rfm, select_two, verbose = False):
    """
    
    Data pre-processing includes:
    (1) reading culumns you want to analysis, 
    (2) fill nan
    (3) distinguish RFM level and add column called "rfm_level"
    (4) If select-rfm, filtered the two elements
    (5) Label encoder

    Parameters
    ----------
    path : str
        The path of category_config.json 
    category : list
        The features will be analyzed
    filename : float
        The file of data
    pma : int
        Specify number of pma
    rfm_level : str
        To distinguish "0" and "1" of R-, F-, and M-level
    select_rfm : boolean
        If True, RFM will be filtered to 2 elements
    select_two : list
        Following select_rfm, specific two elements
    verbose : boolean
        Verbosity

    Returns
    -------
    df : :class:`~pandas.DataFrame`
        Original data after above 1-5 steps
    readcols : dict
        The analyzed columns with key and format
    objectencoder : dict
        Save the object Label Encoder from : class:`~sklearn.preprocessing`

    """
    
    if verbose:
        print("|"+"="*50+"|")
        print("|               Data Preprocessing                 |")
        print("|"+"-"*50+"|")
    
    dconfig = pd.read_json(path)
    
    # must contain these coulmns 
    readcols = {"key": ["mid", "pma_no_fin", "qty", "avg_qty"],
               "fmt": ["object", "object", "values", "values"]}
    
    # read analyzed columns from .json, related to -C 
    if category is not None:
        for cate in category:
            getkey = dconfig[cate]["key"]
            getfmt = dconfig[cate]["format"]
            readcols["key"].extend( getkey )
            readcols["fmt"].extend( getfmt )
        
    if verbose:
        print("*"*5+" "*5+"Read columns: "+str(readcols["key"]))
        print("*"*5+" "*5+"PMA: "+str(pma))
        print("*"*5+" "*5+"Begin to read the file.......")
    
    # read data 
    readcols = pd.DataFrame(readcols)    
    df_ori = pd.read_csv(filename, usecols = readcols["key"])
    df_ori = df_ori[df_ori["pma_no_fin"] == pma]
    
    # fill nan
    df_preprocess = df_ori.copy()
    df_preprocess.fillna(" ", inplace=True)

    objectencoder = defaultdict(list) 
    
    if category is not None and "rfm" in category:
        if verbose:
            print("*"*5+" "*5+"Deal with RFM")
            print("*"*5+" "*5+"RFM level: "+rfm_level)
        
        get_rfmkey = dconfig["rfm"]["key"]
        tempdf_rfm = pd.DataFrame()
        rfm_level_key = []
        
        # RFM level 
        for idx_rfm in get_rfmkey:
            if rfm_level == "average":
                num_split = np.mean(df_preprocess[idx_rfm].astype(float))
            elif rfm_level == "median":
                num_split = np.median(df_preprocess[idx_rfm].astype(float))
            elif rfm_level == "mode":
                num_split = statistics.mode(df_preprocess[idx_rfm].astype(float))
                
            idx_rfm_level = f"{idx_rfm}_level"
            rfm_level_key.append(idx_rfm_level)
            
            # distinfuish 1 or 0 
            if "recency" in idx_rfm :
                tempdf_rfm[idx_rfm_level] = [ "1"  if i <= num_split else "0" for i in df_preprocess[idx_rfm]]
            else:
                tempdf_rfm[idx_rfm_level] = [ "1"  if i >= num_split else "0" for i in df_preprocess[idx_rfm]]

        rfmlevel = []
        vtimes = 0 
        
        # select two elements of RFM 
        for r, f, m in zip(tempdf_rfm[tempdf_rfm.keys()[0]], tempdf_rfm[tempdf_rfm.keys()[1]], tempdf_rfm[tempdf_rfm.keys()[2]]):
            if select_rfm:
                if verbose and vtimes == 0:
                    print("*"*5+" "*5+"Select two elements in RFM: "+str(select_two))
                    vtimes += 1
                    
                if "r" not in select_two:
                    level = f"{f}{m}"
                elif "f" not in select_two:
                    level = f"{r}{m}"
                elif "m" not in select_two:
                    level = f"{r}{f}"       
            else:
                level = f"{r}{f}{m}"
            rfmlevel.append(level)
            
        if verbose:
            print("*"*5+" "*5+"Adding column: rfm_level")

        # Label encoder: RFM level 
        df_preprocess["rfm_level"] = rfmlevel    
        labelencoder_rfm = LabelEncoder()
        df_preprocess["rfm_level"] = labelencoder_rfm.fit_transform(df_preprocess["rfm_level"])
        df_preprocess["rfm_level"] = df_preprocess["rfm_level"].astype(object)
        objectencoder['rfm'].append(labelencoder_rfm)
    
    # Label encoder: Columns with object 
    for objkey in readcols["key"][readcols["fmt"] == "object"]:
        try:
            if "area" not in objkey:
                if verbose:
                    print("*"*5+" "*5 + "Deal with object " + objkey + " -- LabelEncoder")
                
                globals()[f"labelencoder_{objkey}"] = LabelEncoder()
                df_preprocess[objkey] = globals()[f"labelencoder_{objkey}"].fit_transform(df_preprocess[objkey])
                df_preprocess[objkey] = df_preprocess[objkey].astype(object)
                objectencoder[f"{objkey}"].append(globals()[f"labelencoder_{objkey}"])
        except:
            pass
    
    # Deal with "age" 
    try:
        search_space = df_preprocess.apply(lambda x: " " in x.tolist())
        search_space_key = search_space[search_space==True].keys()[0]
        if search_space_key not in readcols["key"][readcols["fmt"]=="object"]:
            df_preprocess[search_space_key] = df_preprocess[search_space_key].replace(" ", 0) 
    except:
        pass
   
    df = df_preprocess.copy()
    
    return df, readcols, objectencoder