import os
import sys
import argparse
import json
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl

parser = argparse.ArgumentParser()

mpl.rcParams['font.family'] = 'Hiragino Maru Gothic Pro'

parser.add_argument('-b', '--begin',
                    help='beginning date of simulator')
parser.add_argument('-f', '--finish',
                    help='finishing date of simulator')
parser.add_argument('-d', '--database', required=True,
                    help='path of database simulated')
parser.add_argument('-s', '--sensor', required=True,
                    help='path of water sensing')
parser.add_argument('-c', '--commoninfo', required=True,
                    help='path of common information')
parser.add_argument('-sraw', '--sensor_raw', action='store_true',
                    help='display sonsor raw information')
parser.add_argument('-sr', '--sunray', action='store_true',
                    help='display sun-ray information')
args = parser.parse_args()

if os.path.isfile(args.database) == False:
    print("ERROR: no input database")
    sys.exit(1)
else:
    df = pd.read_csv(args.database)

if os.path.isfile(args.sensor) == False:
    print("ERROR: no input database")
    sys.exit(1)
else:
    dfs = pd.read_csv(args.sensor, parse_dates=True, index_col='Date', comment='#', usecols=[1,7])

####
dfwt0 = df[['Date','EarlyMorningWaterTemperature']].copy()
dfwt0['Date'] = pd.to_datetime(dfwt0['Date'], format='%Y-%m-%d %H:%M:%S')

dfwt0['Date'] = dfwt0['Date'] + datetime.timedelta(hours=5)
dfwt0 = dfwt0.rename(columns={'EarlyMorningWaterTemperature': 'WaterTemperatureModel'})
dfwt0_d = dfwt0.set_index('Date')

dfwt1 = df[['Date','EveningWaterTemperature']].copy()
dfwt1['Date'] = pd.to_datetime(dfwt1['Date'], format='%Y-%m-%d %H:%M:%S')

dfwt1['Date'] = dfwt1['Date'] + datetime.timedelta(hours=17)
dfwt1 = dfwt1.rename(columns={'EveningWaterTemperature': 'WaterTemperatureModel'})
dfwt1_d = dfwt1.set_index('Date')

dfwt01 = pd.concat([dfwt0_d, dfwt1_d])
####

dft0 = df[['Date','DaytimeTemperature']].copy()
dft0['Date'] = pd.to_datetime(dft0['Date'], format='%Y-%m-%d %H:%M:%S')

dft0['Date'] = dft0['Date'] + datetime.timedelta(hours=14)
dft0 = dft0.rename(columns={'DaytimeTemperature': 'Temperature'})
dft0_d = dft0.set_index('Date')

dft1 = df[['Date','NighttimeTemperature']].copy()
dft1['Date'] = pd.to_datetime(dft1['Date'], format='%Y-%m-%d %H:%M:%S')

dft1['Date'] = dft1['Date'] + datetime.timedelta(hours=2)
dft1 = dft1.rename(columns={'NighttimeTemperature': 'Temperature'})
dft1_d = dft1.set_index('Date')

dft01 = pd.concat([dft0_d, dft1_d])
####

dfsr = df[['Date','SolarRadiation']].copy()
dfsr['Date'] = pd.to_datetime(dft0['Date'], format='%Y-%m-%d %H:%M:%S')

dfsr['Date'] = dfsr['Date'] + datetime.timedelta(hours=12)
dfsr_d = dfsr.set_index('Date')

####

dfsm = dfs.resample('12H', loffset='5H', label='right').mean()
dfsm.index = dfsm.index + datetime.timedelta(hours=12)
dfsm = dfsm.rename(columns={'WaterTemperature': 'AveWaterTemperature'})

dft01 = dft01.rename(columns={'Temperature':'気温'})
dfsm = dfsm.rename(columns={'AveWaterTemperature':'センサ水温'})
dfwt01 = dfwt01.rename(columns={'WaterTemperatureModel':'モデル水温'})
dfsr_d = dfsr_d.rename(columns={'SolarRadiation':'日射量'})

if args.sensor_raw:
    dfc = pd.concat([dfs, dfsm, dfwt01, dft01], axis=1)
else:
    dfc = pd.concat([dfsm, dfwt01, dft01], axis=1)

if args.sunray:
    dfc = pd.concat([dfc, dfsr_d], axis=1)

dfc.to_csv('tmp_wtemper.csv', sep=',')

with open(args.commoninfo) as fci:
    jci = json.load(fci)

if args.begin is not None:
    sdate = datetime.datetime.strptime(args.begin,'%Y-%m-%d').date()
else:
    sdate = datetime.datetime.strptime(jci['schedule']['manure']['date'],'%Y-%m-%d').date()

_dfc = dfc[sdate:]

if args.finish is not None:
    edate = datetime.datetime.strptime(args.finish,'%Y-%m-%d').date()
else:
    edate = datetime.datetime.strptime(jci['schedule']['reaping_date']['date'],'%Y-%m-%d').date()

_dfc = _dfc[:edate]

dfc = _dfc
dfc = dfc.interpolate(method='time')

dfc.plot(title="水温の比較 ("+jci['field']['name']+")",
         figsize=(16,6),
         grid=True,
         linewidth = 3)

plt.ylabel('[℃]')
plt.show()
