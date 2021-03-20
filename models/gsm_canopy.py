import math
import datetime
import json
import pandas as pd

from .gsm_base import GsmBase

class GsmCanopy(GsmBase):

    def __init__(self):
        self.Items = {
                      'EffectiveSunRayReceivingAreaRate':0,'PCR':0, 'LeafAreaIndex':0 }

    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):
        self.calc_leaf_area_index()
        self.calc_effective_sunray_receiving_area_rate()
        self.calc_vegetation_coverage()

        self.update_timebase_db()
        self.count_up_time()

    ###
    def calc_leaf_area_index(self):
        _surface_area = self.get_time_dat('SurfaceAreaOfLeafBlade', True)
        self.Items['LeafAreaIndex'] = min(1, 2.0 / (1 + math.exp(-0.8 * _surface_area)) - 1.0)

    def calc_effective_sunray_receiving_area_rate(self):
        _p_weight_endosperm = self.get_time_dat('WeightEndosperm', True)
        self.Items['EffectiveSunRayReceivingAreaRate'] = self.Items['LeafAreaIndex'] - 0.1 * _p_weight_endosperm / 600.0

    def calc_vegetation_coverage(self):
        _p_weight_endosperm = self.get_time_dat('WeightEndosperm', True)
        self.Items['PCR'] = min(1, self.Items['LeafAreaIndex'] + 0.05 * _p_weight_endosperm / 600.0)

def _main():

    df = pd.read_csv('./36.25913074_140.0676563.calc.csv', parse_dates=True, index_col='Date')
    df = df.fillna(0)

    dfcc = pd.read_csv('../global_param/coeff.csv', comment='#')
    dfcb = pd.read_csv('../global_param/coeff_breed.csv', comment='#')
    dfc = pd.concat([dfcc,dfcb], axis=1)

    print(df.shape, dfc.shape)

    n_row = df.index.size
    gc = GsmCarbon()
    for i in range(1, n_row-1, 24):
        c_df = df[i-1:i+24]
        c_dfd = c_df.to_dict()
        gc.set_coeff_db(dfc)
        gc.set_timebase_db(c_dfd, c_df.index)

        gc.calculate()

        uc_df = pd.DataFrame(c_dfd)
        df.update(uc_df)

    df.to_csv('t.new.csv')

if __name__ == '__main__':
    _main()
