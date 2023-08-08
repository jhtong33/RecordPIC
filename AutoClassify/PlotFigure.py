import numpy as np 
import math 
import pandas as pd
import os, glob
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Taipei Sans TC Beta"]

def read_pma_cate(pmapath):
    return pd.read_csv(pmapath)

def out_text(ax, set_pk, wedges, cntlist):
    bbox_props = dict(boxstyle="square,pad=0.05", fc="w", ec="k", lw=0.01)
    kw = dict(arrowprops=dict(arrowstyle="-", color="lightgrey"), 
              zorder=0, va="center")
    perc = [f"{int(e/s * 100)}% ({e})" for s in (sum(cntlist), ) for e in cntlist]

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        ha = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = f"angle,angleA=0,angleB={ang}"
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax.annotate(f"{set_pk[i]} {perc[i]}", xy=(x, y), 
                    xytext=(1.2*np.sign(x), 1.2*y), fontsize=4, 
                    ha=ha, **kw)
    

def make_autopct(values):
    def my_autopct(pct):
        total = sum(values)
        val = int(round(pct*total/100.0))
        return "{p:.0f}%\n({v:d})".format(p = pct, v = val)
    return my_autopct


def output_log(logfile, df_label, starttime, pma, category, AutoCluster, method, selectMethod, numofCluster):
    
    lenfile = len(df_label) 

    cmd = """
    echo "===========================================" > %(logfile)s
    echo Executing time: %(starttime)s >> %(logfile)s
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
    echo "===========================================" >> %(logfile)s
    """%locals()
    os.system(cmd)

    cnt_grouplen = df_label["label"].value_counts()
    for i in range(numofCluster):
        cnt_group = cnt_grouplen[i]
        pct_group = round(100*(cnt_group/lenfile),2)
        cmd = """
        echo "Group %(i)i: %(cnt_group)i (%(pct_group).2f%%)" >> %(logfile)s
        """%locals()
        os.system(cmd)
        
def plot_values(df_label, savedir, pma, numofCluster, plot_key, pmapath):
    df_pma = read_pma_cate(pmapath)
    pmaname = df_pma["pma_name"][df_pma["pma_no"]==pma].values[0]
    cnt_plot = len(plot_key)

    plt.figure(figsize=(1.4*cnt_plot, 12))
    plt.suptitle(f"PMA: {pma} {pmaname}", fontsize=12)
    for i, pk in enumerate(plot_key):
        plt.subplot(4, math.ceil(cnt_plot/4), i+1)
        plt.scatter(df_label["label"], df_label[pk],  alpha = 0.1, color="k", s=1)
        for i in range(numofCluster):
            plt.errorbar(i, np.mean(df_label[pk][df_label["label"]==i]), 
                        yerr = np.std(df_label[pk][df_label["label"]==i]),
                        color = "r", fmt = "d", capsize = 3, alpha = 0.5)
            plt.text(x = i+0.1, y = np.mean(df_label[pk][df_label["label"]==i]), 
                     s = round(np.mean(df_label[pk][df_label["label"]==i]), 1),
                    fontsize = 6, ha = "left")
        plt.title(pk, fontsize = 8)
        plt.xticks(range(numofCluster), fontsize = 7)
        plt.yticks(fontsize = 7)
        if "recency" in pk:
            plt.ylim(max(df_label[pk])+0.5, min(df_label[pk])-0.5)
    plt.savefig(f"{savedir}/pma_{pma}_Overall.png", dpi = 300, bbox_inches = "tight")
    plt.close()
    
