#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 03:46:02 2020

@author: haotian teng
"""
import json
import os
import numpy as np
from itertools import permutations
from fict.utils import data_op as dop
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from scipy.stats import ttest_rel
import pickle
import string
import matplotlib 
import anndata
plt.style.use(['science','ieee'])
matplotlib.rc('text', usetex=False)
def permute_accuracy(predict,y):
    """Find the best accuracy among all the permutated clustering.
    Input args:
        predict: the clustering result.
        y: the true label.
    Return:
        best_accur: return the best accuracy.
        perm: return the permutation given the best accuracy.
    """
    predict = np.asarray(predict,dtype = np.int)
    y = np.asarray(y,dtype = np.int)
    label_tag = np.unique(y)
    predict_tag = np.unique(predict)
    sample_n = len(y)
    if len(label_tag) == len(predict_tag):
        perms = list(permutations(label_tag))
        hits = []
        for perm in perms:
            hit = np.sum([(predict == p) * (y == i) for i,p in enumerate(perm)])
            hits.append(hit)
        return np.max(hits)/sample_n,perms[np.argmax(hits)]
    else:
        hits = np.zeros(len(predict_tag))
        average_hits = np.zeros(len(predict_tag))
        perms = np.zeros(len(predict_tag))
        for predict_i in predict_tag:
            for label_i in label_tag:
                hit = np.sum([(predict == predict_i) * (y == label_i) ])
                if hit>hits[predict_i]:
                    hits[predict_i] = hit
                    perms[predict_i] = label_i
                average_hits[predict_i]+=hit
            average_hits[predict_i] = (average_hits[predict_i] - hits[predict_i])/(len(predict_tag)-1)
        return (np.sum(hits)-np.sum(average_hits))/sample_n,perms

def read_labels(label_folder,label_idxs):
    labels = []
    for i in label_idxs:
        label = []
        with open(os.path.join(data_folder,str(i)+'.labels'),'r') as f:
            for line in f:
                label.append(int(line.strip().split(' ')[1]))
        labels.append(label)
    labels = np.asarray(labels)
    return labels

def read_smfish_label(result_f,idxs,beta,k=3):
    labels = []
    for i in idxs:
        current_f = os.path.join(result_f,'%d/k_%d/fresult.beta.%.1f.prob.txt'%(i,k,beta))
        probs = []
        if not os.path.exists(current_f):
            continue
        with open(current_f,'r') as f:
            for line in f:
                line = line.strip().split(' ')[1:]
                probs.append([float(x) for x in line])
        probs = np.asarray(probs)
        label = np.argmax(probs,axis=1)
        labels.append(label)
    return np.asarray(labels)

def read_scanpy_accuracy(result_f,idxs):
    accurs = []
    for i in idxs:
        current_f = os.path.join(result_f,'%d/result.hdf5'%(i))
        adata = anndata.read_h5ad(current_f)
        accur,perm = permute_accuracy(adata.obs['cell_type'],adata.obs['leiden'])
        accurs.append(accur)
    return accurs

def read_seurat_labels(result_f,idxs):
    labels = []
    for i in idxs:
        current_f = os.path.join(result_f,'%d/label.csv'%(i))
        label = pd.read_csv(current_f,header = None)
        labels.append(np.asarray(label).transpose())
    return labels


def heatmap(nb,ax,xticks= None,yticks = None,title = ''):
    n,m = nb.shape
    _ = ax.imshow(nb,cmap='gray',vmin=np.min(nb), vmax=1.5*np.max(nb))
    # We want to show all ticks...
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(m))
    ax.grid(False)
    # ... and label them with the respective list entries
    if xticks is not None:
        ax.set_xticklabels(xticks[:n])
    if yticks is not None:
        ax.set_yticklabels(yticks[:m])
    
    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=0, ha="right",
             rotation_mode="anchor")
    
    # Loop over data dimensions and create text annotations.
    for i in range(n):
        for j in range(m):
            text = ax.text(j, i, "%.2f"%(nb[i,j]),
                           ha="center", va="center", color="w")
    ax.set_title(title)
    return ax

def coor_scatter(sim,ax,method):
    ax.scatter(sim.coor[:,0],sim.coor[:,1],c = sim.cell_type_assignment,s=10)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
#    ax.title.set_text(method)
    return ax
#sim_folder = "/home/heavens/lanec1/data/Benchmark/simulation_5celltype/"
sim_folder = "/home/heavens/twilight_hdd1/Simulation/"
cell_type_n = 3
figs,axs = plt.subplots(ncols = 3, nrows = 1,figsize = (3.5*5,2.625))
figs2,axs2 = plt.subplots(ncols = 3, nrows = 1,figsize = (3.5*5,2.625))
figs3,axs3 = plt.subplots(ncols =3, nrows = 1,figsize = (3.5*5,3.5))
for c_i,condition in enumerate(["Addictive","Exclusive","Stripe"]):
    ax = axs[c_i]
    ax2 = axs2[c_i]
    base_folder = sim_folder + condition
    sim_f = os.path.join(base_folder,'simulator.bin')
    with open(sim_f,'rb') as f:
        sim = pickle.load(f)
    coor_scatter(sim,axs3[c_i],condition)
    heatmap(sim.neighbour_frequency,ax2,xticks = ['I','II','III'],yticks = ['I','II','III'])
    data_folder = os.path.join(base_folder,"data")
    smfish_result_folder = os.path.join(base_folder,"smfishHmrf_result")
    scanpy_result_folder = os.path.join(base_folder,"scanpy_result")
    seurat_result_folder = os.path.join(base_folder,"seurat_result")
    FICT_result_file = os.path.join(base_folder,"FICT_result/record.json")
    repeat = 50
    
    with open(FICT_result_file,'r') as f:
        record = json.load(f)
    gene_accur = record['accs_gene']
    fict_accur = record['accs_sg']
    labels = read_labels(data_folder,np.arange(repeat))
    smfish_labels = read_smfish_label(smfish_result_folder,np.arange(repeat),beta = 3.0,k=cell_type_n)
    seurat_labels = read_seurat_labels(seurat_result_folder,np.arange(repeat))
    smfish_accur = []
    seurat_accur = []
    for i in np.arange(repeat):
        label = labels[i,:]
        if i < len(smfish_labels):
            smfish_label = smfish_labels[i,:]
            accur,perms = permute_accuracy(smfish_label,label)
            smfish_accur.append(accur)
        accur,perms = permute_accuracy(seurat_labels[i],label)
        seurat_accur.append(accur)
    scanpy_accur = read_scanpy_accuracy(scanpy_result_folder,idxs = np.arange(repeat))
    gene_accur = np.asarray(gene_accur)
    smfish_accur = np.asarray(smfish_accur)
    if len(smfish_accur)<repeat:
        smfish_accur = np.pad(smfish_accur,(0,repeat - len(smfish_accur)),constant_values = None)
    fict_accur = np.asarray(fict_accur)
    scanpy_accur = np.asarray(scanpy_accur)
    seurat_accur = np.asarray(seurat_accur)
    accur_list = [gene_accur,smfish_accur,fict_accur,scanpy_accur,seurat_accur]
    result = {}
    argsort = np.argsort(gene_accur)
    ### Remove unscessful simulation case whose gene model accuracy is much lower than baseline.
    Threshold_accuracy = 0.6
    mask = gene_accur>Threshold_accuracy
    print("%d outlier case was removed"%(sum(gene_accur<=Threshold_accuracy)))
    result['smfishHmrf'] = smfish_accur[mask]
    result['GMM'] = gene_accur[mask]
    result['FICT'] = fict_accur[mask]
    result['Scanpy'] = scanpy_accur[mask]
    result['Seurat'] = seurat_accur[mask]
    for method in result.keys():
        print("%s, %s:%.3f +- %.3f"%(condition, 
                                     method,
                                     np.mean(result[method]),
                                     np.std(result[method])))
    df = pd.DataFrame(result, columns = list(result.keys()))
    df_long = pd.melt(df,value_vars = list(result.keys()),
                      var_name = "Model",
                      value_name = "Accuracy")
    sns.set(style="whitegrid")
    if c_i==0:
        y_name = "Accuracy"
    else:
        y_name = None
    box_ax = sns.boxplot(data = df_long,x = "Model",y="Accuracy",showfliers=False,ax = ax)
    for box in box_ax.artists:
        box.set_facecolor("white")
        box.set_edgecolor("grey")
    if c_i>0:
        box_ax.set(ylabel = None)
    box_ax.set(xlabel = None)
    if c_i==0:
        ylim0 = ax.get_ylim()
    ylim_current = ax.get_ylim()
    ratio = (ylim_current[1]-ylim_current[0])/(ylim0[1]-ylim0[0])
    def mark_pval(x1,x2,height,offset,axis):
        height = height*ratio
        offset = offset*ratio
        y, h, col = df_long['Accuracy'].max() + height, height, 'k'
        axis.plot([x1, x1, x2, x2], [y+offset, y+h+offset, y+h+offset, y+offset], c=col)
        p_val1 = ttest_rel(accur_list[x1],accur_list[x2]).pvalue
        p_val1 = "{:.2e}".format(p_val1)
        axis.text((x1+x2)*.5, y+h*1.3+offset, "p=%s"%(p_val1), ha='center', va='bottom', color=col)
    mark_pval(0,2,0.004,0.025,ax)
    mark_pval(1,2,0.004,0,ax)
    mark_pval(2,3,0.004,0.030,ax)
    mark_pval(2,4,0.004,0.005,ax)
    ax.text(-0.1, 1.02, string.ascii_uppercase[c_i], transform=ax.transAxes, 
        size=15, weight='bold')
    ax2.text(-0.1, 1.02, string.ascii_uppercase[c_i], transform=ax2.transAxes, 
        size=15, weight='bold')
for i,ax in enumerate(axs3):
    ax.text(-0.1, 1.02, string.ascii_uppercase[i], transform=ax.transAxes, 
        size=20, weight='bold')
#    plt.title("Models accuracy on simulation dataset.")
figs.savefig(os.path.join(sim_folder,"Accuracy.png"),bbox_inches='tight')
figs2.savefig(os.path.join(sim_folder,"NeighbourhoodFrequency.png"),bbox_inches='tight')
figs.savefig("Accuracy.png",bbox_inches='tight',transparent = True)
figs2.savefig("NeighbourhoodFrequency.png",bbox_inches='tight',transparent = True)
figs3.savefig("CoordinateScatter.png",transparent = True)