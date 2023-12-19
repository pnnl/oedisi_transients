# -*- coding: utf-8 -*-
"""
Created on Fri Aug 19 10:21:45 2022

Run a pl4 file through gtppl32.exe and exports a comtrade, then converts
the ASCII comtrade to a float32 comtrade.
   - gtppl32.exe is assumed to be in the same folder as this script, can easily
   change that if needed.

@author: Dylan Tarter
"""

import sys
import os
import subprocess
from comtradeDT import ComtradeConverter


def pl42com(filename):
    # cases that we plan to do, (taken from pl4_to_hdf5)
    cases = [
        {'name': 'IEEE123_PV', 'relatp': 'IEEE123_PV'},
        {'name': 'LV_Network', 'relatp': 'LV_Network/LV_Network'},
        {'name': 'IEEE13_PV', 'relatp': 'IEEE13/IEEE13_PV'},
        {'name': 'IEEE9500', 'relatp': 'IEEE9500/IEEE9500'},
        {'name': 'EPRI_J1', 'relatp': 'EPRI_J1/EPRI_J1'},
        {'name': 'Avista CEF2', 'relatp': 'CEF2/CEF2'},
        {'name': 'Nantucket', 'relatp': 'Nantucket/Nantucket'},
        {'name': 'PNNL', 'relatp': 'PNNL/PNNL'},
    ]

    atp_path = '.'

    # uncomment this stuff to run multiple cases
    # if __name__ == '__main__':
    #   idx = 0
    #  if len(sys.argv) > 1:
    #     idx = int(sys.argv[1])

    # case = cases[idx]
    # atp_root = case['relatp']
    # case = filename
    case = filename
    atp_root = filename

    # derived from pl4_to_hdf5
    print('converting {:s} pl4 to COMTRADE'.format(case))
    pl4_file = '{:s}.pl4'.format(atp_root)
    cmdline = 'gtppl32.exe @@commands.script > nul'  # assumes gtppl32.exe is in the same folder as script

    """Builds a script of commands to be run by gtppl32.exe"""
    fp = open('commands.script', mode='w')
    print('file', atp_root, file=fp)
    print('comtrade all', file=fp)
    print('', file=fp)
    print('stop', file=fp)
    fp.close()
    print('running', cmdline, 'with cwd', atp_path)

    """powershell opens the gtppl32.exe and runs the command script"""
    pw0 = subprocess.call(cmdline, cwd=atp_path, shell=True)
    print('created', atp_root, 'COMTRADE file')

    # small bit for measuring the file size
    comSize = os.stat(atp_root + '.dat').st_size + os.stat(atp_root + '.cfg').st_size

    """Converts from ASCII to float32 mode and prints the file size difference"""
    mode = 'float32'
    ComtradeConverter(atp_root, mode)
    print('converted', atp_root, 'to COMTRADE with ', mode, ' data type')
    comSize1 = os.stat(atp_root + '.dat').st_size + os.stat(atp_root + '.cfg').st_size
    print("    *File is %.2f times smaller in new file type" % (comSize / comSize1))
    print("    *File size is %.fkB" % (comSize1 / 1000))


