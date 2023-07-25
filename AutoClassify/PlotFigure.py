import matplotlib.pyplot as plt
import numpy as np 
import math 
import pandas as pd
import os, glob

df_pma = pd.read_csv('pma_config.csv')
plt.rcParams['font.sans-serif'] = ['Taipei Sans TC Beta']

def out_text(ax, set_pk, wedges, cntlist):
    bbox_props = dict(boxstyle="square,pad=0.05", fc="w", ec="k", lw=0.01)
    kw = dict(arrowprops=dict(arrowstyle="-", color='lightgrey'), 
              zorder=0, va="center")
    perc = [f'{int(e/s * 100)}% ({e})' for s in (sum(cntlist), ) for e in cntlist]

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        ha = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = f"angle,angleA=0,angleB={ang}"
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax.annotate(f'{set_pk[i]} {perc[i]}', xy=(x, y), 
                    xytext=(1.2*np.sign(x), 1.2*y), fontsize=8, 
                    horizontalalignment=ha, **kw)
    

def make_autopct(values):
    def my_autopct(pct):
        total = sum(values)
        val = int(round(pct*total/100.0))
        return '{p:.0f}%\n({v:d})'.format(p=pct,v=val)
    return my_autopct



def plot_values(df_label, savedir, pma, numofCluster, plot_key):
    pmaname = df_pma['pma_name'][df_pma['pma_no']==pma].values[0]
    cnt_plot = len(plot_key)

    plt.figure(figsize=(1.3*cnt_plot,8))
    plt.suptitle(f'PMA: {pma} {pmaname}',fontsize=12)
    for i, pk in enumerate(plot_key):
        plt.subplot(3,math.ceil(cnt_plot/3),i+1)
        for i in range(numofCluster):
            plt.errorbar(i, np.mean(df_label[pk][df_label['label']==i]), 
                        yerr = np.std(df_label[pk][df_label['label']==i]),
                        color='r', fmt='d', capsize = 3,  alpha = 0.5)
            plt.text(x=i+0.1, y=np.mean(df_label[pk][df_label['label']==i]), 
                     s=round(np.mean(df_label[pk][df_label['label']==i]),1),
                    fontsize=6, ha='left')
        plt.scatter(df_label['label'], df_label[pk],  alpha = 0.1)
        plt.title(pk, fontsize=8)
        plt.xticks(range(numofCluster), fontsize=7)
        plt.yticks(fontsize=7)

        if 'recency' in pk:
            plt.ylim(max(df_label[pk])+0.5, min(df_label[pk])-0.5)
    plt.savefig(f'{savedir}/pma_{pma}_Overall.png',dpi = 150, bbox_inches='tight')
    plt.close()
    
def plot_object(df_group, savegroupdir, pma, str_group, plot_key):
    pmaname = df_pma['pma_name'][df_pma['pma_no']==pma].values[0]

    plot_key.remove('mid')
    plot_key.remove('pma_no_fin')
    try:
        if 'area_01' in plot_key:
            for remove_area in ["area_02", "area_03", "area_04", "area_05", "area_06", "area_07", "area_09", "area_10", "area_11"]:
                plot_key.remove(remove_area)
        if 'weekend' in plot_key:
            plot_key.remove('weekend')
    except:
        print('remove error! ')
        
    cnt_plot = len(plot_key)
    if 'rfm_level' in df_group.keys(): 
        plot_key.append('rfm_level')
        cnt_plot += 2

    fig = plt.figure(figsize=(1.5*cnt_plot,4), )
    plt.axis('off')
    plt.suptitle(f'PMA: {pma} {pmaname}/ Group: {str_group}',fontsize=12)
    cmap = list((plt.get_cmap('Pastel1')).colors)
    
    for i, pk in enumerate(plot_key):
        ax = fig.add_subplot(2,math.ceil(cnt_plot/2),i+1) 
        
        if pk == 'area_01':
            ax.set_title('Area', fontsize=10, fontweight='bold')
            df_masterarea = pd.read_csv('store_area_config.csv')
            area_keylist = [ area_key for area_key in df_group.keys() if 'area' in area_key ] 
            set_pk = [] 
            cntlist = [] 
            for ak in area_keylist:
                master_no = int(ak.rsplit('_')[-1])
                master_name = df_masterarea['master_area_name'][df_masterarea['master_area_no']==master_no].values[0]
                cnt_master = np.sum(df_group[ak])
                if cnt_master > 0 :
                    cntlist.append(cnt_master)
                    set_pk.append(master_name)
            if len(set_pk) > 4 :
                wedges, texts = ax.pie(cntlist, colors = cmap)
                out_text(ax, set_pk, wedges, cntlist)
            else:
                ax.pie(cntlist,   
                        labels = set_pk,  
                        autopct = make_autopct(cntlist), 
                        pctdistance = 0.6,       
                        labeldistance = 1.1,
                        textprops = {"fontsize" : 6},
                        colors = cmap) 
        elif pk == 'weekday':
            ax.set_title('Prefer', fontsize=10, fontweight='bold')
            set_pk = ['weekday', 'weekend']
            cntlist = [np.sum(df_group[preferk]) for preferk in set_pk]

            ax.pie(cntlist,   
                    labels = set_pk,  
                    autopct = make_autopct(cntlist), 
                    pctdistance = 0.6,       
                    labeldistance = 1.1,
                    textprops = {"fontsize" : 6},
                    colors = cmap)                 
        else : 
            ax.set_title(pk, fontsize=10, fontweight='bold')
            set_pk = list(set(df_group[pk]))
            cntlist = [df_group[pk].tolist().count(idx) for idx in set_pk]
            
            if len(set_pk) > 4 :
                wedges, texts = ax.pie(cntlist, colors = cmap) 
                out_text(ax, set_pk, wedges, cntlist)
            else:
                ax.pie(cntlist,   
                        labels = set_pk,  
                        autopct = make_autopct(cntlist), 
                        pctdistance = 0.6,       
                        labeldistance = 1.1,
                        textprops = {"fontsize" : 6},
                        colors = cmap) 
        if 'rfm_level' in plot_key: 
            ax = fig.add_subplot(2,math.ceil(cnt_plot/2),cnt_plot) 
            ax.text(x=0, y=0, s = '111: 重要價值\n101: 重要發展\n011: 重要保持\n001: 重要挽留\n110: 一般價值\n100: 一般發展\n010: 一般保持\n000: 一般挽留\n', ha='left', va='bottom', fontsize= 8, fontweight = 'light')
            ax.axis('off')
    plt.savefig(f'{savegroupdir}/01.plot_ratio.png',dpi = 150, bbox_inches='tight')
    plt.close()