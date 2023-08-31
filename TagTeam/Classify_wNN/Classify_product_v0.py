# encoding = utf-8
import pandas as pd
import json, sys, time, re,heapq, io
import torch
import torch.nn as nn
import numpy as np
from torchtext.data import utils
from torchtext.data.utils import _basic_english_normalize
device = torch.device('cuda' if torch.cuda.is_available() else "cpu")

#=============================================================================
class TextSentiment(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_class):
        super().__init__()
        self.embedding = nn.EmbeddingBag(vocab_size, embed_dim, sparse=True)
        self.fc = nn.Linear(embed_dim, num_class)
        self.init_weights()

    def init_weights(self):
        initrange = 0.5
        self.embedding.weight.data.uniform_(-initrange, initrange)
        self.fc.weight.data.uniform_(-initrange, initrange)
        self.fc.bias.data.zero_()

    def forward(self, text, offsets):
        embedded = self.embedding(text, offsets)
        return self.fc(embedded)

def CJK_cleaner(string): 
    filters = re.compile(u'[^0-9a-zA-Z\u4e00-\u9fff]+', re.UNICODE)
    return filters.sub('', string)    
    
def classify(text):
    text = CJK_cleaner(text)
    text = re.sub(r'([\u4e00-\u9fff])',r' \1',text)
    l = list(utils.ngrams_iterator(_basic_english_normalize(text),2))
    l = [[stoi.get(token, 0) for token in l]]

    text = torch.tensor(l)

    with torch.no_grad():
        result = model(text, None)
        value, index = (torch.sort(result,descending=True))
        Maxidx = index[0][0].item()+1
        # print("===========================================")
        # for i in range(0,5):
        #     classIdx = index[0][i].item()
        #     if i == 0 : 
        #         Maxidx = classIdx+1
        #     score = value[0][i].item()
        #     print(f"class: {class_idx_to_name[classIdx+1]}, score:{score}")
        # print("===========================================")
        return index[0][0].item()+1, class_idx_to_name[Maxidx]
    
#=============================================================================  

cmd = '''
awk '{print $1}' Classify_setting.txt
'''%locals()
settingfile=os.popen(cmd).readlines()
inputfile = settingfile[1].rsplit('\n')[0]
outputfile = settingfile[3].rsplit('\n')[0]
df_input = pd.read_csv(inputfile)
Num_keyword = 5

model = torch.load(f'Model/opei_classifier_v4.pt')
model.eval()
class_dict = json.loads(io.open(f'Model/dict_class_v4.json', encoding='utf-8').read())

class_idx_to_name = {}
for k in class_dict.keys():
	class_idx_to_name[class_dict[k]] = k
    
stoi = json.loads(io.open(f'Model/stoi-v4.json', encoding='utf-8').read())
df_class = pd.read_csv('Model/dict_class_comparison.csv')
#=====================================================================

tempdf = {'name':[], 
        'category_no':[],
        'category_name':[],
        'sub_no':[],
        'sub_name': [] } 

for num in range(Num_keyword):
    locals()[f'keyword_{num+1}']=[]
    
for p_idx in range(len(df_input)):
    product = df_input['product'].values[p_idx]
    
#================== using nn model to find subcategory


    sub_no,sub_name = classify(product)

    print(product)
    

    #================== subcategory to category
    categoryname = df_class['大分類'][df_class['中分類編號']==sub_no].values[0]
    category_no  = df_class['大分類編號'][df_class['中分類編號']==sub_no].values[0]

    print(f'大分類: {category_no}, {categoryname}')
    print(f'中分類: {sub_no}, {sub_name}')
    #================== using product name to find keyword
    # try:
    df_keyword = pd.read_csv(f'Model/KEYWORD/{sub_name}_clear_rank.csv')
    keywordname = df_keyword['name'].tolist()
    keywordnum = df_keyword['num'].tolist()

    find_keyword = []
    find_keyword = [{'name':keyname, 'num':keynum} for keyname, keynum in zip(keywordname,keywordnum)  if keyname in product ]
    find_keyword_topN = heapq.nlargest(Num_keyword, find_keyword, key=lambda find_keyword: find_keyword['num'])
    find_keyword_topN = [temp['name'] for temp in find_keyword_topN]
    print(f'標籤: {find_keyword_topN}')
    print()
    print()
    # except:
        # find_keyword = []
    #================== clean up information to csv

    tempdf['name'].append(product)
    tempdf['category_no'].append(category_no)
    tempdf['category_name'].append(categoryname)     
    tempdf['sub_no'].append(sub_no)
    tempdf['sub_name'].append(sub_name)   

    for idx, keyword in enumerate(find_keyword_topN):
        if idx <=4:
            locals()[f'keyword_{idx+1}'].append(keyword)

    if len(find_keyword_topN) < Num_keyword:
        for nanidx in range(len(find_keyword_topN),Num_keyword):
            locals()[f'keyword_{nanidx+1}'].append(np.nan)


tempdf = pd.DataFrame(tempdf)

keytempdf = pd.DataFrame({'keyword_1': keyword_1, 
                          'keyword_2': keyword_2, 
                          'keyword_3': keyword_3, 
                          'keyword_4': keyword_4, 
                          'keyword_5': keyword_5 })

newdf = pd.concat([tempdf,keytempdf], axis=1)


newdf.to_csv(outputfile, index=False)