import math
import pandas as pd

from .gsm_base import GsmBase

class GsmRice(GsmBase):

    def __init__(self):

        self.Items = {'RiceScreeningsRate':1.0, 'WeightGrossBrownRice':0, 'WeightBrownRice':0,
                      'MilkyWhiteRiceRate':0, 'Protein':0, 'Amylose':0, 'Amylopectin':0, 'Moisture':0}

    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):
        if self.idx_time == 1:
            self.carry_previous_db()
        elif self.idx_time == (self.TimeBaseDT.size - 1):
            # calc and update at 23:00:00
            self.calc_weight_gross_brown_rice()
            self.calc_rice_screening_rate()
            self.calc_weight_brown_rice()
            self.calc_milky_white_rice_rate()
            self.calc_protein()
            self.calc_amylose()
            self.calc_amylopectin()
            self.calc_moisture()

        self.update_timebase_db()
        self.count_up_time()

    ###

    def calc_weight_gross_brown_rice(self):
        self.Items['WeightGrossBrownRice'] = self.get_time_dat('WeightEndosperm') / 0.75

    def calc_rice_screening_rate(self):
        _number_of_rough_rice = self.get_time_dat('NumberOfRoughRice')
        if _number_of_rough_rice > 0:
            _coeff = self.get_coeff('CoeffRiceScreeningsRate')
            _weight_gross_brown_rice = self.Items['WeightGrossBrownRice']
            _tg_weight = self.get_coeff('ThousandGrainWeight')
            self.Items['RiceScreeningsRate'] = 1 - min(1, _coeff * _weight_gross_brown_rice / _number_of_rough_rice / (_tg_weight / 1000))
        else:
            self.Items['RiceScreeningsRate'] = 1


    def calc_weight_brown_rice(self):
        _weight_gross_brown_rice = self.Items['WeightGrossBrownRice']
        if _weight_gross_brown_rice > 0:
            _rice_screenings_rate = self.Items['RiceScreeningsRate']
            self.Items['WeightBrownRice'] = (1 - _rice_screenings_rate) * _weight_gross_brown_rice
        else:
            self.Items['WeightBrownRice'] = 0

    def calc_milky_white_rice_rate(self):
        self.Items['MilkyWhiteRiceRate'] = self.get_coeff('CoeffMilkyWhiteRiceRate') # dummy code

    def calc_protein(self):
        _coeff = self.get_coeff('CoeffProtein') # no use
        _sum_of_nitrogen_distribution_amount_of_endosperm = self.get_time_dat('SumOfNitrogenDistributionAmountOfEndosperm')
        _number_of_rough_rice = self.get_time_dat('NumberOfRoughRice')
        _tg_weight = self.get_coeff('ThousandGrainWeight')
#        self.Items['Protein'] = _sum_of_nitrogen_distribution_amount_of_endosperm / 0.16 / (_number_of_rough_rice * (_tg_weight / 1000))
        if self.Items['WeightGrossBrownRice'] > 0:
            _protein = _sum_of_nitrogen_distribution_amount_of_endosperm / 0.16 / self.Items['WeightGrossBrownRice']
        else:
            _protein = 0

        self.Items['Protein'] = _protein

    def calc_amylose(self):
        self.Items['Amylose'] = self.get_coeff('CoeffAmylose') # dummy code

    def calc_amylopectin(self):
        self.Items['Amylopectin'] = 1 - self.Items['Amylose']

    def calc_moisture(self):
        self.Items['Moisture'] = 0 # dummy code


def _main():
    df = pd.read_csv('./36.25913074_140.0676563.calc.csv', parse_dates=True, index_col='Date')
    df = df.fillna(0)

    dfcc = pd.read_csv('../global_param/coeff.csv', comment='#')
    dfcb = pd.read_csv('../global_param/coeff_breed.csv', comment='#')
    dfc = pd.concat([dfcc,dfcb], axis=1)

    print(df.shape, dfc.shape)

    gr = GsmRice()
    n_row = df.index.size
    for i in range(1, n_row-1, 24):
        t_df = df[i:i+24]
        t_dfd = t_df.to_dict()
        c_df = df[i-1:i+24]
        c_dfd = c_df.to_dict()
        gr.set_coeff_db(dfc)
        gr.set_today_db(t_dfd)
        gr.set_timebase_db(c_dfd, c_df.index)

        gr.calculate()

        uc_df = pd.DataFrame(c_dfd)
        df.update(uc_df)

    df.to_csv('t.new.csv')


if __name__ == '__main__':
    _main()