def plot_object(df_group, savegroupdir, pma, str_group, plot_key, pmapath):
    
    df_pma = read_pma_cate(pmapath)    
    pmaname = df_pma["pma_name"][df_pma["pma_no"]==pma].values[0]
    plot_key = sorted(plot_key)
    plot_key.remove("mid")
    plot_key.remove("pma_no_fin")
    
    try:
        if "area_01" in plot_key:
            for remove_area in ["area_02", "area_03", "area_04", "area_05", "area_06", "area_07", "area_09", "area_10", "area_11"]:
                plot_key.remove(remove_area)
        if "weekend" in plot_key:
            plot_key.remove("weekend")
    except:
        print("remove error! ")
        
    cnt_plot = len(plot_key)
    if "rfm_level" in df_group.keys(): 
        plot_key.append("rfm_level")
        cnt_plot += 2
        
    fig = plt.figure(figsize = (2*cnt_plot, 5), )
    plt.subplots_adjust(hspace = 0.5)
    plt.axis("off")
    plt.suptitle(f"PMA: {pma} {pmaname}/ Group: {str_group}", fontsize = 12)
    cmap = list((plt.get_cmap("Pastel1")).colors)
    
    for i, pk in enumerate(plot_key):
        ax = fig.add_subplot(2, math.ceil(cnt_plot/2), i+1) 
        
        if pk == "area_01":
            ax.set_title("Area", fontsize = 10, fontweight = "bold")
            df_masterarea = pd.read_csv("store_area_config.csv")
            area_keylist = [ area_key for area_key in df_group.keys() if "area" in area_key ] 
            set_pk = [] 
            cntlist = [] 
            pctlist = []
            for ak in area_keylist:
                master_no = int(ak.rsplit("_")[-1])
                master_name = df_masterarea["master_area_name"][df_masterarea["master_area_no"]==master_no].values[0]
                master_cnt =  df_masterarea["cnt"][df_masterarea["master_area_no"]==master_no].values[0]
                cnt_master = np.sum(df_group[ak])
                if cnt_master >= 0 :
                    cntlist.append(cnt_master)
                    set_pk.append(master_name)
                    pctlist.append((cnt_master/master_cnt)*100)
                    
            ax.scatter(set_pk, pctlist, color = "k", s = 3)
            for x, y, t in zip(set_pk, pctlist, cntlist):
                ax.text(x, y+0.02, s = t, ha = "left", va = "bottom", fontsize = 5)
            ax.set_xticklabels(set_pk, fontsize = 5, rotation = 20) 
            ax.set_ylabel("Ratio (%)", fontsize = 6)
            ax.set_yticks(np.around(np.arange(min(pctlist), max(pctlist), (max(pctlist)-min(pctlist))/5), 2))
            ax.set_yticklabels(np.around(np.arange(min(pctlist), max(pctlist), (max(pctlist)-min(pctlist))/5), 2), fontsize = 5)
            ax.set_ylim(min(pctlist)-0.05, max(pctlist)+0.05)
            ax.spines[["right", "top"]].set_visible(False)
            
        elif pk == "weekday":
            ax.set_title("Prefer", fontsize = 10, fontweight = "bold")
            set_pk = ["weekday", "weekend"]
            cntlist = [np.sum(df_group[preferk]) for preferk in set_pk]

            ax.pie(cntlist,   
                    labels = set_pk,  
                    autopct = make_autopct(cntlist), 
                    pctdistance = 0.6,       
                    labeldistance = 1.1,
                    textprops = {"fontsize" : 7},
                    colors = cmap)                 
        else : 
            ax.set_title(pk, fontsize = 10, fontweight = "bold")
            set_pk = list(set(df_group[pk]))
            cntlist = [df_group[pk].tolist().count(idx) for idx in set_pk]
            
            if " " in set_pk:
                idx_null = set_pk.index(" ")
                cnt_null = cntlist[idx_null]
                pct_null = round(cnt_null/sum(cntlist) * 100,0)
                ax.text(x = 1, y = -1.4, s = f"Null {pct_null}% ({cnt_null})", \
                fontsize = 6, color = "blue", ha = "right", va = "top")
                set_pk.remove(" ")
                cntlist.pop(idx_null)
            
            if len(set_pk) >= 4 :
                wedges, texts = ax.pie(cntlist, colors = cmap) 
                out_text(ax, set_pk, wedges, cntlist)
            else:
                ax.pie(cntlist,   
                        labels = set_pk,  
                        autopct = make_autopct(cntlist), 
                        pctdistance = 0.6,       
                        labeldistance = 1.1,
                        textprops = {"fontsize" : 7},
                        colors = cmap) 
        if "rfm_level" in plot_key: 
            ax = fig.add_subplot(2, math.ceil(cnt_plot/2), cnt_plot) 
            ax.text(x = 0.5, y = 0, \
            s = "RFM Features\n\n111: 重要價值\n101: 重要發展\n011: 重要保持\n001: 重要挽留\n110: 一般價值\n100: 一般發展\n010: 一般保持\n000: 一般挽留\n", \
            ha = "right", va = "bottom", fontsize = 6)
            ax.axis("off")
    plt.savefig(f"{savegroupdir}/01.plot_ratio.png", dpi = 300, bbox_inches = "tight")
    plt.close()