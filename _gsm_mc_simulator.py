#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import json
from pathlib import Path
import argparse
import numpy as np
import pandas as pd

from models.gsm_base import GsmDriveBase
from models.gsm_microclimate import GsmMicroClimate
from models.gsm_plant_coverage import GsmPlantCoverage

__version__ = 'Alpha7.0.0dev'

class gsm_mc_simulator(GsmDriveBase):
    def __init__(self, BeginDay, FinishDay, WeatherDb, WaterFluxDb, CommonInfo, Output):
        #クラスのインスタンス化
        self.gpc = GsmPlantCoverage()
        self.gmc = GsmMicroClimate()

        self.runList = [self.gpc, self.gmc]
        self.BeginDay = BeginDay
        self.FinishDay = FinishDay
        self.WeatherDb = WeatherDb
        self.WaterFluxDb = WaterFluxDb
        self.CommonInfo = CommonInfo
        self.Output = Output
        self.Database = self.create_initdb(self.runList, BeginDay, FinishDay)

    def _read_files(self):
        # 3次メッシュの気象データ読み込み
        self.dw = pd.read_csv(self.WeatherDb, parse_dates=True, index_col='Date', comment='#')

        # 入落水量および入水温度データの読み込み
        self.dwf = pd.read_csv(self.WaterFluxDb, parse_dates=True, index_col='Date', comment='#')

        #read common_info.json
        with open(self.CommonInfo) as fci:
            self.jci = json.load(fci)

        self.dfc = None

    def _setting_initial_values(self, y_day, t_day, e_day):
        pass

    def run(self):
        self._read_files()
        self.df = self.Database

        ### SIM開始／終了日の定義
        if self.BeginDay != None:
            _begin_date = datetime.datetime.strptime(self.BeginDay,'%Y-%m-%d')
        else:
            _begin_date = datetime.date.today()
        print("begin_date:",_begin_date)

        if self.FinishDay != None:
            _finish_date = datetime.datetime.strptime(self.FinishDay,'%Y-%m-%d')
        else:
            ta = self.df.tail(n=1)
            _finish_date = ta.index[0].date()

        print('finish_date:', _finish_date)

        _sim_begin_date = _begin_date - datetime.timedelta(hours=1)
        sd = self.df[_sim_begin_date:_finish_date]

        #微気象モデル　圃場パラメタの登録
        self.gmc.setLocalConstant(self.jci['microclimate']['localConstant'])
        self.gmc.setGlobalConstant(self.jci['microclimate']['globalConstant'])
        self.gmc.setFieldPosition(self.jci['field']['position'])

        #単純作物モデル　パラメタ登録
        self.gpc.setCoverageParams(self.jci['schedule']['crop_growth'])

        #気象データをSIM-DBに登録
        self.df['AirTemperature'] = np.nan
        self.df['Rainfall'] = np.nan
        self.df['Wind'] = np.nan
        self.df['SolarRadiation'] = np.nan
        self.df['Humidity'] = np.nan
        self.df.update(self.dw)

        #入落水量および入水温度をSIM-DBに登録
        self.df['WFLXinlet'] = np.nan
        self.df['WFLXoutlet'] = np.nan
        self.df['TMPWin'] = np.nan
        self.df.update(self.dwf)

        #initialization
        self.gmc.set_param(self.jci['microclimate']['initialValues'])

        ### シミュレーション
        self.simulate(sd.index.size, self.df, self.dfc, self.runList, self._setting_initial_values)

        if not self.Output == None: self.df.to_csv(self.Output)

def _debug(_dir='directory of field data', _dict='result DataFrame'):
    commoninfo = os.path.join(_dir, 'common_info.json')
    with open(commoninfo) as fci:
        jci = json.load(fci)
    _sdate = jci['schedule']['transplanting_date']['date']
    _edate = jci['schedule']['reaping_date']['date']
    weatherdb = os.path.join(Path(_dir).resolve().parents[1], 'weatherdb', 'w-' + jci['field']['mesh3code'] + '.csv')
    wfluxdb = os.path.join(_dir, 'wflux.csv')

    gsim = gsm_mc_simulator(_sdate, _edate, weatherdb, wfluxdb, commoninfo, None)
    gsim.run()
    _dict['result']=gsim.df

def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', action='store_true', help='output database')
    parser.add_argument('fd', help='directory of field data')
    args = parser.parse_args()

    commoninfo = os.path.join(args.fd, 'common_info.json')

    if os.path.isfile(commoninfo) == False :
        print("ERROR: no growth planning information file")
        sys.exit(1)
    outfp = os.path.join(args.fd, 'out.csv') if args.output else None

    with open(commoninfo) as fci:
        jci = json.load(fci)

    _sdate = jci['schedule']['transplanting_date']['date']
    _edate = jci['schedule']['reaping_date']['date']
    weatherdb = os.path.join(Path(args.fd).resolve().parents[1], 'weatherdb', 'w-' + jci['field']['mesh3code'] + '.csv')
    wfluxdb = os.path.join(args.fd, 'wflux.csv')

    gsim = gsm_mc_simulator(_sdate, _edate, weatherdb, wfluxdb, commoninfo, outfp)
    gsim.run()
    sys.exit(0)

if __name__ == '__main__':
    _main()
