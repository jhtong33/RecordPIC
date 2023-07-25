# !pip install kmodes
# !pip install scikit-learn-extra

import pandas as pd
import numpy as np
import datetime, math
import sys, os, warnings
import matplotlib.pyplot as plt
from kmodes.kprototypes import KPrototypes
from kmodes.kmodes import KModes
from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler,LabelEncoder,OneHotEncoder,MinMaxScaler
from sklearn.cluster import KMeans
from sklearn_extra.cluster import KMedoids
from PlotFigure import plot_values, plot_object
from Autoclass import find_best_cluster
from arguments import  get_arguments
warnings.filterwarnings("ignore")


args = get_arguments()
starttime = datetime.datetime.now()
if args.verb:
    print()
    print("|"+"="*50+"|")
    print("|                Begining to analyze               |")
    print("|"+"="*50+"|")
        
#===========================================
### pre-processing 
if args.verb:
    print("|"+"="*50+"|")
    print("|               Data Preprocessing                 |")
    print("|"+"-"*50+"|")
    
dconfig = pd.read_json(args.cate_json)
readcols = {'key':['mid', 'pma_no_fin', 'qty', 'avg_qty'],
           'fmt': ['object', 'object', 'values', 'values']}

if args.category is not None:
    for cate in args.category:
        getkey = dconfig[cate]['key']
        getfmt = dconfig[cate]['format']
        readcols['key'].extend( getkey )
        readcols['fmt'].extend( getfmt )
        
if args.verb:
    print("*"*5+" "*5+"Read columns: "+str(readcols["key"]))
    print("*"*5+" "*5+"PMA: "+str(args.pma))
    
readcols = pd.DataFrame(readcols)    
df = pd.read_csv(args.filename, usecols = readcols['key'])
df = df[df['pma_no_fin']==args.pma]

df_preprocess = df.copy()
df_preprocess.fillna(' ', inplace=True)

if 'rfm' in args.category:
    
    if args.verb:
        print("*"*5+" "*5+"Deal with RFM")
        print("*"*5+" "*5+"RFM level: "+args.rfm_level)
        
    getkey = dconfig['rfm']['key']
    tempdf_rfm = pd.DataFrame()
    rfm_level_key = []
    for idx_rfm in getkey:
        if args.rfm_level == 'average':
            num_split = np.mean(df_preprocess[idx_rfm].astype(float))
        elif args.rfm_level == 'median':
            num_split = np.median(df_preprocess[idx_rfm].astype(float))
        elif args.rfm_level == 'mode':
            num_split = np.mode(df_preprocess[idx_rfm].astype(float))
        idx_rfm_level = f'{idx_rfm}_level'
        rfm_level_key.append(idx_rfm_level)
        if 'recency' in idx_rfm :
            tempdf_rfm[idx_rfm_level] = [ '1'  if i <= num_split else '0' for i in df_preprocess[idx_rfm]]
        else:
            tempdf_rfm[idx_rfm_level] = [ '1'  if i >= num_split else '0' for i in df_preprocess[idx_rfm]]
    
    rfmlevel = []
    for r, f, m in zip(tempdf_rfm[tempdf_rfm.keys()[0]], tempdf_rfm[tempdf_rfm.keys()[1]], tempdf_rfm[tempdf_rfm.keys()[2]]):
        if args.select_rfm:
            if args.verb:
                print("*"*5+" "*5+"Select two elements in RFM: "+args.select_two)
            
            if 'r' not in args.select_two:
                level = f'{f}{m}'
            elif 'f' not in args.select_two:
                level = f'{r}{m}'
            elif 'm' not in args.select_two:
                level = f'{r}{f}'       
        else:
            level = f'{r}{f}{m}'
        rfmlevel.append(level)
        
    df_preprocess['rfm_level']  = rfmlevel    
    labelencoder_rfm = LabelEncoder()
    df_preprocess['rfm_level'] = labelencoder_rfm.fit_transform(df_preprocess['rfm_level'])
    df_preprocess['rfm_level'] = df_preprocess['rfm_level'].astype(object)
    
