# encoding = utf-8
print()
choice = input('Select 1 (single product name) or 2 (file) to choose what format you want to input:    ')
print()
if choice not in ["1", "2"]:  
    print('***** please select "1" or "2" to classify. ')    
else:
    import time
    start = time.time()
    print()
    print('***** Begining to import module ... please wait a minute')
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

    def single_product():
        product = input("please input the product name: ")
        for num in range(Num_keyword):
            locals()[f'keyword_{num+1}']=[]
        
        sub_no, sub_name = classify(product)
        categoryname = df_class['大分類'][df_class['中分類編號']==sub_no].values[0]
        category_no  = df_class['大分類編號'][df_class['中分類編號']==sub_no].values[0]
        print('************************')
        print(product)
        print(f'大分類: {category_no}, {categoryname}')
        print(f'中分類: {sub_no}, {sub_name}')
        #================== using product name to find keyword
        try:
            df_keyword = pd.read_csv(f'Keyword_clear.csv')
            find_sub_name = sub_name.replace('/','_')
            keywordname =  df_keyword[f'{find_sub_name}_key'][df_keyword[f'{find_sub_name}_key'].notnull()].tolist()
            keywordnum = df_keyword[f'{find_sub_name}_no'][df_keyword[f'{find_sub_name}_no'].notnull()].tolist()
            find_keyword = []
            find_keyword = [{'name':keyname, 'num':keynum} for keyname, keynum in zip(keywordname,keywordnum)  if keyname in product ]
            find_keyword_topN = heapq.nlargest(Num_keyword, find_keyword, key=lambda find_keyword: find_keyword['num'])
            find_keyword_topN = [temp['name'] for temp in find_keyword_topN]
    
            print(f'標籤: {find_keyword_topN}')
            print()
            print('************************')
        except:
            print(f'標籤: Please wait for next version to update the keyword list! ')
    #============================================================================= 
    model = torch.load(f'opei_classifier_v4.pt')
    model.eval()
    class_dict = json.loads(io.open(f'dict_class_v4.json', encoding='utf-8').read())

    class_idx_to_name = {}
    for k in class_dict.keys():
    	class_idx_to_name[class_dict[k]] = k

    stoi = json.loads(io.open(f'stoi-v4.json', encoding='utf-8').read())
    df_class = pd.read_csv('dict_class_comparison.csv')

    Num_keyword = 5
    #============================================================================= 
    if choice == '1':

        single_product()
        again = input('***** Classfiy another product? Y/N      ')
        while again in ['Y', 'y' ,'yes', 'YES']:    
            single_product()
            again = input('***** Classfiy another product? Y/N      ')

    elif choice == '2':
        print()
        print()
        print('***** Relative or absolute path of INPUT file, e.g. /Users/users/test.csv or ../test.csv')
        print()
        inputfile = input('INPUT filename:')
        print()
        print()
        outputfile = input('OUTPUT filename:')
        import glob
        if glob.glob(inputfile) == []:
            print('***** Please set or check the input filename. ')
            print('***** Please set or check the input filename. ')
            print('***** Please set or check the input filename. ')
        else:
            if len(outputfile) == 0:
                outputfile = 'Result_classified.csv'
    
            print(f'***** INputname: {inputfile}, OUTputname: {outputfile}')
            print()
            print()
            print()

     #=============================================================================

            print('***** Begining to load dataset')

            df_input = pd.read_csv(inputfile, names=['product'])
            print(f'***** The length of your dataset: {len(df_input)}')
        
            #=====================================================================
            print('***** Begining to classify product ....... ')
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

                #================== subcategory to category
                categoryname = df_class['大分類'][df_class['中分類編號']==sub_no].values[0]
                category_no  = df_class['大分類編號'][df_class['中分類編號']==sub_no].values[0]

                #================== using product name to find keyword
                try:
                    df_keyword = pd.read_csv(f'Keyword_clear.csv')
                    find_sub_name = sub_name.replace('/','_')
                    keywordname =  df_keyword[f'{find_sub_name}_key'][df_keyword[f'{find_sub_name}_key'].notnull()].tolist()
                    keywordnum = df_keyword[f'{find_sub_name}_no'][df_keyword[f'{find_sub_name}_no'].notnull()].tolist()
                    find_keyword = []
                    find_keyword = [{'name':keyname, 'num':keynum} for keyname, keynum in zip(keywordname,keywordnum)  if keyname in product ]
                    find_keyword_topN = heapq.nlargest(Num_keyword, find_keyword, key=lambda find_keyword: find_keyword['num'])
                    find_keyword_topN = [temp['name'] for temp in find_keyword_topN]
                    if p_idx % 10 == 0 :
                        print(p_idx, product)
                        print(f'大分類: {category_no}, {categoryname}')
                        print(f'中分類: {sub_no}, {sub_name}')
                        print(f'標籤: {find_keyword_topN}')
                        print()
                        print()
                except:
                    find_keyword = []
                    find_keyword_topN = []
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
    
            newdf.to_csv(outputfile, index=False, encoding='utf_8_sig')
            print(f'***** Finished the classification. The outputfile: {outputfile}')
            print(f'***** Finished the classification. The outputfile: {outputfile}')
            print(f'***** Finished the classification. The outputfile: {outputfile}')	
            end = time.time()
            print(format(end-start))