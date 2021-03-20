import math
import datetime
import pandas as pd

from .gsm_base import GsmBase

class GsmWaterManage(GsmBase):

    def __init__(self):
        self.WaterSupplySource = None
        self.GroundWaterTemperature = 15.0 # default ground water Temperature
        self.RiverWaterTemperatureDiff = -3.0
        self.WaterRequirementRate = 0
        self.MaxWaterDepth = 1000 # default is 1 meter
        self.thWaterDepthRate = 0.8
        self.targetWaterDepth = None

        self.InletTime = None
        self.OutletTime = None

        self.VolumeOfInlet = None
        self.VolumeOfOutlet = None

        self.Items = {'StartInlet':0, 'eWFLXinlet':0,
                      'StartOutlet':0, 'eWFLXoutlet':0,
                      'eTMPWin':0}
    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):
        self.check_starting_inlet()
        self.calc_inlet()
        self.check_starting_outlet()
        self.calc_outlet()

        self.update_timebase_db()
        self.count_up_time()

    ###
    def set_water_supply_source(self, wss):
        self.WaterSupplySource = wss

    def set_ground_water_temperature(self, wss):
        self.GroundWaterTemperature = wss

    def set_water_requirement_rate(self, wrr):
        self.WaterRequirementRate = wrr

    def set_Winlet_time(self, st):
        self.InletTime = datetime.datetime.strptime(st,'%H:%M:%S').time()
        if self.OutletTime is None:
            self.OutletTime = datetime.datetime.strptime(st,'%H:%M:%S').time() # default value

    def set_Woutlet_time(self, st):
        self.OutletTime = datetime.datetime.strptime(st,'%H:%M:%S').time()

    def set_volume_of_Winlet(self, vsw): # [L/s]
        self.VolumeOfInlet = vsw * 3600 / 1000 # [/hour /m3]
        if self.VolumeOfOutlet is None:
            self.VolumeOfOutlet = vsw * 3600 / 1000 # [/hour /m3]  # default value

    def set_volume_of_Woutlet(self, vdw): # [L/s]
        self.VolumeOfOutlet = vdw * 3600 / 1000 # [/hour /m3]

    def set_max_water_depth(self, depth):
        self.MaxWaterDepth = depth

    def set_area_of_field(self, area):
        self.AreaOfField = area

    def set_thresh_water_depth_rate(self, depth_rate):
        self.thWaterDepthRate = depth_rate

    ###
    def isInletTime(self):
        return self.TimeBaseDT[self.idx_time].time() == self.InletTime

    def isOutletTime(self):
        return self.TimeBaseDT[self.idx_time].time() == self.OutletTime

    ###
    def check_starting_inlet(self):
        _p_water_depth = self.get_time_dat('eWDPcm', True) * 10.0
        _target_water_depth = self.get_time_dat('TargetWaterDepth')
        _p_start_inlet = self.get_time_dat('StartInlet', True)
        if _p_start_inlet == 0 and self.isInletTime() and _p_water_depth < _target_water_depth * self.thWaterDepthRate:
            _start_inlet = 1
        else:
            _start_inlet = _p_start_inlet
        self.Items['StartInlet'] = _start_inlet

    def calc_inlet(self):
        if self.Items['StartInlet'] == 1:
            _p_water_depth = self.get_time_dat('eWDPcm', True) * 10.00
            _target_water_depth = self.get_time_dat('TargetWaterDepth')
            _type_of_irrigation = self.get_time_dat('IrrigationType')

            if (_type_of_irrigation == 'flow' or _target_water_depth > 0) and _p_water_depth < _target_water_depth :
                _inlet = self.VolumeOfInlet / self.AreaOfField * 1000
            else:
                _inlet = 0
                self.Items['StartInlet'] = 0
        else:
            _inlet = 0
        self.Items['eWFLXinlet'] = _inlet

        if self.WaterSupplySource == 'river':
            _water_temperature = self.get_time_dat('NighttimeTemperature') + self.RiverWaterTemperatureDiff
        else:
            _water_temperature = self.GroundWaterTemperature
        self.Items['eTMPWin'] = _water_temperature + 273.15

    def check_starting_outlet(self):
        _p_start_outlet = self.get_time_dat('StartOutlet', True)
        _p_water_depth = self.get_time_dat('eWDPcm', True) * 10.0
        _target_water_depth = self.get_time_dat('TargetWaterDepth')
        if _p_start_outlet == 0 and self.isOutletTime() and _target_water_depth < 0:
            _start_outlet = 1
            self.targetWaterDepth = 0
        elif _p_start_outlet == 0 and _p_water_depth > self.get_time_dat('MaxWaterDepth'):
            self.targetWaterDepth = self.get_time_dat('MaxWaterDepth')
            _start_outlet = 1
        else:
            _start_outlet = _p_start_outlet
        self.Items['StartOutlet'] = _start_outlet

    def calc_outlet(self):
        _type_of_irrigation = self.get_time_dat('IrrigationType')
        if _type_of_irrigation == 'flow' or self.Items['StartOutlet'] == 1:
            _p_water_depth = self.get_time_dat('eWDPcm', True) * 10.0
            if _p_water_depth > self.targetWaterDepth:
                _outlet = self.VolumeOfOutlet / self.AreaOfField * 1000
            else:
                _outlet = 0
                self.Items['StartOutlet'] = 0
        else:
            _outlet = 0
        self.Items['eWFLXoutlet'] = _outlet

class GsmUtilWaterManage:

    def set_schedule_of_water_management(self, jci, df):

        if 'max_water_depth' in jci['water_management']:
            df['MaxWaterDepth'] = int(jci['water_management']['max_water_depth'])
        else:
            df['MaxWaterDepth'] = 1000 # default is 1 meter

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


def _main():

    df = pd.read_csv('./36.25913074_140.0676563.csv', parse_dates=True, index_col='Date')
    df = df.fillna(0)
    #dfc = pd.read_csv('./sampledat/coeff.csv', parse_dates=True, index_col='Date', comment='#')

    print(f"raw is {df.index.size}")

    gw = GsmWater()
    gw.set_water_supply_source('river')
    gw.set_water_requirement_rate(15)
    gw.set_volume_of_inlet(100)
    gw.set_area_of_field(50)
    gw.set_source_time('6:00:00')

    c_df = df[0:24]
    c_dfd = c_df.to_dict()
    gw.set_timebase_db(c_dfd, c_df.index)
    gw.calculate()
    uc_df = pd.DataFrame(c_dfd)
    df.update(uc_df)

    n_row = df.index.size
    head_date = df.index[0].date()
    tail_date = df.index[n_row-1].date()
    n_day = tail_date - head_date

    for i in range(1, n_row-1, 24):
        c_day = head_date + datetime.timedelta(days=i)
        c_df = df[i-1:i+24]
        c_dfd = c_df.to_dict()
        gw.set_timebase_db(c_dfd, c_df.index)

        '''
        c_day = head_date + datetime.timedelta(days=i+1)
        c_df = df[p_day.strftime('%Y-%m-%d')]
        c_dfd = c_df.to_dict()
        gw.set_current_db(c_dfd, c_df.index[0])
        #gw.set_coeff_db(tc)
        '''
        gw.calculate()

        uc_df = pd.DataFrame(c_dfd)
        df.update(uc_df)

    df.to_csv('t.new.csv')

if __name__ == '__main__':
    _main()
