import math
import datetime
import pandas as pd

from .gsm_base import GsmBase

class GsmWeather(GsmBase):

    def __init__(self):
        self.WaterSupplySource = None
        self.GroundWaterTemperature = 15.0 # default ground water Temperature
        self.RiverWaterTemperatureDiff = -3.0
        self.WaterRequirementRate = 0
        self.MaxWaterDepth = 1000 # default is 1 meter
        self.startWaterDepthRate = 0.8
        self.targetWaterDepth = None
        self.AirTemperature = None

        self.SourceTime = None
        self.DrainTime = None

        self.VolumeOfSourceWater = None
        self.VolumeOfDrainWater = None

        self.Osmosis = None

        self.HeatSpecificOfWater = 4.19 # [J/g/K]
        self.HeatTransferCoeffOfAir = 0.022 # [W/m/K]

        self.Items = {'TimeSunset':0, 'TimeSunrise':0, 'SumOfAirTemperature':0, 'DaytimeTemperature':0, 'NighttimeTemperature':0,
                      'HumidityDeficit':0}

    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):
        self.get_air_temperature()
        self.calc_sunset_sunrise()
        self.calc_ave_air_temperature()
        self.calc_humidity_deficit()

        self.update_timebase_db()
        self.count_up_time()

    ###
    def get_air_temperature(self):
        self.AirTemperature = None
        if self.check_key('SensorAirTemperature'):
            self.AirTemperature = self.get_time_dat('SensorAirTemperature')
        if self.AirTemperature == None:
            self.AirTemperature = self.get_time_dat('AirTemperature')
    ###
    def calc_sunset_sunrise(self):
        _p_time_sunset = self.get_time_dat('TimeSunset', True)
        _p_time_sunrise = self.get_time_dat('TimeSunrise', True)
        if self.check_sunset():
            self.Items['TimeSunset'] = self.TimeBaseDT[self.idx_time].strftime("%H")
            self.Items['TimeSunrise'] = _p_time_sunrise
        elif self.check_sunrise():
            self.Items['TimeSunset'] = _p_time_sunset
            self.Items['TimeSunrise'] = self.TimeBaseDT[self.idx_time].strftime("%H")
        else:
            self.Items['TimeSunset'] = _p_time_sunset
            self.Items['TimeSunrise'] = _p_time_sunrise

    def calc_ave_air_temperature(self):
        _air_temperature = self.AirTemperature
        if self.check_sunset():
            _day_time = int(self.Items['TimeSunset']) - int(self.Items['TimeSunrise'])
            self.Items['DaytimeTemperature'] = self.Items['SumOfAirTemperature'] / _day_time
            self.Items['SumOfAirTemperature'] = _air_temperature
        elif self.check_sunrise():
            _night_time = 24 + int(self.Items['TimeSunrise']) - int(self.Items['TimeSunset'])
            self.Items['NighttimeTemperature'] = self.Items['SumOfAirTemperature'] / _night_time
            self.Items['SumOfAirTemperature'] = _air_temperature
        else:
            self.Items['NighttimeTemperature'] = self.get_time_dat('NighttimeTemperature', True)
            self.Items['SumOfAirTemperature'] += _air_temperature

    def calc_humidity_deficit(self):
        _air_temperature = self.AirTemperature
        _humidty = self.get_time_dat('Humidity')
        _vapor_pressure = 6.1078 * 10 ** ((7.5 * _air_temperature / (_air_temperature + 237.3)))
        _saturation_water_vapor_pressure = 217.0 * _vapor_pressure / (_vapor_pressure + 273.15)
        self.Items['HumidityDeficit'] = (100.0 - _humidty) * _saturation_water_vapor_pressure / 100.0

def _main():

    df = pd.read_csv('./36.25913074_140.0676563.csv', parse_dates=True, index_col='Date')
    df = df.fillna(0)
    #dfc = pd.read_csv('./sampledat/coeff.csv', parse_dates=True, index_col='Date', comment='#')

    print(f"raw is {df.index.size}")

    gw = GsmWater()
    gw.set_water_supply_source('river')
    gw.set_water_requirement_rate(15)
    gw.set_volume_of_source_water(100)
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
