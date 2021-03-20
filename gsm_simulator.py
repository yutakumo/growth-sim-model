import os
import sys
import datetime as dt
import json
import pandas as pd

from models import *

import make_ideal_gindex as mig
import tools.update_db.insert_aveweather as ins_aw

__version__ = 'Alpha7.0.0dev'

class gsm_simulator(GsmDriveBase):
    def __init__(self,
                 BeginDay, FinishDay,
                 AveWeather,ImSense,
                 InitValues, IdealDat, BaseWeather, WeatherDb, FcWeatherDb,
                 FieldSensDb, CommonInfo, Fertilizer, Coeff, CoeffCultivar,
                 WaterFlux,
                 Output,
                 HeadingDate='simulate', NoCheckMtime=False):
        #クラスのインスタンス化
        self.gcn = GsmCanopy()
        self.gwe = GsmWeather()
        self.gwm = GsmWaterManage()
        self.gmc = GsmMicroClimate()
        self.gso = GsmSoil()
        self.gf = GsmFertilizer()
        self.gc = GsmCarbon()
        self.grp = GsmRespiration()
        self.gs = GsmSucrose()
        self.gnb = GsmNitrogenBalance()
        self.gn = GsmNitrogen()
        self.gr = GsmRice()
        self.gg = GsmGrowth()

        self.ugw = GsmUtilWaterManage()

        self.runList = [self.gcn, self.gwe, self.gwm, self.gmc,
                        self.gso, self.gf, self.gnb, self.grp, self.gc, self.gs, self.gn, self.gr, self.gg]

        self.BeginDay = BeginDay
        self.FinishDay = FinishDay
        self.InitValues = InitValues
        self.IdealDat = IdealDat
        self.BaseWeather = BaseWeather
        self.WeatherDb = WeatherDb
        self.FcWeatherDb = FcWeatherDb
        self.FieldSensDb = FieldSensDb
        self.CommonInfo = CommonInfo
        self.Fertilizer = Fertilizer
        self.Coeff = Coeff
        self.CoeffCultivar = CoeffCultivar
        self.WaterFlux = WaterFlux
        self.Output = Output
        self.HeadingDate = HeadingDate
        self.NoCheckMtime = NoCheckMtime

        self.Database = None
        self.ImSense = ImSense
        self.AveWeather = AveWeather

        self.initialize_db()

    def initialize_db(self):
        if self.Database is not None:
            print("del DB")
            del self.Database
        self.Database = self.create_initdb(self.runList, self.BeginDay, self.FinishDay)
        self._set_imsense(self.Database, self.ImSense)
        self._set_aveweather(self.Database, self.AveWeather)

    def _set_imsense(self, df, imsdb):
        try:
            ims = pd.read_csv(imsdb, parse_dates=True, index_col='Date')
        except Exception as e:
            print(e), sys.exit(1)
        df['SenseRedAbsorptionRate'] = np.nan
        df['SenseEffectiveSunRayReceivingAreaRate'] = np.nan
        df.update(ims)

    def _set_aveweather(self, df, avewdb):
        try:
            dw = pd.read_csv(avewdb, parse_dates=True, index_col='Date', comment='#')
        except Exception as e:
            print(e), sys.exit(1)

        df['AveDaytimeTemperature'] = np.nan
        df['AveNighttimeTemperature'] = np.nan
        df['AveSolarRadiation'] = np.nan

        ins_aw.insertAverageWeatherData(df, dw)
        df['AveSolarRadiation'] = df['AveSolarRadiation'].fillna(method='ffill')

        adt, ant = np.nan, np.nan
        print(df['AveNighttimeTemperature'])
        for index, row in df.iterrows():
            if np.isnan(row['AveNighttimeTemperature']):
                df.at[index,'AveDaytimeTemperature'] = adt
                df.at[index,'AveNighttimeTemperature'] = ant
            else:
                adt = row['AveDaytimeTemperature']
                ant = row['AveNighttimeTemperature']
        print(df['AveNighttimeTemperature'])

    #モデルパラメータの読み込み
    def _read_coeff(self, jci):
        try:
            dfcc = pd.read_csv(self.Coeff, usecols=[1,2], index_col=0)
        except Exception as e:
            print(e), sys.exit(1)
        else:
            dfcc = dfcc.T.reset_index(drop=True)

        try:
            dfcb = pd.read_csv(self.CoeffCultivar, parse_dates=True, comment='#')
        except Exception as e:
            print(e), sys.exit(1)

        _cultivar = jci['planting']['cultivar']
        dfc = pd.concat([dfcc, dfcb[dfcb.Cultivar==_cultivar].reset_index()], axis=1)

        #print(df[df.index.duplicated(keep=False)])
        #print(dw[dw.index.duplicated(keep=False)])
        return dfc

    def _read_files(self):
        '''
        try:
            #データベースの読み込み
            self.df = pd.read_csv(self.Database, parse_dates=True, index_col='Date')
        except Exception as e:
            print(e), sys.exit(1)
        '''

        if self.FcWeatherDb is not None:
            try:
                #気象予報値の読み込み（ファイルパスで入力される）
                self.pdw = pd.read_csv(self.FcWeatherDb, parse_dates=True, index_col='Date', comment='#')
            except Exception as e:
                print(e), sys.exit(1)

        self.dw = None
        if self.BaseWeather is not None:
            try:
                #3次メッシュ外の気象値の読み込み（ファイルパスで入力される）
                self.dw = pd.read_csv(self.BaseWeather, parse_dates=True, index_col='Date', comment='#')
            except Exception as e:
                print(e), sys.exit(1)

        if self.WeatherDb is not None: #3次メッシュの気象値の読み込み（ファイルパスで入力される）
            try:
                _dw = pd.read_csv(self.WeatherDb, parse_dates=True, index_col='Date', comment='#')
            except Exception as e:
                print(e), sys.exit(1)

            if self.dw is not None:
                self.dw = pd.concat([self.dw, _dw])
            else:
                self.dw = _dw
        print(self.dw)

        #栽培情報の入力
        print(self.CommonInfo)
        try:
            with open(self.CommonInfo) as fci:
                self.jci = json.load(fci)
        except Exception as e:
            print(e), sys.exit(1)

        #肥料情報の読み込み
        try:
            with open(self.Fertilizer) as ff:
                self.jf = json.load(ff)
        except Exception as e:
            print(e), sys.exit(1)

        self.dfc = self._read_coeff(self.jci)

        # 入落水量および入水温度データの読み込み
        try:
            self.dwf = pd.read_csv(self.WaterFlux, parse_dates=True, index_col='Date', comment='#')
        except Exception as e:
            print(e), sys.exit(1)

    def _set_water_manage_param(self, jci):
        print(jci['water_management']['water_supply_source'])
        self.gwm.set_water_supply_source(jci['water_management']['water_supply_source'])
        if jci['water_management'].get('ground_water_temperature', None) != None:
            self.gwm.set_ground_water_temperature(jci['water_management']['ground_water_temperature'])

        self.gwm.set_Winlet_time(jci['water_management']['water_entry_time'])
        self.gwm.set_volume_of_Winlet(float(jci['water_management']['water_supply']))
        if 'water_drain' in jci['water_management']:
            self.gwm.set_volume_of_Woutlet(float(jci['water_management']['water_drain']))
        if 'start_water_depth_rate' in jci['water_management']:
            self.gwm.set_th_water_depth_rate(float(jci['water_management']['start_water_depth_rate']))
        self.gwm.set_volume_of_Winlet(int(jci['water_management']['water_supply']))
        self.gwm.set_area_of_field(jci['field']['area'])

    def _is_start_cultivation(self, y_day, t_day, e_day):
        return (self._pmethod == "transplantation" and y_day == self._init_date) or (e_day > 1 and self._pmethod == "direct_sowing" and self.gg.is_seedling_date())

    def _set_initial_values(self, y_day):
        print("set initial values")
        self._idf['Date'] = y_day
        idf = self._idf.set_index('Date')
        idf = idf.dropna(axis=1, how='all')
        self.df.update(idf)
        yd = self.df[y_day:y_day]
        ydd = yd.to_dict()
        self.gs.set_timebase_db(ydd, yd.index)
        self.gs.set_coeff_db(self.dfc)
        self.gs.calc_init_surface_area_of_leaf_blade()
        self.gs.calc_init_surface_area_of_rootage()
        self.gs.calc_w_total()
        self.gs.update_timebase_db()
        ydn = pd.DataFrame(ydd)
        self.df.update(ydn)

    def _setting_initial_values(self, y_day, t_day, e_day):
        if self._is_start_cultivation(y_day, t_day, e_day):
            self._set_initial_values(y_day)

    def run(self):
        self._read_files()
        self.df = self.Database

        ### SIM開始／終了日の定義
        if self.BeginDay != None:
            _begin_date = dt.datetime.strptime(self.BeginDay,'%Y-%m-%d')
        else:
            _begin_date = dt.date.today()
        print("begin_date:",_begin_date)

        if self.FinishDay != None:
            _finish_date = dt.datetime.strptime(self.FinishDay,'%Y-%m-%d')
        else:
            ta = self.df.tail(n=1)
            _finish_date = ta.index[0].date()

        print('finish_date:', _finish_date)

        _sim_begin_date = _begin_date - dt.timedelta(hours=1)
        sd = self.df[_sim_begin_date:_finish_date]
        index_date = sd.index
        len_date = sd.index.size

        #水管理情報パラメータの設定
        self._set_water_manage_param(self.jci)

        #水管理情報の更新
        self.df = self.ugw.set_schedule_of_water_management(self.jci, self.df)

        self.gs.set_planting_density(self.jci['planting']['density'])

        if self.jci.get('sensing', None) != None and 'lodging' in self.jci['sensing']:
            self.gc.set_lodging(self.jci['sensing']['lodging'])

        _sch_fertilizer = []
        if self.jci['schedule'].get('ground_fertilizer_date') is not None and len(self.jci['schedule']['ground_fertilizer_date']) > 0:
            _sch_fertilizer.append(self.jci['schedule']['ground_fertilizer_date'])

        #作物の初期値設定
        ## set initial values
        try:
            self._idf = pd.read_csv(self.InitValues)
        except Exception as e:
            print(e), sys.exit(1)
        self._pmethod = self.jci['planting']['method']

        #初期値は栽植密度で調整
        _plant_density_rate = float(self.jci['planting']['density']) / 16.0
        self._idf['WeightLeafBlade'] = self._idf['WeightLeafBlade'] * _plant_density_rate
        self._idf['WeightRootage'] = self._idf['WeightRootage'] * _plant_density_rate
        self._idf['WeightTotal'] = self._idf['WeightLeafBlade'] + self._idf['WeightRootage']
        self._idf['SumOfNitrogenDistributionAmountOfLeafBlade'] = self._idf['SumOfNitrogenDistributionAmountOfLeafBlade'] * _plant_density_rate
        self._idf['EffectiveSunRayReceivingAreaRate'] = self._idf['EffectiveSunRayReceivingAreaRate'] * _plant_density_rate

        _pm_date = {'direct_sowing': 'sowing_date', 'transplantation': 'transplanting_date'}
        self._init_date = dt.datetime.strptime(self.jci['schedule'][_pm_date[self._pmethod]]['date'],'%Y-%m-%d')
        self._init_date = self._init_date - dt.timedelta(hours=1)

        # センシングの理想推移を計算し，SIM-DBに登録
        ## set ideal growth-index
        try:
            _bdat = pd.read_csv(self.IdealDat)
        except Exception as e:
            print(e), sys.exit(1)
        sdate = self._init_date + dt.timedelta(days=1)
        edate = dt.datetime.strptime(self.jci['schedule']['reaping_date']['date'],'%Y-%m-%d') + dt.timedelta(hours=23)
        print(sdate, edate)

        _idat = mig.make_ideal_gindex(sdate, edate, _bdat)
        self.df = pd.concat([self.df, _idat], axis=1)

        if self.jci['schedule'].get('additional_fertilizer_date', None) != None:
            _sch_fertilizer.extend(self.jci['schedule']['additional_fertilizer_date'])

        for i in range(len(_sch_fertilizer)):
            for j in range(len(self.jf)):
                if _sch_fertilizer[i]['fertilizer_id'] == self.jf[j]['id']:
                    _sch_fertilizer[i].update(self.jf[j])

        #微気象モデル　圃場パラメタの登録
        self.gmc.setLocalConstant(self.jci['microclimate']['localConstant'])
        self.gmc.setGlobalConstant(self.jci['microclimate']['globalConstant'])
        self.gmc.setFieldPosition(self.jci['field']['position'])

        #栽培スケジュールの設定
        print("type of heading date is",self.HeadingDate)
        if self.HeadingDate != 'simulate':
            _heading_date = None
            if self.HeadingDate == 'fix':
                _heading_date = self.jci['schedule']['heading_date']['date']
            elif self.HeadingDate == 'predict':
                _heading_date = self.jci['schedule']['heading_predicted_date']['date']
            gg.set_heading_date(_heading_date)
            print("heading date is ", _heading_date)

        #窒素データを各モデルに設定
        self.gf.set_sn_feritilizer_info(_sch_fertilizer)
        self.gnb.set_sn_manure_info(self.jci['schedule']['manure'])
        self.gnb.set_water_supply_nitrogen_content(self.jci['water_management']['water_supply_nitrogen_content'])

        #気象データをSIM-DBに登録
        self.df['AirTemperature'] = np.nan
        self.df['Rainfall'] = np.nan
        self.df['Wind'] = np.nan
        self.df['SolarRadiation'] = np.nan
        self.df['Humidity'] = np.nan
        if self.FcWeatherDb is not None:
            self.df.update(self.pdw)
        self.df.update(self.dw)

        self.df['AveDiffTemperature'] = self.df['AveDaytimeTemperature'] - self.df['AveNighttimeTemperature']

        #肥料の無機化状態を格納するアイテムをDBに追加
        ccount, ocount = 0, 0
        for i in range(len(_sch_fertilizer)):
            _snfi_coated = _sch_fertilizer[i]['coated_fertilizer']
            for j in range(len(_snfi_coated)):
                _key = 'CoatedFertilizerElutionDays_' + str(ccount)
                ccount += 1
                self.df[_key] = 0
                print('Added Key:', _key, _snfi_coated[j]['80_persent_elution'], _snfi_coated[j]['rate'] / 100)

            _snfi_organic = _sch_fertilizer[i]['organic_fertilizer']
            for j in range(len(_snfi_organic)):
                _key = 'OrganicFertilizerElutionDays_' + str(ocount)
                self.df[_key] = 0
                _key = 'SumOfSnOrganicFertilizer_' + str(ocount)
                self.df[_key] = 0
                ocount += 1
                print('Added Key:', _key, _snfi_organic[j]['rate'] / 100)


        self.df['cgsm-version'] = __version__

        self.df['OrganicDecompositionElutionDays'] = 0
        self.df['SumOfSnOrganicDecomposition'] = 0

        #表示用に画像センシング値だけのアイテムとセンシング値間を線形補間したアイテムを分ける
        df_idealgindex = self.df[['IdealRedAbsorptionRate','IdealEffectiveSunRayReceivingAreaRate']]
        df_idealgindex = df_idealgindex.interpolate(limit_area='inside')

        df_sensing = self.df[['SenseRedAbsorptionRate','SenseEffectiveSunRayReceivingAreaRate']]
        df_sensing_org = df_sensing.copy()
        df_sensing_org = df_sensing_org.rename(columns={'SenseRedAbsorptionRate':'SenseRedAbsorptionRate_ORG'})
        df_sensing_org = df_sensing_org.rename(columns={'SenseEffectiveSunRayReceivingAreaRate':'SenseEffectiveSunRayReceivingAreaRate_ORG'})
        df_sensing = df_sensing.interpolate(limit_area='inside')
        self.df = self.df.drop(['SenseRedAbsorptionRate','SenseEffectiveSunRayReceivingAreaRate'], axis=1)
        #self.df = self.df.fillna(0)

        #入落水量および入水温度をSIM-DBに登録
        self.df['WFLXinlet'] = np.nan
        self.df['WFLXoutlet'] = np.nan
        self.df['TMPWin'] = np.nan
        self.df.update(self.dwf)

        #圃場センシング値のDB登録．１時間ごとのデータになるように加工してから登録
        self.df['SensorAirTemperature'] = None
        self.df['SensorWaterDepth'] = None
        self.df['SensorWaterTemperature'] = None
        self.df['SensorSoilTemperature'] = None
        if self.FieldSensDb is not None:
            try:
                dfs = pd.read_csv(self.FieldSensDb, parse_dates=True, index_col='Date', comment='#')
            except Exception as e:
                print(e), sys.exit(1)
            dfs = dfs.resample('10T').interpolate(limit=6*6)
            dfs = dfs.resample('H').interpolate(limit=6)
            self.df.update(dfs)

        self.df.update(df_sensing)
        self.df.update(df_idealgindex)
        self.df = pd.concat([self.df, df_sensing, df_sensing_org], axis=1)

        #initialization
        self.gmc.set_param(self.jci['microclimate']['initialValues']['waterTemperature'],
                           self.jci['microclimate']['initialValues']['soilTemperature'],
                           self.jci['microclimate']['initialValues']['waterDepthmm']
                           )

        ### シミュレーション
        self.simulate(sd.index.size, self.df, self.dfc, self.runList, self._setting_initial_values)

        self.df['DiffTemperature'] = self.df['DaytimeTemperature'] - self.df['NighttimeTemperature']
        self.df['SumDSolarRadiation'] = self.df['SolarRadiation'].resample('D').sum()
        self.df['SumDSolarRadiation'] = self.df['SumDSolarRadiation'].fillna(method='ffill')
        self.df['SumNitrogenAssimilation'] = self.df['NitrogenAssimilation'].cumsum()
        self.df['eWDPmm'] = self.df['eWDPcm'] * 10.0
        self.df['WaterTemperature'] = self.df['eTMPW'] - 273.15
        self.df['SoilTemperature'] = self.df['eTMPS'] - 273.15

        self.df.to_csv(self.Output)

