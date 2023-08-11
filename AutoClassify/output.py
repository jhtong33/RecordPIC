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

The codes are related to save results with text and figure

"""
import numpy as np 
import pandas as pd
import os, math
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Taipei Sans TC Beta"]



def read_pma_cate(path, pma):
    """
    
    Read the number of pma and corresponding name
    
    Parameters
    ----------
    path : str
        The path of pma configure
    pma : int
        Specific number of pma

    Returns
    -------
    name : str
        Corresponding name of pma
    
    """
    
    df = pd.read_csv(path)
    name = df["pma_name"][df["pma_no"]==pma].values[0]
    return name

def out_text(ax, labels, wedges, count):
    """
    
    Adjust the position of annotates in a pie figure
    
    Parameters
    ----------
    ax : :class:`~matplotlib.pyplot.axis`
        Axis handle
    labels : list
        The labels in a pie figure
    wedges : :class:`~matplotlib.patches.Wedge`
        A wedge centered at x, y center with radius r that sweeps theta1 to theta2 (in degrees)
    cntlist : list
        Count number of each label
    
    """
    
    # text kwargs setting 
    kw = dict(arrowprops = dict(arrowstyle = "-", color = "lightgrey"), 
              zorder = 0, va = "center")
              
    # calculate percentage 
    perc = [f"{int(e/s * 100)}% ({e})" for s in (sum(count), ) for e in count]

    for i, p in enumerate(wedges):
        
        # trigonometric functions
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        ha = {-1: "right", 1: "left"}[int(np.sign(x))]
        
        # arrow kwargs setting 
        connectionstyle = f"angle,angleA=0,angleB={ang}"
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        
        ax.annotate(f"{labels[i]} {perc[i]}", xy = (x, y), 
                    xytext = (1.2*np.sign(x), 1.2*y), fontsize = 4, 
                    ha = ha, **kw)
    

def make_autopct(values):
    
    def my_autopct(pct):
        total = sum(values)
        val = int(round(pct*total/100.0))
        return "{p:.0f}%\n({v:d})".format(p = pct, v = val)
        
    return my_autopct


def output_log(filename, df, starttime, pma, category, AutoCluster, method, selectMethod, num):
    """
    
    Save the initial setting as a text file 
    The Linux command line is used to write down information
    
    Parameters
    ----------
    filename : str
        Output filename
    df : :class:`~pandas.DataFrame`
        The data finished cluster with labels
    starttime : :class:`datetime.datetime`
        The program begin time 
    pma : int
        Specify number of pma    
    category : list
         The specific features will be analyzed
    AutoCluster : boolean
        Automatically search best number of clusters
    method : str
        Specify clustering algorithm
    selectMethod : str
        Specify method algorithm to decide clustering numbers
    num : int
         The best number of groups
    
    """
    
    ### initial information    
    lenfile = len(df) 
    
    ### command line 
    cmd = """
    echo "===========================================" > %(filename)s
    echo Executing time: %(starttime)s >> %(filename)s
    echo PMA: %(pma)i >> %(filename)s
    echo Datalength: %(lenfile)i >> %(filename)s
    echo Features: %(category)s >> %(filename)s
    if %(AutoCluster)s == 'True';  
    then 
        echo Cluster method: %(method)s/Auto/%(selectMethod)s >> %(filename)s
    else
        echo Cluster method: %(method)s/Manual >> %(filename)s
    fi

    echo Num. of Group: %(num)i >> %(filename)s
    echo "===========================================" >> %(filename)s
    """%locals()
    os.system(cmd)

    ### save quantity and percentage of each group
    cnt_grouplen = df["label"].value_counts()
    
    for i in range(num):
        
        # count
        cnt_group = cnt_grouplen[i]
        
        # calculate percentage
        pct_group = round(100*(cnt_group/lenfile),2)
        
        ### command line 
        cmd = """
        echo "Group %(i)i: %(cnt_group)i (%(pct_group).2f%%)" >> %(filename)s
        """%locals()
        os.system(cmd)
        
        
        
def plot_values(df, savedir, pma, num, key, pmapath):
    """
    
    Plot the figure of analyzed columns with values
    Note: Save figure automatically 
    
    Parameters
    ----------
    df: :class:`~pandas.DataFrame`
        The data finished cluster with labels
    savedir : str
        Specify directory to save figures
    pma : int
        Specify number of pma    
    num : int
        The best number of groups
    key : list
        The format of columns is values
    pmapath : str
        The path of pma config
    
    """
    
    ### initial information
    pmaname = read_pma_cate(pmapath, pma)
    cnt_plot = len(key)
    
    ### Figure handle
    plt.figure(figsize=(1.4*cnt_plot, 12))
    
    # Title of this figure 
    plt.suptitle(f"PMA: {pma} {pmaname}", fontsize=12)
    
    
    for i, pk in enumerate(key):
        
        # Figure handle
        plt.subplot(4, math.ceil(cnt_plot/4), i+1)
        
        ### scatter plot
        plt.scatter(df["label"], df[pk],  alpha = 0.1, color="k", s=1)
        
        ### plot the average and standard deviations of each group 
        for i in range(num):
            # error bar 
            plt.errorbar(i, np.mean(df[pk][df["label"]==i]), 
                        yerr = np.std(df[pk][df["label"]==i]),
                        color = "r", fmt = "d", capsize = 3, alpha = 0.5)
            # text
            plt.text(x = i+0.1, y = np.mean(df[pk][df["label"]==i]), 
                     s = round(np.mean(df[pk][df["label"]==i]), 1),
                    fontsize = 6, ha = "left")
        
        # title of this plot          
        plt.title(pk, fontsize = 8)
        
        plt.xticks(range(num), fontsize = 7)
        plt.yticks(fontsize = 7)
        
        # reverse y-axis due to recency definition 
        if "recency" in pk:
            plt.ylim(max(df[pk])+0.5, min(df[pk])-0.5)
            
            
    plt.savefig(f"{savedir}/pma_{pma}_Overall.png", dpi = 300, bbox_inches = "tight")
    plt.close()
    
def plot_object(df, savedir, pma, numgroup, key, pmapath):
    """
    
    Plot the figure of analyzed columns with object. 
    Note: Save figure automatically 
    
    Parameters
    ----------
    df: :class:`~pandas.DataFrame`
        Data of each group
    savedir : str
        Specify directory to save figures
    pma : int
        Specify number of pma    
    numgroup : str
        The number of group
    key : list
        The format of columns is object
    pmapath : str
        The path of pma config
    
    """
    ### initial information    
    pmaname = read_pma_cate(pmapath, pma)    
    
    key = sorted(key)
    key.remove("mid")
    key.remove("pma_no_fin")
    
    ### Features (Area and Perfer) need to tidy up to plot a pie
    try:
        if "area_01" in key:
            for remove_area in ["area_02", "area_03", "area_04", "area_05", "area_06", "area_07", "area_09", "area_10", "area_11"]:
                key.remove(remove_area)
        if "weekend" in key:
            key.remove("weekend")
    except:
        print("remove error! ")
        
    ### initial information      
    cnt_plot = len(key)
    
    ### Show the RFM-level rather than RFM values
    if "rfm_level" in df.keys(): 
        key.append("rfm_level")
        cnt_plot += 2
        
    # Figure handle
    fig = plt.figure(figsize = (2*cnt_plot, 5), )
    plt.subplots_adjust(hspace = 0.5)
    plt.axis("off")
    
    # pie color 
    cmap = list((plt.get_cmap("Pastel1")).colors)
        
    # Title of this figure 
    plt.suptitle(f"PMA: {pma} {pmaname}/ Group: {numgroup}", fontsize = 12)
    
    
    for i, pk in enumerate(key):
        
        # Figure handle
        ax = fig.add_subplot(2, math.ceil(cnt_plot/2), i+1) 
        
        # Specfically handle feature: Area
        if pk == "area_01":
            
            # title of this pie 
            ax.set_title("Area", fontsize = 10, fontweight = "bold")
            
            # get the corresponding name of master area
            df_masterarea = pd.read_csv("store_area_config.csv")
            area_keylist = [ area_key for area_key in df.keys() if "area" in area_key ] 
            
            set_labels = [] 
            cntlist = [] 
            pctlist = []
            
            # Count and calculate percentage of master area
            for ak in area_keylist:
                master_no = int(ak.rsplit("_")[-1])
                master_name = df_masterarea["master_area_name"][df_masterarea["master_area_no"]==master_no].values[0]
                master_cnt =  df_masterarea["cnt"][df_masterarea["master_area_no"]==master_no].values[0]
                cnt_master = np.sum(df[ak])
                
                if cnt_master >= 0 :
                    cntlist.append(cnt_master)
                    set_labels.append(master_name)
                    pctlist.append((cnt_master/master_cnt)*100)
                    
            
            ax.scatter(set_labels, pctlist, color = "k", s = 3)
            
            for x, y, t in zip(set_labels, pctlist, cntlist):
                ax.text(x, y+0.02, s = t, ha = "left", va = "bottom", fontsize = 5)
                
            ax.set_xticklabels(set_labels, fontsize = 5, rotation = 20) 
            
            ax.set_ylabel("Ratio (%)", fontsize = 6)
            ax.set_ylim(min(pctlist)-0.05, max(pctlist)+0.05)
            ax.set_yticks(np.around(np.arange(min(pctlist), max(pctlist), (max(pctlist)-min(pctlist))/5), 2))
            ax.set_yticklabels(np.around(np.arange(min(pctlist), max(pctlist), (max(pctlist)-min(pctlist))/5), 2), fontsize = 5)
            
            ax.spines[["right", "top"]].set_visible(False)
        
        # Specfically handle feature: Prefer    
        elif pk == "weekday":
            
            # title of this pie 
            ax.set_title("Prefer", fontsize = 10, fontweight = "bold")
            
            # labels
            set_labels = ["weekday", "weekend"]
            
            # count  
            cntlist = [np.sum(df[preferk]) for preferk in set_labels]
            
            ax.pie(cntlist,   
                    labels = set_labels,  
                    autopct = make_autopct(cntlist), 
                    pctdistance = 0.6,       
                    labeldistance = 1.1,
                    textprops = {"fontsize" : 7},
                    colors = cmap)    
        
        # general pie                       
        else : 
            # title of this pie 
            ax.set_title(pk, fontsize = 10, fontweight = "bold")
            
            # labels
            set_labels = list(set(df[pk]))
            
            # count  
            cntlist = [df[pk].tolist().count(idx) for idx in set_labels]
            
            # count the number of null 
            if " " in set_labels:
                idx_null = set_labels.index(" ")
                cnt_null = cntlist[idx_null]
                pct_null = round(cnt_null/sum(cntlist) * 100,0)
                
                # write down
                ax.text(x = 1, y = -1.4, s = f"Null {pct_null}% ({cnt_null})", \
                fontsize = 6, color = "blue", ha = "right", va = "top")
                
                # and remove null
                set_labels.remove(" ")
                cntlist.pop(idx_null)
            
            # plot pie and adjust text position
            if len(set_labels) >= 4 :
                
                wedges, texts = ax.pie(cntlist, colors = cmap) 
                out_text(ax, set_labels, wedges, cntlist)
            
            # plot pie and NO adjust text position
            else:
                ax.pie(cntlist,   
                        labels = set_labels,  
                        autopct = make_autopct(cntlist), 
                        pctdistance = 0.6,       
                        labeldistance = 1.1,
                        textprops = {"fontsize" : 7},
                        colors = cmap) 
                        
        # Annotate RFM features: its level and meaning 
        if "rfm_level" in key: 
            
            # Figure handle
            ax = fig.add_subplot(2, math.ceil(cnt_plot/2), cnt_plot) 
            ax.axis("off")
            
            ax.text(x = 0.5, y = 0, \
            s = "RFM Features\n\n111: 重要價值\n101: 重要發展\n011: 重要保持\n001: 重要挽留\n110: 一般價值\n100: 一般發展\n010: 一般保持\n000: 一般挽留\n", \
            ha = "right", va = "bottom", fontsize = 6)
            
    plt.savefig(f"{savedir}/01.plot_ratio.png", dpi = 300, bbox_inches = "tight")
    plt.close()