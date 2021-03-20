import math
import datetime
import json
import math
import pandas as pd

from .gsm_base import GsmBase

class GsmRespiration(GsmBase):

    def __init__(self):
        self.Items = {'RsmLeafBlade':0, 'RsmLeafSheath':0, 'RsmCulm':0, 'RsmRootage':0, 'RsmSpike':0,
                      'RsmRoughRice':0, 'RsmEndosperm':0,
                      'MaintenanceRespiration':0, 'DailyMaintenanceRespiration':0, 'SumOfMaintenanceRespiration':0}

    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):
        self.calc_rsm_leaf_blade()
        self.calc_rsm_leaf_sheath()
        self.calc_rsm_culm()
        self.calc_rsm_rootage()
        self.calc_rsm_spike()
        self.calc_rsm_rough_rice()
        self.calc_rsm_endosperm()
        self.calc_maintenance_respiration()
        self.calc_daily_maintenance_respiration()
        self.calc_sum_of_maintenance_respiration()

        self.update_timebase_db()
        self.count_up_time()


    def calc_rsm_leaf_blade(self):
        _p_weight_leaf_blade = self.get_time_dat('WeightLeafBlade', True)
        self.Items['RsmLeafBlade'] = self.get_coeff('CoeffRsmLeafBlade') / 24 * _p_weight_leaf_blade

    def calc_rsm_leaf_sheath(self):
        _p_weight_leaf_sheath = self.get_time_dat('WeightLeafSheath', True)
        self.Items['RsmLeafSheath'] = self.get_coeff('CoeffRsmLeafSheath') / 24 * _p_weight_leaf_sheath

    def calc_rsm_culm(self):
        _p_weight_culm = self.get_time_dat('WeightCulm', True)
        self.Items['RsmCulm'] = self.get_coeff('CoeffRsmCulm') / 24 * _p_weight_culm

    def calc_rsm_rootage(self):
        _p_weight_rootage = self.get_time_dat('WeightRootage', True)
        self.Items['RsmRootage'] = self.get_coeff('CoeffRsmRootage') / 24 * _p_weight_rootage

    def calc_rsm_spike(self):
        _p_weight_spike = self.get_time_dat('WeightSpike', True)
        self.Items['RsmSpike'] = self.get_coeff('CoeffRsmSpike') / 24 * _p_weight_spike

    def calc_rsm_rough_rice(self):
        _p_weight_rough_rice = self.get_time_dat('WeightRoughRice', True)
        self.Items['RsmRoughRice'] = self.get_coeff('CoeffRsmRoughRice') / 24 * _p_weight_rough_rice

    def calc_rsm_endosperm(self):
        _p_weight_endosperm = self.get_time_dat('WeightEndosperm', True)
        self.Items['RsmEndosperm'] = self.get_coeff('CoeffRsmEndosperm') / 24 * _p_weight_endosperm

    ###

    def calc_maintenance_respiration(self):
        _sum_rsm = self.Items['RsmLeafBlade'] + self.Items['RsmLeafSheath'] + self.Items['RsmCulm'] + self.Items['RsmRootage'] + self.Items['RsmSpike'] + self.Items['RsmRoughRice'] + self.Items['RsmEndosperm']
        _water_temperature = self.get_time_dat('SensorWaterTemperature')
        if _water_temperature == None:
            _water_temperature = self.get_time_dat('eTMPW') - 273.15

        _ed_since_pd = self.get_time_dat('ElapsedDaysSincePanicleDifferentiation', True)
        if _ed_since_pd > 0:
            #ef_q10 = 0.001437 * _water_temperature * _water_temperature + 0.0248 * _water_temperature - 0.518
            ef_q10 = 0.002400 * _water_temperature * _water_temperature - 0.0278 * _water_temperature + 0.1978
        else:
            ef_q10 = 0.000100 * _water_temperature * _water_temperature + 0.0078 * _water_temperature + 0.1961

        self.Items['MaintenanceRespiration'] = _sum_rsm * ef_q10
        #print("MR:", self.Items['MaintenanceRespiration'], _sum_rsm, self.get_time_dat('eTMPW'), q10)

    def calc_daily_maintenance_respiration(self):
        if self.check_sunrise():
            self.Items['DailyMaintenanceRespiration'] = 0
        else:
            self.Items['DailyMaintenanceRespiration'] = self.get_time_dat('DailyMaintenanceRespiration', True) + self.Items['MaintenanceRespiration']

    def calc_sum_of_maintenance_respiration(self):
        self.Items['SumOfMaintenanceRespiration'] = self.get_time_dat('SumOfMaintenanceRespiration', True) + self.Items['MaintenanceRespiration']
    ###

def _main():
    df = pd.read_csv('./36.25913074_140.0676563.calc.csv', parse_dates=True, index_col='Date')
    df = df.fillna(0)

    dfcc = pd.read_csv('../global_param/coeff.csv', comment='#')
    dfcb = pd.read_csv('../global_param/coeff_breed.csv', comment='#')
    dfc = pd.concat([dfcc,dfcb], axis=1)

    print(df.shape, dfc.shape)

    gr = GsmRespiration()
    n_row = df.index.size
    for i in range(1, n_row-1, 24):
        t_df = df[i:i+24]
        t_dfd = t_df.to_dict()
        c_df = df[i-1:i+24]
        c_dfd = c_df.to_dict()
        gr.set_coeff_db(dfc)
        gr.set_today_db(t_dfd)
        gr.set_timebase_db(c_dfd, c_df.index)

        grp.calculate()

        uc_df = pd.DataFrame(c_dfd)
        df.update(uc_df)

    df.to_csv('t.new.csv')

if __name__ == '__main__':
    _main()