def _main():

    parser = argparse.ArgumentParser()

    parser.add_argument('-b', '--begin',
                        help='beginning date of simulator')
    parser.add_argument('-f', '--finish',
                        help='finishing date of simulator')
    parser.add_argument('-iv', '--initvalues', default='./global_param/init_db.csv',
                        help='path of input initial database')
    parser.add_argument('-o', '--output', default='./out.csv',
                        help='path of output database')
    parser.add_argument('-c', '--coeff', default='./global_param/coeff.csv',
                        help='path of coeffiecient database')
    parser.add_argument('-cb', '--coeffcultivar', default='./global_param/coeff_cultivar.csv',
                        help='path of cultivar specific coeffiecient database')
    parser.add_argument('-bw', '--baseweather',
                        help='path of base weather information database')
    parser.add_argument('-w', '--weatherdb',
                        help='path of weather information database')
    parser.add_argument('-wfc', '--fcweatherdb',
                        help='path of weather forcast information database')
    parser.add_argument('-frtl', '--fertilizer', default='./global_param/fertilizer.json',
                        help='path of fertilizer information file')
    parser.add_argument('-ci', '--commoninfo', default='./sampledat/common_info.json',
                        help='path of growth planning information file')
    parser.add_argument('-wf', '--waterflux', default='./sampledat/wflux.csv',
                        help='path of water flux information file')
    parser.add_argument('-hd', '--headingdate', choices=['fix', 'predict', 'simulate'], default='simulate',
                        help='select kind of heading date')
    parser.add_argument('-aw', '--aveweatherdb', default='./sampledat/shirochi_summarize.csv',
                        help='path of average weather information database')
    parser.add_argument('-fs', '--fieldsensor',
                        help='path of field sensor data')
    parser.add_argument('-is', '--imsense', default='./sampledat/imsense.csv',
                        help='path of image sensing database')
    parser.add_argument('-id', '--idealdat', default='./global_param/base_ideal_gindex.csv',
                        help='path of base ideal gindex data')

    parser.add_argument('-gd', '--globaldir',
                        help='directory of global data')
    parser.add_argument('-fd', '--fielddir',
                        help='directory of field data')
    parser.add_argument('-wd', '--weatherdir',
                        help='directory of weather data')

    parser.add_argument('-nufs', '--nousefieldsensor', action='store_true')

    parser.add_argument('-nocmt', '--nocheckmtime', action='store_true',
                        help='no check mtime of growth planning information file and database')

    args = parser.parse_args()

    if args.globaldir is not None:
        initvalues = args.globaldir + '/init_db.csv'
        coeff = args.globaldir + '/coeff.csv'
        coeffcultivar = args.globaldir + '/coeff_cultivar.csv'
        idealdat = args.globaldir + '/base_ideal_gindex.csv'
    else:
        initvalues = args.initvalues
        coeff = args.coeff
        coeffcultivar = args.coeffcultivar
        idealdat = args.idealdat
    fertilizer = args.fertilizer

    weatherdb = None
    if args.fielddir is not None:
        baseweather = args.fielddir + '/weatherdb.csv'
        imsense = args.fielddir + '/imsense.csv'
        commoninfo = args.fielddir + '/common_info.json'
        output = args.fielddir + '/out_gsm_db.csv'
        fieldsensor = args.fielddir + '/fieldsensor.csv'
        fcweatherdb = args.fielddir + '/weatherdb_fc.csv'
        wflux = args.fielddir + '/wflux.csv'
        if os.path.isfile(fieldsensor) == False or args.nousefieldsensor == True:
            fieldsensor = None
        if os.path.isfile(fcweatherdb) == False:
            fcweatherdb = None
        if os.path.isfile(baseweather) == False:
            baseweather = None
    else:
        baseweather = args.baseweather
        weatherdb = args.weatherdb
        fcweatherdb = args.fcweatherdb
        imsense = args.imsense
        commoninfo = args.commoninfo
        output = args.output
        fieldsensor = args.fieldsensor
        wflux = agrgs.watrerflux

    if os.path.isfile(coeff) == False :
        print("ERROR: no input coeffiecient database")
        sys.exit(1)

    if os.path.isfile(coeffcultivar) == False :
        print("ERROR: no input cultivar specific coeffiecient database")
        sys.exit(1)

    if os.path.isfile(fertilizer) == False :
        print("ERROR: no fertilizer information file")
        sys.exit(1)

    if os.path.isfile(commoninfo) == False :
        print("ERROR: no growth planning information file")
        sys.exit(1)

    with open(commoninfo) as fci:
        jci = json.load(fci)

    if args.begin is not None:
        _sdate = args.begin
    else:
        _plant_method = {'direct_sowing': 'sowing_date', 'transplantation': 'transplanting_date'}
        plant_method = _plant_method[jci['planting']['method']]
        _sdate = jci['schedule']['manure']['date']

    if args.finish is not None:
        _edate = args.finish
    elif 'date' in jci['schedule']['reaping_date']:
        _edate = jci['schedule']['reaping_date']['date']
    else:
        _edate = None

    if args.weatherdir is not None and jci['field'].get('mesh3code') is not None:
        weatherdb = args.weatherdir + '/w-' + jci['field']['mesh3code'] + '.csv'
        fcweatherdb = args.weatherdir + '/fcw-' + str(jci['field']['mesh3code']) + '.csv'

    fci.close()
    #database = _create_initdb(args.initvalues, _sdate, _edate, args.aveweatherdb, imsense)

    gsim = gsm_simulator(_sdate, _edate,
                         args.aveweatherdb, imsense,
                         initvalues, args.idealdat, baseweather, weatherdb, fcweatherdb,
                         fieldsensor, commoninfo, fertilizer,
                         coeff, coeffcultivar, wflux, args.output,
                         args.headingdate, args.nocheckmtime)
    gsim.run()

    sys.exit(0)

if __name__ == '__main__':
    import argparse
    import numpy as np
    _main()
