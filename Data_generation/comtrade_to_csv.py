#!/usr/bin/env python3

# Author: Matt Cornachione
# This converts a comtrade .cgf and .dat file to csv
# Some header information is lost, but all analog channels are
# saved with their name as the header

import comtradeDT as com
import pandas as pd
import numpy as np
import os
import argparse
import glob

class Converter:
    ''' Class to convert comtrade to csv '''
    def __init__(self):
        self.comtrade = com.Comtrade()

    def _get_header(self, file):
        try:
            cfg_file = f'{file}.cfg'
            self.comtrade.load(cfg_file)
        except FileNotFoundError: # Simple handling of lower vs. uppercase file extension
            cfg_file = f'{file}.CFG'
            self.comtrade.load(cfg_file)
        header = list()
        for i in range(self.comtrade.analog_count):
            header.append(self.comtrade.cfg.analog_channels[i].name)
        return header
    
    def _get_data(self, file):
        try:
            cfg_file = f'{file}.cfg'
            dat_file = f'{file}.dat'
            self.comtrade.load(cfg_file, dat_file)
        except FileNotFoundError: # Simple handling of lower vs. uppercase file extension
            cfg_file = f'{file}.CFG'
            dat_file = f'{file}.DAT'
            self.comtrade.load(cfg_file, dat_file)
        data = np.array(self.comtrade.analog)
        return data

    def convert_com2csv(self, file):
        ''' converts the given file from comtrade to csv '''
        header = self._get_header(file)
        data = self._get_data(file)
        if len(header) != data.shape[0]:
            raise IndexError(f"Size mismatch between header ({len(header)}) and data (data.shape)")
        df = pd.DataFrame(data=data.T, columns=header)
        df.to_csv(f'{file}_test.csv', index=False)

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--filename', type=str, help="Name of the .dat (.cfg) file to open (use full path if in a different directory)",
                    default=None)
parser.add_argument('-d', '--directory', type=str, help="Directory to explore - will convert all comtrade files in this directory", default='Examples')
args = parser.parse_args()

use_dir = False
use_file = False
directory = None
filename = None
cwd = os.getcwd()
if args.filename is None:
    use_dir = True
    if args.directory is None:
        directory = cwd
    else:
        if cwd not in args.directory:
            directory = os.path.join(cwd, args.directory)
        if not os.path.isdir(directory):
            raise ValueError(f"Directory input {args.directory} is not a valid directory.")
else:
    use_file = True
    if cwd in args.filename:
        filename = args.filename
    else:
        filename = os.path.join(cwd,args.filename)
    if not os.path.isfile(filename):
        if not os.path.isfile(f"{filename}.dat"): # Check if .dat was excluded
            raise ValueError(f"Filename input {args.filename} does not exist.")
    else:
        # Strip .cfg or .dat
        if filename.endswith('.cfg') or filename.endswith('.dat'):
            filename = filename[:-4]
    if args.directory != 'Examples':
        print("Both filename and directory were specified. Filename supercedes directory")

# Either use single file or all files in directory
if use_file:
    filelist = [filename]
elif use_dir:
    all_files = [f for f in os.listdir(directory)]
    filelist = [os.path.join(directory,f[:-4]) for f in all_files if f.lower().endswith('.cfg')]

converter = Converter()
for file in filelist:
    print(f"Converting file {file}")
    converter.convert_com2csv(file)