for objkey in readcols['key'][readcols['fmt']=='object']:
    if args.verb:
        print("*"*5+" "*5+"Deal with object "+objkey+" -- LabelEncoder")
    try:
        if 'area' not in objkey:
            globals()[f'labelencoder_{objkey}'] = LabelEncoder()
            df_preprocess[objkey] = globals()[f'labelencoder_{objkey}'].fit_transform(df_preprocess[objkey])
            df_preprocess[objkey] = df_preprocess[objkey].astype(object)
    except:
        pass

df_preprocess = df_preprocess.replace(' ',0)   
df_4cluster = df_preprocess.copy()

if 'rfm' in args.category:
    df_4cluster = df_4cluster.drop(['mid', 'pma_no_fin', 'rfm_recency', 'rfm_frequency', 'rfm_monetary'], axis = 1) 
else:
    df_4cluster = df_4cluster.drop(['mid', 'pma_no_fin'], axis = 1) 
    
catobj_Name =  list(df_4cluster.select_dtypes('object').columns)
catobj_Pos = [df_4cluster.columns.get_loc(col) for col in list(df_4cluster.select_dtypes('object').columns)] 


#===========================================
### mkdir
savedir = f'{args.savepath}/PMA-{args.pma}'
if not os.path.isdir(savedir):
        os.makedirs(savedir)
else:
    if not args.ovr:
        gettime = os.path.getctime(savedir)
        datetimeObj = datetime.datetime.fromtimestamp(gettime)
        dateStr = datetimeObj.strftime('%Y%m%d_%H%M%S')
        os.makedirs(f'{savedir}/{dateStr}')
        cmd = '''
        mv %(savedir)s/Group* %(savedir)s/%(dateStr)s
        mv %(savedir)s/*.log %(savedir)s/%(dateStr)s
        mv %(savedir)s/*.png %(savedir)s/%(dateStr)s
        '''%locals()
        os.system(cmd)
        
#===========================================
### Find the best number of cluster
if args.AutoCluster:
    numofCluster = find_best_cluster(args.method, df_4cluster, args.pma, savedir, catobj_Pos, args.selectMethod, args.Gmin, args.Gmax)
    if args.verb:
        print("|"+"="*50+"|")
        print("|"+" "*5+"Automatically find the best number of group"+" "*2+"|")
        print("|"+"-"*50+"|")
        print("*"*5+" "*5+"Clustering method: "+args.method)
        print("*"*5+" "*5+"The method to choose : "+args.selectMethod)
        print("*"*5+" "*5+"The best number of cluster : "+str(numofCluster))
        print("*"*5+" "*5+"The analysis result path : "+savedir)
        print("|"+"="*50+"|")
else:
    numofCluster = args.numofCluster
    if args.verb:
        print("|"+"="*50+"|")
        print("|"+" "*6+"Manually specify the number of group  "+" "*6+"|")
        print("|"+"-"*50+"|")
        print("*"*5+" "*5+"The number of cluster : "+str(numofCluster))
        print("|"+"="*50+"|")
#===========================================
### Beginging to classify 
if args.verb:
    print("|"+"="*50+"|")
    print("|               Begining to classify               |")
    print("|"+"="*50+"|")
df_label = df_preprocess.copy()
if args.method.casefold() == 'KMeans'.casefold():
    model_kmean = KMeans(n_clusters=numofCluster, init='random', random_state=50)
    result = model_kmean.fit(df_4cluster)
    label = result.labels_
    df_label['label'] = label
elif args.method.casefold() == 'KPrototypes'.casefold():
    model_kproto = KPrototypes(n_clusters=numofCluster, init='Huang', random_state=50)
    label = model_kproto.fit_predict(df_4cluster.to_numpy(), categorical=catobj_Pos)
    df_label['label'] = label
