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
from models.gsm_weather import GsmWeather
from models.gsm_water_manage import GsmWaterManage

__version__ = 'Alpha7.0.0dev'

class gsm_mc_simulator(GsmDriveBase):
    def __init__(self, BeginDay, FinishDay, WeatherDb, WaterFluxDb, CommonInfo, Output):
        #クラスのインスタンス化
        self.gpc = GsmPlantCoverage()
        self.gmc = GsmMicroClimate()
        self.gwe = GsmWeather()
        self.gwm = GsmWaterManage()

        self.runList = [self.gwe, self.gwm, self.gpc, self.gmc]
        self.BeginDay = BeginDay
        self.FinishDay = FinishDay
        self.WeatherDb = WeatherDb
        self.WaterFluxDb = WaterFluxDb
        self.CommonInfo = CommonInfo
        self.Output = Output
        self.Database = self.create_initdb(self.runList, BeginDay, FinishDay)

    #水管理部分の読み込みデータ格納
    def _set_schedule_of_water_management(self, jci, df):
        asize = len(jci['water_management']['schedule'])

        for i in range(asize):
            s_date = datetime.datetime.strptime(jci['water_management']['schedule'][i]['start'],'%Y-%m-%d')
            e_date = datetime.datetime.strptime(jci['water_management']['schedule'][i]['end'],'%Y-%m-%d')
            depth = jci['water_management']['schedule'][i]['depth']
            if 'type' in jci['water_management']['schedule'][i]:
                _type = jci['water_management']['schedule'][i]['type']
            else:
                _type = 'normal'

            _s_date = s_date + datetime.timedelta(hours=6)
            _e_date = e_date + datetime.timedelta(hours=6+23)
            print(_s_date, _e_date, depth)
            df.loc[_s_date: _e_date,'TargetWaterDepth'] = depth
            df.loc[_s_date: _e_date,'IrrigationType'] = _type
            if 'type' in jci['water_management']['schedule'][i] and jci['water_management']['schedule'][i]['type'] == "flow":
                df.loc[_s_date: _e_date,'MaxWaterDepth'] = 0
            elif 'max_depth' in jci['water_management']['schedule'][i]:
                df.loc[_s_date: _e_date,'MaxWaterDepth'] = jci['water_management']['schedule'][i]['max_depth']
        return df

    def _set_water_manage_param(self, jci):
        print(jci['water_management']['water_supply_source'])
        self.gwm.set_water_supply_source(jci['water_management']['water_supply_source'])
        if jci['water_management'].get('ground_water_temperature', None) != None:
            self.gwm.set_ground_water_temperature(jci['water_management']['ground_water_temperature'])

        self.gwm.set_Winlet_time(jci['water_management']['water_entry_time'])
        self.gwm.set_volume_of_Winlet(float(jci['water_management']['water_supply']))
        if 'water_drain' in jci['water_management']:
            self.gwm.set_volume_of_Woutlet(float(jci['water_management']['water_drain']))
        if 'max_water_depth' in jci['water_management']:
            self.df['MaxWaterDepth'] = int(jci['water_management']['max_water_depth'])
        else:
            self.df['MaxWaterDepth'] = 1000 # default is 1 meter
        if 'start_water_depth_rate' in jci['water_management']:
            self.gwm.set_th_water_depth_rate(float(jci['water_management']['start_water_depth_rate']))
        self.gwm.set_volume_of_Winlet(int(jci['water_management']['water_supply']))
        self.gwm.set_area_of_field(jci['field']['area'])

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

        #水管理情報パラメータの設定
        self._set_water_manage_param(self.jci)

        #水管理情報の更新
        self.df = self._set_schedule_of_water_management(self.jci, self.df)

        #initialization
        self.gmc.set_param(self.jci['microclimate']['initialValues']['waterTemperature'],
                           self.jci['microclimate']['initialValues']['soilTemperature'],
                           self.jci['microclimate']['initialValues']['waterDepthmm']
                           )


        ### シミュレーション
        self.simulate(sd.index.size, self.df, self.dfc, self.runList, self._setting_initial_values)

        if not self.Output == None: self.df.to_csv(self.Output)

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
