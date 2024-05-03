# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 12:16:39 2024

@author: corn677
"""

import scipy
import numpy as np
import pandas as pd
from os.path import join
import os

def mat_dict_to_df(mat_dict):
    exclude = ['__header__', '__version__', '__globals__', 'ans']
    columns = [k for k in mat_dict.keys() if k not in exclude]
    size = mat_dict[columns[0]].size
    data = np.zeros((size, len(columns)))
    for i, k in enumerate(columns):
        data[:,i] = mat_dict[k].reshape((mat_dict[k].size,))
    df = pd.DataFrame(data, columns=columns, index=None)
    return df

# path = "C:/ATP/OEDI_ATP_Models/IEEE123/results"
# files = ['NoFault_NoPV_0001.mat', 'NoFault_YesPV_0001.mat']
path = 'Examples'
files = [f for f in os.listdir(path) if '.mat' in f]

for file in files:
    mat_dict = scipy.io.loadmat(join(path, file))
    df = mat_dict_to_df(mat_dict)
    # df.to_csv(join(path,f"{file.split('.')[0][:-5]}.csv"), index=False)
    df.to_csv(join(path,f"{file.split('.')[0]}.csv"), index=False)