elif args.method.casefold() == 'KMedoids'.casefold():    
    model_kmedoids = KMedoids(n_clusters=numofCluster, random_state=50)
    result = model_kmedoids.fit(df_4cluster)
    df_label['label'] = result.labels_
elif args.method.casefold() == 'KModes'.casefold():   
    model_kmodes = KModes(n_clusters=numofCluster, random_state=50)
    result = model_kmodes.fit(df_4cluster)
    df_label['label'] = result.labels_

#===========================================
### Overall 
logfile = f'{savedir}/pma_{args.pma}.log'
lenfile = len(df_label)
printcluster = numofCluster-1

pma = args.pma
category = args.category
AutoCluster = args.AutoCluster
method = args.method
selectMethod = args.selectMethod

cmd = '''
echo '===========================================' > %(logfile)s
echo `date` >> %(logfile)s
echo PMA: %(pma)i >> %(logfile)s
echo Datalength: %(lenfile)i >> %(logfile)s
echo Features: %(category)s >> %(logfile)s
if %(AutoCluster)s == 'True';  
then 
    echo Cluster method: %(method)s/Auto/%(selectMethod)s >> %(logfile)s
else
    echo Cluster method: %(method)s/Manual >> %(logfile)s
fi

echo Num. of Group: %(numofCluster)i >> %(logfile)s
echo '===========================================' >> %(logfile)s
'''%locals()
os.system(cmd)

cnt_grouplen = df_label['label'].value_counts()
for i in range(numofCluster):
    cnt_group = cnt_grouplen[i]
    pct_group = round(100*(cnt_group/lenfile),2)
    cmd = '''
    echo "Group %(i)i: %(cnt_group)i (%(pct_group).2f%%)" >> %(logfile)s
    '''%locals()
    os.system(cmd)


plot_key = readcols['key'][readcols['fmt']=='values'].tolist()
plot_values(df_label, savedir, args.pma, numofCluster, plot_key)

#===========================================
### each group 
for i in range(numofCluster):

    str_group = str(i).zfill(2)
    savegroupdir = f'{savedir}/Group_{str_group}'
    if not os.path.isdir(savegroupdir):
        os.makedirs(savegroupdir)

        
    df_group = df_label[df_label['label']==i]
    for objkey in readcols['key'][readcols['fmt']=='object']:
        try:
            if 'area' not in objkey:
                df_group[objkey] = globals()[f'labelencoder_{objkey}'].inverse_transform(df_group[objkey].astype(int))
        except:
            pass
    if 'rfm_level' in df_group.keys():
        df_group['rfm_level'] = labelencoder_rfm.inverse_transform(df_group['rfm_level'].astype(int))

    df_group_describe = df_group.describe()
    df_group_describe = df_group_describe.drop(labels='count')
    df_group_describe = df_group_describe.drop(columns='label')
    df_group_describe = df_group_describe.drop(columns='pma_no_fin')
    
    df_group_describe.to_csv(f'{savegroupdir}/00.Descriptive_statistics_G{str_group}.csv')
    plot_key = readcols['key'][readcols['fmt']=='object'].tolist()
    plot_object(df_group, savegroupdir, args.pma, str_group, plot_key)
    df_group.to_csv(f'{savegroupdir}/02.Detail_info_mid.csv', index=False)
    
endtime = datetime.datetime.now()
execution_time = endtime-starttime
if args.verb:
    print("|"+"="*50+"|")
    print("|"+" "*5+"Saving descriptive statistics of dataset"+" "*5+"|")
    print("|"+"-"*50+"|")
    print("*"*5+" "*5+"filename path : "+savedir+" "*5)
    
print()
print()
print(f"A total of {lenfile} records were processed in {execution_time.total_seconds()} seconds in PMA: {args.pma}")
print()
print()
     

