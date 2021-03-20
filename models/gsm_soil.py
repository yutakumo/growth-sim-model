import math
import json
import datetime
import pandas as pd

from .gsm_base import GsmBase

class GsmSoil(GsmBase):

    def __init__(self):
        self.WaterSupplyOxygenContent = 5
        self.Items = {'SumOfSoilTemperature':0,
                      'SoilOxygenConcentration':0}

    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):
        self.calc_sum_of_soil_temperature()
        self.calc_soil_oxygen_concentration()

        self.update_timebase_db()
        self.count_up_time()

    ###
    def calc_sum_of_soil_temperature(self):
        _soil_temperature = self.get_time_dat('SensorSoilTemperature')
        if _soil_temperature == None:
            _soil_temperature = self.get_time_dat('eTMPS') - 273.15
        self.Items['SumOfSoilTemperature'] = self.get_time_dat('SumOfSoilTemperature', True) + _soil_temperature

    def calc_soil_oxygen_concentration(self): # hour-sim
        _water_depth = self.get_time_dat('eWDPcm') * 10.0
        if _water_depth > 5 :
            _vf_surface_drainage = self.get_coeff('CoeffDecVariableForSurfaceDrainage') / 24
        elif _water_depth > -5 :
            _vf_surface_drainage = self.get_coeff('CoeffIncVariableForSurfaceDrainage') / 24 * (5 - _water_depth) / 10
        else :
            _vf_surface_drainage = self.get_coeff('CoeffIncVariableForSurfaceDrainage') / 24

        _p_soil_oxygen_concentration = self.get_time_dat('SoilOxygenConcentration', True)

        _volume_of_source_water = self.get_time_dat('WFLXinlet')
        if math.isnan(_volume_of_source_water):
            _volume_of_source_water = self.get_time_dat('eWFLXinlet')

        _water_oxygen = self.WaterSupplyOxygenContent / 1000 * max(0, _volume_of_source_water) * 0.25 # tentative logic , so need to modify

        _max_oxygen = 1.14 * 0.21 * 1000 * 15 / 100

        #print('Oxygen:',  _p_soil_oxygen_concentration, _vf_surface_drainage, _water_oxygen)
        self.Items['SoilOxygenConcentration'] = min(_max_oxygen, max(0, _p_soil_oxygen_concentration + _vf_surface_drainage + _water_oxygen)) #- self.Items['Denitrification'] * 1.86)


def _main():

    df = pd.read_csv('./36.25913074_140.0676563.calc.csv', parse_dates=True, index_col='Date')
    df = df.fillna(0)

    dfcc = pd.read_csv('../global_param/coeff.csv', comment='#')
    dfcb = pd.read_csv('../global_param/coeff_breed.csv', comment='#')
    dfc = pd.concat([dfcc,dfcb], axis=1)

    print(df.shape, dfc.shape)
    gso = GsmSoil()

    n_row = df.index.size

    for i in range(1, n_row-1, 24):
        c_df = df[i-1:i+24]
        c_dfd = c_df.to_dict()
        gso.set_coeff_db(dfc)
        gso.set_timebase_db(c_dfd, c_df.index)

        gso.calculate()

        uc_df = pd.DataFrame(c_dfd)
        df.update(uc_df)

    df.to_csv('t.new.csv')

if __name__ == '__main__':
    _main()
