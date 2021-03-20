import math
import datetime
import pandas as pd

from .gsm_base import GsmBase

class GsmWater(GsmBase):

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
                      'HumidityDeficit':0,
                      'StartSourceWater':0, 'SourceWater':0,
                      'StartDrainWater':0, 'DrainWater':0,
                      'EvaporationFromWaterSurface':0, 'EvaporationFromLeafSurface':0, 'Osmosis':0,
                      'WaterDepth':0, 'eTMPW':0}

    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):
        self.get_air_temperature()
        self.calc_sunset_sunrise()
        self.calc_ave_air_temperature()
        self.calc_humidity_deficit()

        self.check_starting_source_water()
        self.calc_source_water()
        self.check_starting_drain_water()
        self.calc_drain_water()
        self.calc_evaporation_from_water()
        self.calc_evaporation_from_leaf_surface()
        self.calc_osmosis()
        self.calc_water_depth()
        self.calc_water_temperature()

        self.update_timebase_db()
        self.count_up_time()

    ###
    def get_air_temperature(self):
        self.AirTemperature = self.get_time_dat('SensorAirTemperature')
        if self.AirTemperature == None:
            self.AirTemperature = self.get_time_dat('AirTemperature')

    def set_water_supply_source(self, wss):
        self.WaterSupplySource = wss

    def set_ground_water_temperature(self, wss):
        self.GroundWaterTemperature = wss

    def set_water_requirement_rate(self, wrr):
        self.WaterRequirementRate = wrr

    def set_source_time(self, st):
        self.SourceTime = datetime.datetime.strptime(st,'%H:%M:%S').time()
        if self.DrainTime is None:
            self.DrainTime = datetime.datetime.strptime(st,'%H:%M:%S').time() # default value

    def set_drain_time(self, st):
        self.DrainTime = datetime.datetime.strptime(st,'%H:%M:%S').time()

    def set_volume_of_source_water(self, vsw): # [L/s]
        self.VolumeOfSourceWater = vsw * 3600 / 1000 # [/hour /m3]
        if self.VolumeOfDrainWater is None:
            self.VolumeOfDrainWater = vsw * 3600 / 1000 # [/hour /m3]  # default value

    def set_volume_of_drain_water(self, vdw): # [L/s]
        self.VolumeOfDrainWater = vdw * 3600 / 1000 # [/hour /m3]

    def set_max_water_depth(self, depth):
        self.MaxWaterDepth = depth

    def set_area_of_field(self, area):
        self.AreaOfField = area

    def set_start_water_depth_rate(self, depth_rate):
        self.startWaterDepthRate = depth_rate

    def set_osmosis(self, osmosis):
        self.Osmosis = osmosis

    ###
    def isSourceTime(self):
        return self.TimeBaseDT[self.idx_time].time() == self.SourceTime

    def isDrainTime(self):
        return self.TimeBaseDT[self.idx_time].time() == self.DrainTime

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

    ###
    def check_starting_source_water(self):
        _p_water_depth = self.get_time_dat('WaterDepth', True)
        _water_depth_of_irrigation = self.get_time_dat('WaterDepthOfIrrigation')
        _p_start_source_water = self.get_time_dat('StartSourceWater', True)
        if _p_start_source_water == 0 and self.isSourceTime() and _p_water_depth < _water_depth_of_irrigation * self.startWaterDepthRate:
            _start_source_water = 1
        else:
            _start_source_water = _p_start_source_water
        self.Items['StartSourceWater'] = _start_source_water

    def calc_source_water(self):
        if self.Items['StartSourceWater'] == 1:
            _p_water_depth = self.get_time_dat('WaterDepth', True)
            _water_depth_of_irrigation = self.get_time_dat('WaterDepthOfIrrigation')
            _type_of_irrigation = self.get_time_dat('TypeOfIrrigation')

            if (_type_of_irrigation == 'flow' or _water_depth_of_irrigation > 0) and _p_water_depth < _water_depth_of_irrigation :
                _source_water = self.VolumeOfSourceWater / self.AreaOfField * 1000
            else:
                _source_water = 0
                self.Items['StartSourceWater'] = 0
        else:
            _source_water = 0
        self.Items['SourceWater'] = _source_water

    def check_starting_drain_water(self):
        _p_start_drain_water = self.get_time_dat('StartDrainWater', True)
        _p_water_depth = self.get_time_dat('WaterDepth', True)
        _water_depth_of_irrigation = self.get_time_dat('WaterDepthOfIrrigation')
        if _p_start_drain_water == 0 and self.isDrainTime() and _water_depth_of_irrigation < 0:
            _start_drain_water = 1
            self.targetWaterDepth = 0
        elif _p_start_drain_water == 0 and _p_water_depth > self.get_time_dat('MaxWaterDepth'):
            self.targetWaterDepth = self.get_time_dat('MaxWaterDepth')
            _start_drain_water = 1
        else:
            _start_drain_water = _p_start_drain_water
        self.Items['StartDrainWater'] = _start_drain_water

    def calc_drain_water(self):
        _type_of_irrigation = self.get_time_dat('TypeOfIrrigation')
        if _type_of_irrigation == 'flow' or self.Items['StartDrainWater'] == 1:
            _p_water_depth = self.get_time_dat('WaterDepth', True)
            if _p_water_depth > self.targetWaterDepth:
                _drain_water = self.VolumeOfDrainWater / self.AreaOfField * 1000
            else:
                _drain_water = 0
                self.Items['StartDrainWater'] = 0
        else:
            _drain_water = 0
        self.Items['DrainWater'] = _drain_water

    def calc_evaporation_from_water(self):
        _humidity = self.get_time_dat('Humidity')
        _air_temperature = self.AirTemperature
        _wind = self.get_time_dat('Wind')
        self.Items['EvaporationFromWaterSurface'] = max(0, 0.171474583 + 0.00482931034482759 * _air_temperature - 0.003784505 * _humidity + 0.015200426 * _wind)

    def calc_evaporation_from_leaf_surface(self): # need to improve
        _coeff = self.get_coeff('CoeffEvaporationFromLeafSurface')
        _vegetation_coverage = self.get_time_dat('PCR', True)
        _solar_radiation = self.get_time_dat('SolarRadiation')

        self.Items['EvaporationFromLeafSurface'] = _coeff * _vegetation_coverage * _solar_radiation

    def calc_osmosis(self):
        _evaporation_from_water = self.Items['EvaporationFromWaterSurface']
        if self.Osmosis is None:
            _osmosis = self.WaterRequirementRate / 24 - _evaporation_from_water
        else:
            _osmosis = self.Osmosis / 24
        self.Items['Osmosis'] = _osmosis

    def calc_water_depth(self):
        _rainfall = self.get_time_dat('Rainfall')
        _p_water_depth = self.get_time_dat('WaterDepth', True)
        _inc_water = self.Items['SourceWater'] + _rainfall
        _water_depth = _p_water_depth + _inc_water
        if _water_depth > -10 :
            _dec_water = self.Items['DrainWater'] + self.Items['EvaporationFromWaterSurface'] + self.Items['Osmosis'] + self.Items['EvaporationFromLeafSurface']
        else:
            _dec_water = self.Items['EvaporationFromWaterSurface']

        _water_depth = _water_depth - _dec_water
        self.Items['WaterDepth'] = _water_depth

    def calc_water_temperature(self):
        _p_water_temper = self.get_time_dat('eTMPW', True)
        _p_water_depth = self.get_time_dat('WaterDepth', True)
        if _p_water_depth > 0:
            #_p_water_hc = (_p_water_temper + 273) * _p_water_depth * self.HeatSpecificOfWater
            _p_water_hc = _p_water_temper * _p_water_depth * self.HeatSpecificOfWater * 1000
        else:
            _p_water_hc = 0

        #_source_water_hc = (self.GroundWaterTemperature + 273) * self.Items['SourceWater'] * self.HeatSpecificOfWater
        if self.WaterSupplySource == 'river':
            _water_temperature = self.Items['NighttimeTemperature'] + self.RiverWaterTemperatureDiff
        else:
            _water_temperature = self.GroundWaterTemperature
        _source_water_hc = _water_temperature * self.Items['SourceWater'] * self.HeatSpecificOfWater * 1000

        _rainfall = self.get_time_dat('Rainfall')
        _air_temperature = self.AirTemperature
        #_rainfall_hc = (_air_temperature + 273) * _rainfall * self.HeatSpecificOfWater
        _rainfall_hc = _air_temperature * _rainfall * self.HeatSpecificOfWater * 1000

        _solar_radiation = self.get_time_dat('SolarRadiation') * 1000000
        _vegetation_coverage = self.get_time_dat('PCR', True)

        _vc_eff = -1.0 / 54 * (1-math.exp(4 * _vegetation_coverage))
        _all_hc = _solar_radiation * (1.0 - _vc_eff) + _p_water_hc + _source_water_hc + _rainfall_hc

        if self.Items['WaterDepth'] <= 0:
            _water_temperature = _air_temperature
        else:
            _temperature_depon_hc = _all_hc / (self.HeatSpecificOfWater * self.Items['WaterDepth'] * 1000)
            if _temperature_depon_hc > _air_temperature: # Newton's law of cooling
                _param = 0.5 # tentative value
                #_k = _param * -1.0 * _esra_eff * self.HeatTransferCoeffOfAir / (self.HeatSpecificOfWater * (self.Items['WaterDepth'] / 10))
                _k = _param * -1.0 * (1.0 - 0.5 *_vc_eff) * self.HeatTransferCoeffOfAir / (self.HeatSpecificOfWater * (self.Items['WaterDepth'] / 10))
                _water_temperature = (_temperature_depon_hc - _air_temperature) * math.exp(_k * 3600) + _air_temperature
            else:
                _water_temperature = _temperature_depon_hc

        self.Items['eTMPW'] = _water_temperature

        #print(f"ESRA_EFF: {self.Items['eTMPW']}, {_all_hc}, {_all_hc_t}, {_vegetation_coverage}, {_vc_eff}, {_esra_eff} : {_all_hc / (self.HeatSpecificOfWater * self.Items['WaterDepth'] * 1000)}, {_air_temperature}, {_solar_radiation*_esra_eff}, {_p_water_hc}, {_source_water_hc}, {_rainfall_hc}, {_water_temperature}, {self.Items['SourceWater']}")

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
