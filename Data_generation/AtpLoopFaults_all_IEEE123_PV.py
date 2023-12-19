# -*- coding: utf-8 -*-
"""
Created on Fri Feb 10 17:53:28 2023

@author: chat694 Kaustav Chatterjee PNNL
"""

import math
import sys
import operator
import subprocess
import os
import shutil
import random
import msvcrt
from pynput.keyboard import Key, Controller
import pandas as pd
import csv


no_sims = 1  # 1000

def run_atp_fault_case(bus, phs, slgf, fname):
  tfault = random.uniform(0.15, 0.15 + 1/60)
  vsrc = '{:.2f}'.format (atp_vpu * source_vbase)
  fp = open (atp_parm, mode='w')
  print ('$PARAMETER', file=fp)
  print ('_FLT_=\'' + bus.ljust(5) + '\'', file=fp)
  print ('__DELTAT   ={:.5f}'.format (atp_dt), file=fp)
  print ('____TMAX   =0.40', file=fp)
  print ('_VSOURCE__ =' + vsrc, file=fp)
  if slgf == True:  # line-to-gnd fault
    if phs == 'A':
      print ('_TFAULTA__ ={:.5f}'.format (tfault), file=fp)
      # print ('_TFAULTA__ =9.15', file=fp)
      print ('_TFAULTB__ =9.15', file=fp)
      print ('_TFAULTC__ =9.15', file=fp)
      print ('_TFAULTBC_ =9.15', file=fp)
    elif phs == 'B':
      print ('_TFAULTA__ =9.15', file=fp)
      print ('_TFAULTB__ ={:.5f}'.format (tfault), file=fp)
      # print ('_TFAULTB__ =9.15', file=fp)
      print ('_TFAULTC__ =9.15', file=fp)
      print ('_TFAULTBC_ =9.15', file=fp)
    else:
      print ('_TFAULTA__ =9.15', file=fp)
      print ('_TFAULTB__ =9.15', file=fp)
      # print ('_TFAULTC__ =9.15', file=fp)
      print ('_TFAULTC__ ={:.5f}'.format (tfault), file=fp)
      print ('_TFAULTBC_ =9.15', file=fp)
  elif phs == 'AB' :
    print ('_TFAULTA__ ={:.5f}'.format (tfault), file=fp)
    print ('_TFAULTB__ ={:.5f}'.format (tfault), file=fp)
    # print ('_TFAULTA__ =9.15', file=fp)
    # print ('_TFAULTB__ =9.15', file=fp)
    print ('_TFAULTC__ =9.15', file=fp)
    print ('_TFAULTBC_ =9.15', file=fp)
  elif phs == 'BC' :
    print ('_TFAULTA__ =9.15', file=fp)
    # print ('_TFAULTB__ =9.15', file=fp)
    # print ('_TFAULTC__ =9.15', file=fp)
    print ('_TFAULTB__ ={:.5f}'.format (tfault), file=fp)
    print ('_TFAULTC__ ={:.5f}'.format (tfault), file=fp)
    print ('_TFAULTBC_ =9.15', file=fp)
  elif phs == 'AC' :
    # print ('_TFAULTA__ =9.15', file=fp)
    print ('_TFAULTA__ ={:.5f}'.format (tfault), file=fp)
    print ('_TFAULTB__ =9.15', file=fp)
    # print ('_TFAULTC__ =9.15', file=fp)
    print ('_TFAULTC__ ={:.5f}'.format (tfault), file=fp)
    print ('_TFAULTBC_ =9.15', file=fp)
  else :
    print ('_TFAULTA__ ={:.5f}'.format (tfault), file=fp)
    print ('_TFAULTB__ ={:.5f}'.format (tfault), file=fp)
    print ('_TFAULTC__ ={:.5f}'.format (tfault), file=fp)
    # print ('_TFAULTA__ =9.15', file=fp)
    # print ('_TFAULTB__ =9.15', file=fp)
    # print ('_TFAULTC__ =9.15', file=fp)
    print ('_TFAULTBC_ =9.15', file=fp)
  print ('BLANK END PARAMETER', file=fp)
  fp.close()

  cmdline = "runtp " + atp_file + " >nul"
  
  p1 = subprocess.Popen(cmdline, cwd=atp_path, shell=True)
  p1.wait()
  
  # move the pl4 file
  print ('moving {:s} to {:s}'.format (atp_pl4, fname))
  shutil.move(atp_pl4, fname)



atp_base = 'IEEE123_PV'
atp_path = "C:/ATP/OEDI_ATP_Models/"
atp_file = atp_base + '.atp'
atp_list = atp_path + atp_base + '.lis'
atp_parm = atp_path + atp_base + '.prm'
atp_pl4 = atp_path + atp_base + '.pl4'
pl4path = "C:/ATP/OEDI_ATP_Models/"
source_vbase = float(10181.71)
atp_vpu = float(1.035)
atp_dt = float(1e-5)

zones = pd.read_csv('zone_info_IEEE123_PV_v2.csv')  # read csv from zone classification file
zone = zones.zone_35  # zones.zone_35
zone = zone.dropna()
for times in range(no_sims):
    ln=random.choice(zone)
    toks = ln.split('_')
    bus = toks[0]
    atpbus = toks[0]
    nph = len(toks[1])
    phs = toks[1]

    if nph == 3:
      phs = 'ABC'
      pl4name = pl4path + '/' + 'F3_' + atpbus + phs + str(times) + '.pl4'
      print ('running three-phase fault at {:s} ({:s}), output to {:s}'.format (atpbus, bus, pl4name))
      run_atp_fault_case (atpbus, phs, slgf=False, fname=pl4name)
      
      for phs in ['AB', 'BC', 'AC']:
          pl4name = pl4path + '/' + 'F2_' + atpbus + phs + str(times) + '.pl4'
          print ('running two-phase fault at {:s} ({:s}), output to {:s}'.format (atpbus, bus, pl4name))
          run_atp_fault_case (atpbus, phs, slgf=False, fname=pl4name)
      
      for phs in ['A', 'B', 'C']:
          pl4name = pl4path + '/' + 'F1_' + atpbus + phs + str(times) + '.pl4'
          print ('running SLGF on {:s} at {:s} ({:s}), output to {:s}'.format (phs, atpbus, bus, pl4name))
          run_atp_fault_case (atpbus, phs, slgf=True, fname=pl4name)

    # dlgf
    elif nph == 2:
      pl4name = pl4path + '/' + 'F2_' + atpbus + phs + str(times) + '.pl4'
      print('running two-phase fault at {:s} ({:s}), output to {:s}'.format(atpbus, bus, pl4name))
      run_atp_fault_case(atpbus, phs, slgf=False, fname=pl4name)

      for phs in list(phs):
        pl4name = pl4path + '/' + 'F1_' + atpbus + phs + str(times) + '.pl4'
        print('running SLGF on {:s} at {:s} ({:s}), output to {:s}'.format(phs, atpbus, bus, pl4name))
        run_atp_fault_case(atpbus, phs, slgf=True, fname=pl4name)

    else : 
      phs = toks[1]
      pl4name = pl4path + '/' + 'F1_' + atpbus + phs + str(times) + '.pl4'
      print ('running SLGF on {:s} at {:s} ({:s}), output to {:s}'.format (phs, atpbus, bus, pl4name))
      run_atp_fault_case (atpbus, phs, slgf=True, fname=pl4name)  

