import math
import pandas as pd
import datetime

# _SumOfSucroseProductionTh = 1500.0 no use
_RedAbsorptionRateTh = 0.0
_EffectiveSunRayReceivingAreaRateTh = 0.65

from .gsm_base import GsmBase

class GsmGrowth(GsmBase):

    def __init__(self):
        #super().__init__()
        self._heading_date = None
        self._seedling_date = None
        self.Items = {'ElapsedDaysSincePanicleDifferentiation':0, 'ElapsedDaysSinceHeading':0}

    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):
        if self.idx_time == 1:
            self.carry_previous_db()
        elif self.idx_time == (self.TimeBaseDT.size - 1):
            # calc and update at 23:00:00
            self.est_seedling_date()
            self.calc_elapsed_days_since_panicle_differentiation()
            self.calc_elapsed_days_since_heading()

        self.update_timebase_db()
        self.count_up_time()


    ###

    def set_heading_date(self, hd):
        if hd is not None:
            self._heading_date = datetime.datetime.strptime(hd,'%Y-%m-%d').date()
    ###

    def is_seedling_date(self):
        if self._seedling_date is None:
            return False
        elif self._seedling_date == self.TimeBaseDT[24].date():
            return True
        else:
            return False

    def est_seedling_date(self):
        _p_sum_of_soil_temperature = self.get_time_dat('SumOfSoilTemperature')
        if _p_sum_of_soil_temperature / 24 > self.get_coeff('SumOfSoilTemperatureTh') and self._seedling_date is None:
            self._seedling_date = self.TimeBaseDT[self.idx_time].date()

    def est_panicle_differentiation_date(self):
        _is_panicle_differentiation_date = False

        _red_absorption_rate = self.get_time_dat('RedAbsorptionRate')
        _effective_sunray_receiving_area_rate = self.get_time_dat('EffectiveSunRayReceivingAreaRate')

        if _red_absorption_rate > _RedAbsorptionRateTh and _effective_sunray_receiving_area_rate > _EffectiveSunRayReceivingAreaRateTh:
            _is_panicle_differentiation_date = True
        return _is_panicle_differentiation_date

    def est_heading_date(self):
        if self._heading_date is not None:
            _date = self.TimeBaseDT[self.idx_time].date() > self._heading_date
        else:
            _date = self.get_time_dat('SumOfSucroseProductionSincePanicleDifferentiation') > self.get_coeff('SumOfSucroseProductionTh')
        return _date

    def calc_elapsed_days_since_panicle_differentiation(self):
        _p_elapsed_days_since_panicle_differentiation = self.get_time_dat('ElapsedDaysSincePanicleDifferentiation', True)
        if _p_elapsed_days_since_panicle_differentiation > 0:
            self.Items['ElapsedDaysSincePanicleDifferentiation'] = _p_elapsed_days_since_panicle_differentiation + 1
        elif self.est_panicle_differentiation_date():
            self.Items['ElapsedDaysSincePanicleDifferentiation'] = 1

    def calc_elapsed_days_since_heading(self):
        _p_elapsed_days_since_heading = self.get_time_dat('ElapsedDaysSinceHeading', True)

        if _p_elapsed_days_since_heading > 0:
            self.Items['ElapsedDaysSinceHeading'] = _p_elapsed_days_since_heading + 1
        elif self.est_heading_date():
            self.Items['ElapsedDaysSinceHeading'] = 1

def _main():
    df = pd.read_csv('./36.25913074_140.0676563.calc.csv', parse_dates=True, index_col='Date')
    df = df.fillna(0)

    dfcc = pd.read_csv('../global_param/coeff.csv', comment='#')
    dfcb = pd.read_csv('../global_param/coeff_breed.csv', comment='#')
    dfc = pd.concat([dfcc,dfcb], axis=1)

    print(df.shape, dfc.shape)

    gg = GsmGrowth()
    gg.set_heading_date('2019-08-01')
    n_row = df.index.size
    for i in range(1, n_row-1, 24):
        t_df = df[i:i+24]
        t_dfd = t_df.to_dict()
        c_df = df[i-1:i+24]
        c_dfd = c_df.to_dict()
        gg.set_coeff_db(dfc)
        gg.set_today_db(t_dfd)
        gg.set_timebase_db(c_dfd, c_df.index)

        gg.calculate()

        uc_df = pd.DataFrame(c_dfd)
        df.update(uc_df)

    df.to_csv('t.new.csv')

if __name__ == '__main__':
    _main()
