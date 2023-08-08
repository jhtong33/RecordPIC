import pandas as pd
import numpy as np
import statistics
from sklearn.preprocessing import LabelEncoder
from collections import defaultdict

def processing(category_path, category, filename, pma, rfm_level, select_rfm, select_two, verbose = False):
    ### pre-processing 
    if verbose:
        print("|"+"="*50+"|")
        print("|               Data Preprocessing                 |")
        print("|"+"-"*50+"|")
    
    dconfig = pd.read_json(category_path)
    readcols = {"key": ["mid", "pma_no_fin", "qty", "avg_qty"],
               "fmt": ["object", "object", "values", "values"]}

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
    
    readcols = pd.DataFrame(readcols)    
    df = pd.read_csv(filename, usecols = readcols["key"])
    df = df[df["pma_no_fin"]==pma]

    df_preprocess = df.copy()
    df_preprocess.fillna(" ", inplace=True)

    objectencoder = defaultdict(list) 
    if category is not None and "rfm" in category:
        if verbose:
            print("*"*5+" "*5+"Deal with RFM")
            print("*"*5+" "*5+"RFM level: "+rfm_level)
    
        getkey = dconfig["rfm"]["key"]
        tempdf_rfm = pd.DataFrame()
        rfm_level_key = []
        for idx_rfm in getkey:
            if rfm_level == "average":
                num_split = np.mean(df_preprocess[idx_rfm].astype(float))
            elif rfm_level == "median":
                num_split = np.median(df_preprocess[idx_rfm].astype(float))
            elif rfm_level == "mode":
                num_split = statistics.mode(df_preprocess[idx_rfm].astype(float))
                
            idx_rfm_level = f"{idx_rfm}_level"
            rfm_level_key.append(idx_rfm_level)
            
            if "recency" in idx_rfm :
                tempdf_rfm[idx_rfm_level] = [ "1"  if i <= num_split else "0" for i in df_preprocess[idx_rfm]]
            else:
                tempdf_rfm[idx_rfm_level] = [ "1"  if i >= num_split else "0" for i in df_preprocess[idx_rfm]]

        rfmlevel = []
        for r, f, m in zip(tempdf_rfm[tempdf_rfm.keys()[0]], tempdf_rfm[tempdf_rfm.keys()[1]], tempdf_rfm[tempdf_rfm.keys()[2]]):
            if select_rfm:
                if verbose:
                    print("*"*5+" "*5+"Select two elements in RFM: "+select_two)
        
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

        df_preprocess["rfm_level"]  = rfmlevel    
        labelencoder_rfm = LabelEncoder()
        df_preprocess["rfm_level"] = labelencoder_rfm.fit_transform(df_preprocess["rfm_level"])
        df_preprocess["rfm_level"] = df_preprocess["rfm_level"].astype(object)
        objectencoder['rfm'].append(labelencoder_rfm)
    
    for objkey in readcols["key"][readcols["fmt"]=="object"]:
        try:
            if "area" not in objkey:
                if verbose:
                    print("*"*5+" "*5+"Deal with object "+objkey+" -- LabelEncoder")
                
                globals()[f"labelencoder_{objkey}"] = LabelEncoder()
                df_preprocess[objkey] = globals()[f"labelencoder_{objkey}"].fit_transform(df_preprocess[objkey])
                df_preprocess[objkey] = df_preprocess[objkey].astype(object)
                objectencoder[f"{objkey}"].append(globals()[f"labelencoder_{objkey}"])
        except:
            pass
            
    try:
        search_space = df_preprocess.apply(lambda x: " " in x.tolist())
        search_space_key = search_space[search_space==True].keys()[0]
        if search_space_key not in readcols["key"][readcols["fmt"]=="object"]:
            df_preprocess[search_space_key] = df_preprocess[search_space_key].replace(" ", 0) 
    except:
        pass
   
    
    return df_preprocess, readcols, objectencoder