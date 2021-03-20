import math
import json
import datetime
import pandas as pd

from .gsm_base import GsmBase

class GsmNitrogen(GsmBase):

    def __init__(self):
        self.Items = {'RnLeafBlade':0,'RnLeafSheath':0, 'RnCulm':0, 'RnRootage':0, 'RnSpike':0, 'RnRoughRice':0, 'RnEndosperm':0,
                      'RnTransformGrowthStage':0,
                      'RnSum':0,
                      'DnLeafBlade':0, 'DnLeafSheath':0, 'DnCulm':0, 'DnRootage':0, 'DnSpike':0, 'DnRoughRice':0, 'DnEndosperm':0,
                      'DnTransformGrowthStage':0,
                      'QnLeafBlade':0, 'QnLeafSheath':0, 'QnCulm':0, 'QnRootage':0, 'QnSpike':0, 'QnRoughRice':0, 'QnEndosperm':0,
                      'QnTransformGrowthStage':0,
                      'SumOfNitrogenDistributionAmountOfLeafBlade':0,
                      'SumOfNitrogenDistributionAmountOfEndosperm':0, 'SumOfNitrogenDistributionAmountOfRoughRice':0}

    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):

        if self.idx_time == 1:
            self.carry_previous_db()
        elif self.idx_time == (self.TimeBaseDT.size - 1):
            # calc and update at 23:00:00
            self.calc_rn_leaf_blade()
            self.calc_rn_leaf_sheath()
            self.calc_rn_culm()
            self.calc_rn_rootage()
            self.calc_rn_spike()
            self.calc_rn_rough_rice()
            self.calc_rn_endosperm()
            self.calc_rn_transform_growth_stage()
            self.calc_rn_sum()
            self.calc_dn_leaf_blade()
            self.calc_dn_leaf_sheath()
            self.calc_dn_culm()
            self.calc_dn_rootage()
            self.calc_dn_spike()
            self.calc_dn_rough_rice()
            self.calc_dn_endosperm()
            self.calc_dn_transform_growth_stage()
            self.calc_qn_leaf_blade()
            self.calc_qn_leaf_sheath()
            self.calc_qn_culm()
            self.calc_qn_rootage()
            self.calc_qn_spike()
            self.calc_qn_rough_rice()
            self.calc_qn_endosperm()
            self.calc_qn_transform_growth_stage()
            self.calc_sum_of_nitrogen_distribution_amount_of_leaf_blade()
            self.calc_sum_of_nitrogen_distribution_amount_of_rough_rice()
            self.calc_sum_of_nitrogen_distribution_amount_of_endsperm()

        self.update_timebase_db()
        self.count_up_time()

    ###

    def calc_rn_leaf_blade(self):
        #_red_absorption_rate = self.get_time_dat('RedAbsorptionRate')
        #_red_eff = 1.0 - (1 - math.exp(-4.5 * _red_absorption_rate))
        _max_red_absorption_rate = self.get_time_dat('MaxRedAbsorptionRate')
        _rar = _max_red_absorption_rate
        _rar2 = _rar * _max_red_absorption_rate
        _rar3 = _rar2 * _max_red_absorption_rate
        _rar4 = _rar3 * _max_red_absorption_rate
        _rar5 = _rar4 * _max_red_absorption_rate
        _rar6 = _rar5 * _max_red_absorption_rate
        _red_eff = -2.9412 * _rar6 + 9.7851 * _rar5 - 11.333 * _rar4 + 4.937 * _rar3 + 0.7471 * _rar2 - 2.1854 * _rar + 1.0009

        _p_elapsed_days_since_heading = self.get_time_dat('ElapsedDaysSinceHeading', True)
        if _p_elapsed_days_since_heading > 1:
            _eff = max(0 , 1.0 - 1.015 * (1 - math.exp(-4.0 * (_p_elapsed_days_since_heading - 1)/ 45.0)))
        else:
            _eff = 1.0

        _p_weight_endosperm = self.get_time_dat('WeightEndosperm', True)
        _p_rs_endosperm = self.get_time_dat('RsEndosperm', True)
        _sucrose_param = min(1, max(0, _p_rs_endosperm/_p_weight_endosperm - 0.2 if _p_weight_endosperm > 0 else 1))
        _surface_area_of_leaf_blade = self.get_time_dat('SurfaceAreaOfLeafBlade')
        #_dsm_leaf_blade = self.get_time_dat('DsmLeafBlade')
        _dsm_leaf_blade = 1.0

        self.Items['RnLeafBlade'] = _red_eff * _surface_area_of_leaf_blade * _dsm_leaf_blade * _eff * _sucrose_param

    def calc_rn_leaf_sheath(self):
        _p_weight_leaf_blade = self.get_time_dat('WeightLeafBlade', True)
        if _p_weight_leaf_blade > 0:
            _coeff = self.get_coeff('CoeffRnLeafSheath')
            _rn_leaf_blade = self.Items['RnLeafBlade']
            _p_weight_leaf_sheath = self.get_time_dat('WeightLeafSheath', True)
            self.Items['RnLeafSheath'] = _coeff * _rn_leaf_blade * _p_weight_leaf_sheath / _p_weight_leaf_blade
        else:
            self.Items['RnLeafSheath'] = 0

    def calc_rn_culm(self):
        _p_weight_leaf_blade = self.get_time_dat('WeightLeafBlade', True)
        if _p_weight_leaf_blade > 0:
            _coeff = self.get_coeff('CoeffRnCulm')
            _rn_leaf_blade = self.Items['RnLeafBlade']
            _p_weight_culm = self.get_time_dat('WeightCulm', True)
            self.Items['RnCulm'] = _coeff * _rn_leaf_blade * _p_weight_culm / _p_weight_leaf_blade
        else:
            self.Items['RnCulm'] = 0

    def calc_rn_rootage(self):
        self.Items['RnRootage'] = 0

    def calc_rn_spike(self):

        _elapsed_days_since_heading = self.get_time_dat('ElapsedDaysSinceHeading', True)
        _elapsed_days_since_panicle_differentiation = self.get_time_dat('ElapsedDaysSincePanicleDifferentiation', True)
        if _elapsed_days_since_heading > 0:
            _coeff = self.get_coeff('CoeffRnSpike')
            _p_number_of_rough_rice = self.get_time_dat('NumberOfRoughRice', True)
            _rn_spike = _coeff * max(0, 20 - _elapsed_days_since_heading) * _p_number_of_rough_rice
        elif _elapsed_days_since_panicle_differentiation > 0:
            _coeff = self.get_coeff('CoeffRnPanicle')
            _rn_spike = _coeff * self.get_time_dat('PCR', True)
        else:
            _rn_spike = 0.0

        _p_rn_spike = self.get_time_dat('RnSpike', True)
        #_rn_spike = 0.5 * _p_rn_spike if _rn_spike == 0 and _elapsed_days_since_heading < 21 else _rn_spike

        _p_rn_sum = self.get_time_dat('RnSum', True)
        if ( _p_rn_spike > 0 ) :
            _max_rn_spike = 1.5 * _p_rn_spike
        else:
            _max_rn_spike = min(0.5 * _rn_spike, 0.1 * _p_rn_sum)

        self.Items['RnSpike'] = min(_max_rn_spike, _rn_spike)

    def calc_rn_rough_rice(self):
        self.Items['RnRoughRice'] = 0

    def calc_rn_endosperm(self):
        _elapsed_days_since_heading = self.get_time_dat('ElapsedDaysSinceHeading', True)
        _p_number_of_rough_rice = self.get_time_dat('NumberOfRoughRice', True)
        _p_sum_of_nitogen_distribution_amount_of_endosperm = self.get_time_dat('SumOfNitrogenDistributionAmountOfEndosperm', True)
        _coeff = self.get_coeff('CoeffRnEndosperm')
        _p_weight_endosperm = self.get_time_dat('WeightEndosperm', True)
        if _elapsed_days_since_heading > 0:
            _req_nit = 0.16 * _p_weight_endosperm / 0.75
            _rn_endosperm = max(0, 0.07 * _req_nit - _p_sum_of_nitogen_distribution_amount_of_endosperm) * _coeff
            _rn_endosperm += max(0, 0.08 * _req_nit - _p_sum_of_nitogen_distribution_amount_of_endosperm) * _coeff * 0.1
            _rn_endosperm += max(0, 0.09 * _req_nit - _p_sum_of_nitogen_distribution_amount_of_endosperm) * _coeff * 0.01
        else:
            _rn_endosperm = 0

        #print("CHECK:", 0.07 * 0.16 * _p_weight_endosperm / 0.75, _p_sum_of_nitogen_distribution_amount_of_endosperm, _rn_endosperm)

        _p_rn_endosperm = self.get_time_dat('RnEndosperm', True)
        #_rn_endosperm = 0.5 * _p_rn_endosperm if (_rn_endosperm == 0 and _p_sum_of_nitogen_distribution_amount_of_endosperm == 0) else _rn_endosperm
        _p_rn_sum = self.get_time_dat('RnSum', True)
        if ( _p_rn_endosperm > 0 ) :
            _max_rn_endosperm = 1.5 * _p_rn_endosperm
        else:
            _max_rn_endosperm = min(0.5 * _rn_endosperm, 0.1 * _p_rn_sum)

        self.Items['RnEndosperm'] = min(_max_rn_endosperm, _rn_endosperm)

    def calc_rn_transform_growth_stage(self):
        _elapsed_days_since_panicle_differentiation = self.get_time_dat('ElapsedDaysSincePanicleDifferentiation', True)
        _elapsed_days_since_heading = self.get_time_dat('ElapsedDaysSinceHeading', True)
        if _elapsed_days_since_panicle_differentiation > 15 and _elapsed_days_since_heading < 15:
            _p_total_weight = self.get_time_dat('WeightTotal', True)
            _coeff = self.get_coeff('CoeffRnTransformGrowthStage')
            self.Items['RnTransformGrowthStage'] = _coeff * _p_total_weight * max(0, _elapsed_days_since_panicle_differentiation - 4 * _elapsed_days_since_heading)
        else:
            self.Items['RnTransformGrowthStage'] = 0

    def calc_rn_sum(self):
        self.Items['RnSum'] = self.Items['RnLeafBlade'] + self.Items['RnLeafSheath'] + self.Items['RnCulm'] + self.Items['RnRootage'] + self.Items['RnSpike'] + self.Items['RnRoughRice'] + self.Items['RnEndosperm'] + self.Items['RnTransformGrowthStage']

    ###

    def calc_dn_leaf_blade(self):
        if self.Items['RnSum'] > 0:
            self.Items['DnLeafBlade'] = self.Items['RnLeafBlade'] / self.Items['RnSum']
        else:
            self.Items['DnLeafBlade'] = 0

    def calc_dn_leaf_sheath(self):
        if self.Items['RnSum'] > 0:
            self.Items['DnLeafSheath'] = self.Items['RnLeafSheath'] / self.Items['RnSum']
        else:
            self.Items['DnLeafSheath'] = 0

    def calc_dn_culm(self):
        if self.Items['RnSum'] > 0:
            self.Items['DnCulm'] = self.Items['RnCulm'] / self.Items['RnSum']
        else:
            self.Items['DnCulm'] = 0

    def calc_dn_rootage(self):
        if self.Items['RnSum'] > 0:
            self.Items['DnRootage'] = self.Items['RnRootage'] / self.Items['RnSum']
        else:
            self.Items['DnRootage'] = 0

    def calc_dn_spike(self):
        if self.Items['RnSum'] > 0:
            self.Items['DnSpike'] = self.Items['RnSpike'] / self.Items['RnSum']
        else:
            self.Items['DnSpike'] = 0

    def calc_dn_rough_rice(self):
        if self.Items['RnSum'] > 0:
            self.Items['DnRoughRice'] = self.Items['RnRoughRice'] / self.Items['RnSum']
        else:
            self.Items['DnRoughRice'] = 0

    def calc_dn_endosperm(self):
        if self.Items['RnSum'] > 0:
            self.Items['DnEndosperm'] = self.Items['RnEndosperm'] / self.Items['RnSum']
        else:
            self.Items['DnEndosperm'] = 0

    def calc_dn_transform_growth_stage(self):
        if self.Items['RnSum'] > 0:
            self.Items['DnTransformGrowthStage'] = self.Items['RnTransformGrowthStage'] / self.Items['RnSum']
        else:
            self.Items['DnTransformGrowthStage'] = 0

    def calc_qn_leaf_blade(self):
        self.Items['QnLeafBlade'] = self.Items['DnLeafBlade'] * self.get_day_dat('NitrogenAssimilation')
        #print("R-Sum", self.Items['RnSum'], "N-Assim", self.get_day_dat('NitrogenAssimilation'),"DIFF", self.get_day_dat('NitrogenAssimilation')-self.Items['RnSum'])

    def calc_qn_leaf_sheath(self):
        self.Items['QnLeafSheath'] = self.Items['DnLeafSheath'] * self.get_day_dat('NitrogenAssimilation')

    def calc_qn_culm(self):
        self.Items['QnCulm'] = self.Items['DnCulm'] * self.get_day_dat('NitrogenAssimilation')

    def calc_qn_rootage(self):
        self.Items['QnRootage'] = self.Items['DnRootage'] * self.get_day_dat('NitrogenAssimilation')

    def calc_qn_spike(self):
        self.Items['QnSpike'] = self.Items['DnSpike'] * self.get_day_dat('NitrogenAssimilation')

    def calc_qn_rough_rice(self):
        self.Items['QnRoughRice'] = self.Items['DnRoughRice'] * self.get_day_dat('NitrogenAssimilation')

    def calc_qn_endosperm(self):
        self.Items['QnEndosperm'] = self.Items['DnEndosperm'] * self.get_day_dat('NitrogenAssimilation')

    def calc_qn_transform_growth_stage(self):
        self.Items['QnTransformGrowthStage'] = self.Items['DnTransformGrowthStage'] * self.get_day_dat('NitrogenAssimilation')
    ###

    def calc_sum_of_nitrogen_distribution_amount_of_leaf_blade(self):
        _p_effective_sunray_receiving_area_rate = self.get_time_dat('EffectiveSunRayReceivingAreaRate', True)
        if _p_effective_sunray_receiving_area_rate > 0.90:
            _carry_rate = 0.975
        else:
            _carry_rate = 1.0

        _nitrogen_translocation_choropalst_breakup = self.get_day_dat('NitrogenTranslocationChoropalstBreakup')
        self.Items['SumOfNitrogenDistributionAmountOfLeafBlade'] = self.get_time_dat('SumOfNitrogenDistributionAmountOfLeafBlade', True) - 1.10 * _nitrogen_translocation_choropalst_breakup
        _nitrogen_assimilation = self.get_day_dat('NitrogenAssimilation')
        self.Items['SumOfNitrogenDistributionAmountOfLeafBlade'] += (_nitrogen_assimilation + _nitrogen_translocation_choropalst_breakup) * self.Items['DnLeafBlade']

    def calc_sum_of_nitrogen_distribution_amount_of_rough_rice(self):
        self.Items['SumOfNitrogenDistributionAmountOfRoughRice'] = self.get_time_dat('SumOfNitrogenDistributionAmountOfRoughRice', True)
        _nitrogen_assimilation = self.get_day_dat('NitrogenAssimilation')
        _nitrogen_translocation_choropalst_breakup = self.get_day_dat('NitrogenTranslocationChoropalstBreakup')
        self.Items['SumOfNitrogenDistributionAmountOfRoughRice'] += (_nitrogen_assimilation + _nitrogen_translocation_choropalst_breakup) * self.Items['DnRoughRice']

    def calc_sum_of_nitrogen_distribution_amount_of_endsperm(self):
        self.Items['SumOfNitrogenDistributionAmountOfEndosperm'] = self.get_time_dat('SumOfNitrogenDistributionAmountOfEndosperm', True)
        _nitrogen_assimilation = self.get_day_dat('NitrogenAssimilation')
        _nitrogen_translocation_choropalst_breakup = self.get_day_dat('NitrogenTranslocationChoropalstBreakup')
        self.Items['SumOfNitrogenDistributionAmountOfEndosperm'] += (_nitrogen_assimilation + _nitrogen_translocation_choropalst_breakup) * self.Items['DnEndosperm']

def _main():
    df = pd.read_csv('./36.25913074_140.0676563.calc.csv', parse_dates=True, index_col='Date')
    df = df.fillna(0)

    dfcc = pd.read_csv('../global_param/coeff.csv', comment='#')
    dfcb = pd.read_csv('../global_param/coeff_breed.csv', comment='#')
    dfc = pd.concat([dfcc,dfcb], axis=1)

    print(df.shape, dfc.shape)

    gn = GsmNitrogen()
    n_row = df.index.size
    for i in range(1, n_row-1, 24):
        t_df = df[i:i+24]
        t_dfd = t_df.to_dict()
        c_df = df[i-1:i+24]
        c_dfd = c_df.to_dict()
        gn.set_coeff_db(dfc)
        gn.set_today_db(t_dfd)
        gn.set_timebase_db(c_dfd, c_df.index)

        gn.calculate()

        uc_df = pd.DataFrame(c_dfd)
        df.update(uc_df)

    df.to_csv('t.new.csv')

if __name__ == '__main__':
    _main()
