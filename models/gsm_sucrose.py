import math
import datetime
import json
import math
import pandas as pd

from .gsm_base import GsmBase

class GsmSucrose(GsmBase):

    def __init__(self):
        self.Items = {'RsLeafBlade':0, 'RsLeafSheath':0, 'RsCulm':0,'RsRootage':0, 'RsSpike':0,
                      'RsRoughRice':0, 'RsEndosperm':0,
                      'RsSum':0,
                      'DsLeafBlade':0, 'DsLeafSheath':0, 'DsCulm':0, 'DsRootage':0, 'DsSpike':0,
                      'DsRoughRice':0, 'DsEndosperm':0,
                      'QsLeafBlade':0, 'QsLeafSheath':0, 'QsCulm':0, 'QsRootage':0, 'QsSpike':0,
                      'QsRoughRice':0, 'QsEndosperm':0,
                      'SucroseSurpluse':0,
                      'WeightLeafBlade':0,'WeightLeafSheath':0, 'WeightCulm':0, 'WeightRootage':0,
                      'WeightSpike':0,'WeightRoughRice':0, 'WeightEndosperm':0, 'WeightTotal':0,
                      'NitrogenConcentration':0,
                      'SurfaceAreaOfLeafBlade':0,'SurfaceAreaOfRootage':0,
                      'NumberOfSpikelet':0, 'NumberOfRoughRice':0, 'VolumeOfRoughRice':0}

    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):
        n_row = self.TimeBaseDT.size

        if self.idx_time == 1:
            self.carry_previous_db()
        elif self.check_sunrise():
            self.calc_rs_leaf_blade()
            self.calc_rs_leaf_sheath()
            self.calc_rs_culm()
            self.calc_rs_rootage()
            self.calc_rs_spike()
            self.calc_rs_rough_rice()
            self.calc_rs_endosperm()
            self.calc_rs_sum()
            self.calc_ds_leaf_blade()
            self.calc_ds_leaf_sheath()
            self.calc_ds_culm()
            self.calc_ds_rootage()
            self.calc_ds_spike()
            self.calc_ds_rough_rice()
            self.calc_ds_endosperm()
            self.calc_w_leaf_blade()
            self.calc_w_leaf_sheath()
            self.calc_w_culm()
            self.calc_w_rootage()
            self.calc_w_spike()
            self.calc_w_roughRice()
            self.calc_w_endosperm()
            self.calc_w_total()
            self.calc_nitrogen_concentration()
            self.calc_surface_area_of_leaf_blade()
            self.calc_surface_area_of_rootage()
            self.calc_number_of_rough_rice()
            self.calc_volume_of_rough_rice()

        self.update_timebase_db()
        self.count_up_time()

    ###
    def set_planting_density(self, pd):
        self._planting_density = pd

    ###
    def calc_init_surface_area_of_leaf_blade(self):
        self.idx_time = 0
        self.Items['WeightLeafBlade'] = self.get_time_dat('WeightLeafBlade')
        self.Items['SurfaceAreaOfLeafBlade'] = self.get_coeff('CoeffSurfaceAreaOfLeafBlade') * pow(self.Items['WeightLeafBlade'],2/3)

    def calc_init_surface_area_of_rootage(self):
        self.idx_time = 0
        self.Items['WeightRootage'] = self.get_time_dat('WeightRootage')
        self.Items['SurfaceAreaOfRootage'] = self.get_coeff('CoeffSurfaceAreaOfRootage') * pow(self.Items['WeightRootage'],2/3)
    ###

    def calc_rs_leaf_blade(self):
        _p_total_weight = self.get_time_dat('WeightTotal', True)
        _coeff_breed = self.get_coeff('CoeffBreedLeafBlade')
        _red_absorption_rate = self.get_time_dat('RedAbsorptionRate')
        _effective_sunray_receiving_area_rate = self.get_time_dat('EffectiveSunRayReceivingAreaRate')
        _vegetation_coverage = self.get_time_dat('PCR')
        _red_eff = 1 / (0.985 * (1 + (math.exp(-8.0 * (max(0, (_red_absorption_rate - 0.3)) / 0.7 - 0.5)))))
        _esrar_eff = 1.0 - _effective_sunray_receiving_area_rate
        _cover_eff = 1.0 - _vegetation_coverage
        self.Items['RsLeafBlade'] = _coeff_breed * _cover_eff * _red_eff * _p_total_weight

    def calc_rs_leaf_sheath(self):
        _coeff_breed = self.get_coeff('CoeffBreedLeafSheath')
        _p_leaf_blade_weight = self.get_time_dat('WeightLeafBlade', True)
        _effective_sunray_receiving_area_rate = self.get_time_dat('EffectiveSunRayReceivingAreaRate')
        _var = (1 - _effective_sunray_receiving_area_rate)
        _vegetation_coverage = self.get_time_dat('PCR')
        _cover_eff = 1.0 - _vegetation_coverage
        self.Items['RsLeafSheath'] = _coeff_breed * _cover_eff * _p_leaf_blade_weight * _p_leaf_blade_weight

    def calc_rs_culm(self):
        _p_total_weight = self.get_time_dat('WeightTotal', True)
        _coeff_breed = self.get_coeff('CoeffBreedCulm')
        _effective_sunray_receiving_area_rate = self.get_time_dat('EffectiveSunRayReceivingAreaRate')
        self.Items['RsCulm'] = _coeff_breed * (1 - _effective_sunray_receiving_area_rate) * _p_total_weight

    def calc_rs_rootage(self):
        _p_soil_nitrogen_concentration = self.get_time_dat('SoilNitrogenConcentration', True)
        _nitrogen_assimilation = self.get_day_dat('NitrogenAssimilation')
        _p_total_weight = self.get_time_dat('WeightTotal', True)
        _coeff_breed = self.get_coeff('CoeffBreedRootage')
        _coeff0 = self.get_coeff('Coeff0RsRootage')
        _coeff1 = self.get_coeff('Coeff1RsRootage')
        _p_sum_of_nitrogen_assimilation = self.get_time_dat('SumOfNitrogenAssimilation', True)
        #_red_absorption_rate = self.get_time_dat('MaxRedAbsorptionRate')
        '''
        print(_coeff0 / _p_soil_nitrogen_concentration > _coeff_breed * _coeff1 * _p_sum_of_nitrogen_assimilation / _p_total_weight,
              _coeff0 / _p_soil_nitrogen_concentration,
              _coeff_breed * _coeff1 * _p_sum_of_nitrogen_assimilation / _p_total_weight)
        '''
        if _p_total_weight == 0:
            _rs_rootage = 0
        else:
            _rs_rootage = _coeff_breed * min(_coeff0 / _p_soil_nitrogen_concentration,
                                             _coeff1 * _p_sum_of_nitrogen_assimilation / _p_total_weight)

        self.Items['RsRootage'] = _rs_rootage

    def calc_rs_spike(self):
        self.Items['RsSpike'] = 0

    def calc_rs_rough_rice(self):
        _elapsed_days_since_panicle_differentiation = self.get_time_dat('ElapsedDaysSincePanicleDifferentiation', True)
        _elapsed_days_since_heading = self.get_time_dat('ElapsedDaysSinceHeading', True)

        if _elapsed_days_since_panicle_differentiation > 13 and _elapsed_days_since_heading < 3 :
            _coeff = self.get_coeff('CoeffRsRoughRice')
            _p_number_of_spikelet = self.get_time_dat('NumberOfSpikelet', True)
            _p_weight_roughrice = self.get_time_dat('WeightRoughRice', True)
            _tg_weight = 0.003 * self.get_coeff('ThousandGrainWeight') / 22.0
            _rs_rough_rice = _coeff * max(0 , (_tg_weight * _p_number_of_spikelet - _p_weight_roughrice))
        else:
            _rs_rough_rice = 0

        _p_rs_rough_rice = self.get_time_dat('RsRoughRice', True)
        _p_rs_sum = self.get_time_dat('RsSum', True)
        if ( _p_rs_rough_rice > 0 ) :
            _max_rs_rough_rice = 1.25 * _p_rs_rough_rice
        else:
            _max_rs_rough_rice = min(0.25 * _rs_rough_rice, 0.1 * _p_rs_sum)

        self.Items['RsRoughRice'] = min(_max_rs_rough_rice, _rs_rough_rice)

    def calc_rs_endosperm(self):
        _elapsed_days_since_heading = self.get_time_dat('ElapsedDaysSinceHeading', True)
        _coeff = self.get_coeff('CoeffBreedEndosperm')
        _p_number_of_rough_rice = self.get_time_dat('NumberOfRoughRice', True)
        _p_weight_endosperm = self.get_time_dat('WeightEndosperm', True)

        if _elapsed_days_since_heading > 0: # and _elapsed_days_since_heading < 36:
            _tg_weight = self.get_coeff('ThousandGrainWeight')
            _target_w = _tg_weight / 1000.0 * 0.75
            self.Items['RsEndosperm'] = _coeff * max(0 , (_target_w * _p_number_of_rough_rice - _p_weight_endosperm))
        else:
            self.Items['RsEndosperm'] = 0

        _p_rs_endosperm = self.get_time_dat('RsEndosperm', True)
        _p_rs_sum = self.get_time_dat('RsSum', True)
        if ( _p_rs_endosperm > 0 ) :
            _max_rs_endosperm = 1.15 * _p_rs_endosperm
        else:
            _max_rs_endosperm = 0.15 * self.Items['RsEndosperm']
            #_max_rs_endosperm = min(0.15 * self.Items['RsEndosperm'], 0.5 * _p_rs_sum)

        self.Items['RsEndosperm'] = min(_max_rs_endosperm, self.Items['RsEndosperm'])
    ###

    def calc_rs_sum(self):
        self.Items['RsSum'] = self.Items['RsLeafBlade'] + self.Items['RsLeafSheath'] + self.Items['RsCulm'] + self.Items['RsRootage'] + self.Items['RsSpike'] + self.Items['RsRoughRice'] + self.Items['RsEndosperm']
        #print(self.Items['RsLeafBlade'], self.Items['RsLeafSheath'], self.Items['RsCulm'], self.Items['RsRootage'], self.Items['RsSpike'], self.Items['RsRoughRice'], self.Items['RsEndosperm'])
    ###

    def calc_ds_leaf_blade(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsLeafBlade'] = self.Items['RsLeafBlade'] / self.Items['RsSum']
        else:
            self.Items['DsLeafBlade'] = 0

    def calc_ds_leaf_sheath(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsLeafSheath'] = self.Items['RsLeafSheath'] / self.Items['RsSum']
        else:
            self.Items['DsLeafSheath'] = 0

    def calc_ds_culm(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsCulm'] = self.Items['RsCulm'] / self.Items['RsSum']
        else:
            self.Items['DsCulm'] = 0

    def calc_ds_rootage(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsRootage'] = self.Items['RsRootage'] / self.Items['RsSum']
        else:
            self.Items['DsRootage'] = 0

    def calc_ds_spike(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsSpike'] = self.Items['RsSpike'] / self.Items['RsSum']
        else:
            self.Items['DsSpike'] = 0

    def calc_ds_rough_rice(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsRoughRice'] = self.Items['RsRoughRice'] / self.Items['RsSum']
        else:
            self.Items['DsRoughRice'] = 0

    def calc_ds_endosperm(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsEndosperm'] = self.Items['RsEndosperm'] / self.Items['RsSum']
        else:
            self.Items['DsEndosperm'] = 0

    ###
    def calc_dsm_leaf_blade(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsmLeafBlade'] = self.Items['RsmLeafBlade'] / self.Items['RsSum']
        else:
            self.Items['DsmLeafBlade'] = 0

    def calc_dsm_leaf_sheath(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsmLeafSheath'] = self.Items['RsmLeafSheath'] / self.Items['RsSum']
        else:
            self.Items['DsmLeafSheath'] = 0

    def calc_dsm_culm(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsmCulm'] = self.Items['RsmCulm'] / self.Items['RsSum']
        else:
            self.Items['DsmCulm'] = 0

    def calc_dsm_rootage(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsmRootage'] = self.Items['RsmRootage'] / self.Items['RsSum']
        else:
            self.Items['DsmRootage'] = 0

    def calc_dsm_spike(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsmSpike'] = self.Items['RsmSpike'] / self.Items['RsSum']
        else:
            self.Items['DsmSpike'] = 0

    def calc_dsm_rough_rice(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsmRoughRice'] = self.Items['RsmRoughRice'] / self.Items['RsSum']
        else:
            self.Items['DsmRoughRice'] = 0

    def calc_dsm_endosperm(self):
        if self.Items['RsSum'] > 0:
            self.Items['DsmEndosperm'] = self.Items['RsmEndosperm'] / self.Items['RsSum']
        else:
            self.Items['DsmEndosperm'] = 0

    ###
    '''
    def calc_scurose_for_growth(self):
        self.Items['SucroseForGrowth'] = max(0, self.get_day_dat('SucroseConsumption') - self.Items['MaintenanceRespiration'])
        if self.Items['SucroseForGrowth'] > self.Items['RsSum']:
            self.Items['SucroseSurpluse'] = self.Items['SucroseForGrowth'] - self.Items['RsSum']
            self.Items['SucroseForGrowth'] = self.Items['RsSum']
    '''

    def calc_w_leaf_blade(self):
        _p_effective_sunray_receiving_area_rate = self.get_time_dat('EffectiveSunRayReceivingAreaRate', True)
        if _p_effective_sunray_receiving_area_rate > 0.90:
            _carry_rate = 0.99
        else:
            _carry_rate = 1.0

        self.Items['QsLeafBlade'] = self.get_time_dat('SucroseForGrowth') * self.Items['DsLeafBlade']
        _weight = self.get_time_dat('WeightLeafBlade', True) * _carry_rate
        _weight += self.get_coeff('CoeffWeightLeafBlade') * self.Items['QsLeafBlade']

        self.Items['WeightLeafBlade'] = _weight

    def calc_w_leaf_sheath(self):
        self.Items['QsLeafSheath'] = self.get_time_dat('SucroseForGrowth') * self.Items['DsLeafSheath']
        _weight = self.get_time_dat('WeightLeafSheath', True)
        _weight += self.get_coeff('CoeffWeightLeafSheath') * self.Items['QsLeafSheath']

        self.Items['WeightLeafSheath'] = _weight

    def calc_w_culm(self):
        self.Items['QsCulm'] = self.get_time_dat('SucroseForGrowth') * self.Items['DsCulm']
        _weight = self.get_time_dat('WeightCulm', True)
        _weight += self.get_coeff('CoeffWeightCulm') * self.Items['QsCulm']

        self.Items['WeightCulm'] = _weight

    def calc_w_rootage(self):
        self.Items['QsRootage'] = self.get_time_dat('SucroseForGrowth') * self.Items['DsRootage']
        _weight = self.get_time_dat('WeightRootage', True)
        _weight += self.get_coeff('CoeffWeightRootage') * self.Items['QsRootage']

        self.Items['WeightRootage'] = _weight

    def calc_w_spike(self):
        self.Items['QsSpike'] = self.get_time_dat('SucroseForGrowth') * self.Items['DsSpike']
        _weight = self.get_time_dat('WeightSpike', True)
        _weight += self.get_coeff('CoeffWeightSpike') * self.Items['QsSpike']

        self.Items['WeightSpike'] = _weight

    def calc_w_roughRice(self):
        self.Items['QsRoughRice'] = self.get_time_dat('SucroseForGrowth') * self.Items['DsRoughRice']
        _weight = self.get_time_dat('WeightRoughRice', True)
        _weight += self.get_coeff('CoeffWeightRoughRice') * self.Items['QsRoughRice']

        self.Items['WeightRoughRice'] = _weight
        _tg_weight = 0.003 * self.get_coeff('ThousandGrainWeight') / 22.0
        self.Items['NumberOfRoughRice'] = _weight / _tg_weight

    def calc_w_endosperm(self):
        self.Items['QsEndosperm'] = self.get_time_dat('SucroseForGrowth') * self.Items['DsEndosperm']
        _weight = self.get_time_dat('WeightEndosperm', True)
        _weight += self.get_coeff('CoeffWeightEndosperm') * self.Items['QsEndosperm']

        self.Items['WeightEndosperm'] = _weight

    def calc_w_total(self):
        self.Items['WeightTotal'] = self.Items['WeightLeafBlade'] + self.Items['WeightLeafSheath'] + self.Items['WeightCulm'] + self.Items['WeightRootage'] + self.Items['WeightSpike'] + self.Items['WeightRoughRice'] + self.Items['WeightEndosperm']
    ###
    def calc_nitrogen_concentration(self):
        if self.Items['WeightTotal'] == 0:
            _nitrogen_concentration = 0
        else:
            _nitrogen_concentration = self.get_time_dat('SumOfNitrogenAssimilation') / self.Items['WeightTotal']

        self.Items['NitrogenConcentration'] = _nitrogen_concentration


    def calc_surface_area_of_leaf_blade(self):
        self.Items['SurfaceAreaOfLeafBlade'] = self.get_coeff('CoeffSurfaceAreaOfLeafBlade') * pow(self.Items['WeightLeafBlade'],2/3)

    def calc_surface_area_of_rootage(self):
        self.Items['SurfaceAreaOfRootage'] = self.get_coeff('CoeffSurfaceAreaOfRootage') * pow(self.Items['WeightRootage'],2/3)

    def calc_number_of_rough_rice(self):
        _p_elapsed_days_since_panicle_differentiation = self.get_time_dat('ElapsedDaysSincePanicleDifferentiation', True)
        if _p_elapsed_days_since_panicle_differentiation < 8 or _p_elapsed_days_since_panicle_differentiation > 28:
            _n_vrr = 0
            _n_crr = 0
        elif _p_elapsed_days_since_panicle_differentiation < 14:
            _n_vrr = 3.8 * (_p_elapsed_days_since_panicle_differentiation - 7)
            _n_crr = 0.2 * (_p_elapsed_days_since_panicle_differentiation - 7)
        elif _p_elapsed_days_since_panicle_differentiation < 24:
            _n_vrr = 19
            _n_crr = 1
        else:
            _n_vrr = 3.8 * (29 - _p_elapsed_days_since_panicle_differentiation)
            _n_crr = 0.2 * (29 - _p_elapsed_days_since_panicle_differentiation)

        _sucrose_production = self.get_day_dat('SucroseProduction')

        _nitrogen_assimilation = self.get_day_dat('NitrogenAssimilation')
        _coeff_max_nitrogen = self.get_coeff('CoeffMaxNitrogenAssimilationByDay')
        _n_dec = _nitrogen_assimilation / _coeff_max_nitrogen

        #if _n_crr > 0 : print(_s_dec>_n_dec, _s_dec, _n_dec)

        self.Items['NumberOfSpikelet'] = self.get_time_dat('NumberOfSpikelet', True) + (_n_vrr *_n_dec + _n_crr) * 30 * 15

    def calc_volume_of_rough_rice(self):
        _coeff0 = self.get_coeff('Coeff0VolumeOfRoughRice')
        _weight_endosperm = self.Items['WeightEndosperm']
        _coeff1 = self.get_coeff('Coeff1VolumeOfRoughRice')
        _nitrogen_assimilation = self.get_day_dat('NitrogenAssimilation')
        _rn_endosperm = self.get_time_dat('RnEndosperm')

        self.Items['VolumeOfRoughRice'] = _coeff0 * _weight_endosperm + _coeff1 * _nitrogen_assimilation * _rn_endosperm


def _main():
    df = pd.read_csv('./36.25913074_140.0676563.calc.csv', parse_dates=True, index_col='Date')
    df = df.fillna(0)

    dfcc = pd.read_csv('../global_param/coeff.csv', comment='#')
    dfcb = pd.read_csv('../global_param/coeff_breed.csv', comment='#')
    dfc = pd.concat([dfcc,dfcb], axis=1)

    print(df.shape, dfc.shape)

    gs = GsmSucrose()
    n_row = df.index.size
    for i in range(1, n_row-1, 24):
        t_df = df[i:i+24]
        t_dfd = t_df.to_dict()
        c_df = df[i-1:i+24]
        c_dfd = c_df.to_dict()
        gs.set_coeff_db(dfc)
        gs.set_today_db(t_dfd)
        gs.set_timebase_db(c_dfd, c_df.index)

        gs.calculate()

        uc_df = pd.DataFrame(c_dfd)
        df.update(uc_df)

    df.to_csv('t.new.csv')

if __name__ == '__main__':
    _main()
