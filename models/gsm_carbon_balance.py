import math
import datetime
import json
import pandas as pd

from .gsm_base import GsmBase

class GsmCarbon(GsmBase):

    def __init__(self):
        self.LodgingDate = None
        self.Items = {
                      'RedAbsorptionRate':0, 'MaxRedAbsorptionRate':0,
                      'EffectiveSolarRadiation':0,
                      'CarbonAssimilation':0, 'SucroseProduction':0,'SucroseProductionTempTerm':0,
                      'SucroseTranslocation':0,
                      'SucroseConsumption':0, 'SucroseForGrowth':0,
                      'DailySucroseProduction':0, 'DailySucroseConsumption':0,
                      'SumOfSucroseProduction':0,
                      'SumOfSucroseAccumulation':0,
                      'SumOfSucroseProductionSincePanicleDifferentiation':0,
                      'SucroseAccumulation':0,
                      'MaxDailySucroseProduction': 0 }

    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):
        self.calc_red_absorption_rate()

        self.calc_effective_solar_radiation()
        self.calc_sucrose_accumulation()
        self.calc_carbon_assimilation()
        self.calc_sucrose_production()
        self.calc_sucrose_translocation()
        self.calc_max_daily_sucrose_production()
        self.calc_sucrose_consumption()
        self.calc_daily_sucrose()
        self.calc_sum_of_sucrose_accumulation()
        self.calc_sum_of_sucrose_accumulation_since_panicle_differentiation()

        self.update_timebase_db()
        self.count_up_time()

    ###
    def set_lodging(self, date):
        self.LodgingDate = datetime.datetime.strptime(date, '%Y-%m-%d').date()

    ###
    def calc_red_absorption_rate(self): # day-sim
        _p_surface_area_of_leaf_blade = self.get_time_dat('SurfaceAreaOfLeafBlade', True)
        if _p_surface_area_of_leaf_blade > 0 :
            if self.idx_time == 13:
                _coeff = self.get_coeff('CoeffRedAbsorptionRate')
                _p_sum_of_nitrogen_distribution_amount_of_leaf_blade = self.get_time_dat('SumOfNitrogenDistributionAmountOfLeafBlade', True)
                _ave_n = _p_sum_of_nitrogen_distribution_amount_of_leaf_blade / _p_surface_area_of_leaf_blade
                _rate = 0.15 * min(1.0, _p_surface_area_of_leaf_blade / 0.5)
                _max_n = _ave_n * (1.0 + _rate)
                _min_n = _ave_n * (1.0 - _rate)
                _lai_min = _max_n - (_max_n - _min_n) / _p_surface_area_of_leaf_blade * self.get_time_dat('LeafAreaIndex')
                _red_absorption_rate = _coeff * ((_max_n - _lai_min) / 2 + _lai_min)
            else:
                _red_absorption_rate = self.get_time_dat('RedAbsorptionRate', True)
                _max_n = self.get_time_dat('MaxRedAbsorptionRate', True)
        else:
            _red_absorption_rate = 0
            _max_n = 0

        self.Items['MaxRedAbsorptionRate'] = _max_n
        self.Items['RedAbsorptionRate'] = min(1, _red_absorption_rate)

    def calc_effective_solar_radiation(self): # hour-sim
        _solar_radiation = self.get_time_dat('SolarRadiation')
        self.Items['EffectiveSolarRadiation'] = 0.27 * _solar_radiation

    def calc_sucrose_accumulation(self): # hour-sim
        if self.check_sunrise():
            _p_daily_sucrose_production = self.get_time_dat('DailySucroseProduction', True)
            _p_sucrose_consumption = self.get_time_dat('SucroseConsumption', True)
            self.Items['SucroseAccumulation'] = _p_daily_sucrose_production - _p_sucrose_consumption
        else:
            self.Items['SucroseAccumulation'] = 0

    def calc_carbon_assimilation(self): # hour-sim
        _red_absorption_rate = self.Items['RedAbsorptionRate']
        _effective_sunray_receiving_area_rate = self.get_time_dat('EffectiveSunRayReceivingAreaRate')
        _effective_solar_radiation = self.Items['EffectiveSolarRadiation']
        _coeff = self.get_coeff('CoeffCarbonAssimilation')
        self.Items['CarbonAssimilation'] = _coeff * _red_absorption_rate * _effective_sunray_receiving_area_rate * _effective_solar_radiation
        # should use yesterday's data ?

    def calc_sucrose_production(self): # hour-sim
        _air_temperature = self.get_time_dat('SensorAirTemperature')
        if _air_temperature == None:
            _air_temperature = self.get_time_dat('AirTemperature')
        _red_absorption_rate = self.Items['RedAbsorptionRate']
        _effective_sunray_receiving_area_rate = self.get_time_dat('EffectiveSunRayReceivingAreaRate')
        _effective_solar_radiation = self.Items['EffectiveSolarRadiation']
        _coeff0 = self.get_coeff('Coeff0SucroseProduction')
        _coeff1 = self.get_coeff('Coeff1SucroseProduction')
        _c0 = _coeff0 * _red_absorption_rate * _effective_sunray_receiving_area_rate * _effective_solar_radiation
        _dep_temp = -0.0002 * (_air_temperature**3) + 0.0073 * (_air_temperature**2) + 0.1558 * _air_temperature + 1.0707
        _c1 = _coeff1 * _red_absorption_rate * _effective_sunray_receiving_area_rate * _dep_temp

        _hd = self.get_time_dat('HumidityDeficit')
        '''
        if _hd > 7.5 :
            _hd_eff = 1.0 - min(1.0,(_hd - 7.5) / 10)
        elif _hd < 1.5:
            _hd_eff = _hd / 6
        else:
            _hd_eff = 1.0
        #print('HumidityDeficit:', _hd, _hd_eff)
        _hd_eff = 1.0
        '''

        if _hd > 7 :
            _hd_eff = 1.0 - min(1.0, (_hd - 7.0) * 0.0267)
        elif _hd < 4:
            _hd_eff = 1.0 - min(1.0, (4.0 - _hd) * 0.0267)
        else:
            _hd_eff = 1.0

        if self.LodgingDate is not None and self.TimeBaseDT[self.idx_time].date() >= self.LodgingDate :
            _lodging_eff = 0.6
        else:
            _lodging_eff = 1.0

        self.Items['SucroseProductionTempTerm'] = _c1 # term for evaluting
        self.Items['SucroseProduction'] = min(_c0, _c1) * _hd_eff * _lodging_eff
        self.Items['SumOfSucroseProduction'] = self.Items['SucroseProduction'] + self.get_time_dat('SumOfSucroseProduction', True)

    def calc_sucrose_translocation(self): # hour-sim
        _elapsed_days_since_heading = self.get_time_dat('ElapsedDaysSinceHeading', True)
        _p_total_weight = self.get_time_dat('WeightTotal', True)
        _p_sum_of_sucrose_accumulation = self.get_time_dat('SumOfSucroseAccumulation', True)
        _sucrose_production = self.Items['SucroseProduction']
        _effective_solar_radiation = self.Items['EffectiveSolarRadiation']
        _coeff = self.get_coeff('CoeffSucroseTranslocation')

        if _elapsed_days_since_heading > 0:
            _trans_rate = 0.25
        else:
            _trans_rate = 0

        _p_daily_sucrose_production = self.get_time_dat('DailySucroseProduction', True)
        if self.check_sunset() and _p_daily_sucrose_production > 0 and _p_total_weight > 0:
            self.Items['SucroseTranslocation'] = min(_trans_rate * _p_sum_of_sucrose_accumulation,
                                                     _coeff * _p_sum_of_sucrose_accumulation / (_p_daily_sucrose_production * _p_daily_sucrose_production) * _p_total_weight)
        else:
            self.Items['SucroseTranslocation'] = 0

    def calc_max_daily_sucrose_production(self):
        if self.check_sunrise():
            _max_daily_sucrose_production = 0
        else:
            _p_max_daily_sucrose_production = self.get_time_dat('MaxDailySucroseProduction', True)
            _max_daily_sucrose_production = _p_max_daily_sucrose_production + self.Items['SucroseProduction']
        self.Items['MaxDailySucroseProduction'] = _max_daily_sucrose_production

    def calc_sucrose_consumption(self): # hour-sim
        _water_temperature = self.get_time_dat('SensorWaterTemperature')
        if _water_temperature == None:
            _water_temperature = self.get_time_dat('eTMPW') - 273.15
        _total_weight = self.get_time_dat('WeightTotal', True)
        _coeff = self.get_coeff('CoeffSucroseConsumption')

        self.Items['SucroseConsumption'] = _coeff * 2.0 ** ((_water_temperature - 25)/ 10) * _total_weight

    def calc_daily_sucrose(self):
        _p_daily_sc_production = self.get_time_dat('DailySucroseProduction', True)
        _p_maintenance_resp = self.get_time_dat('MaintenanceRespiration', True)
        _sc_production = self.Items['SucroseProduction']
        _sc_translocation = self.Items['SucroseTranslocation'] * 0.9
        self.Items['DailySucroseProduction'] = max(0, _p_daily_sc_production + _sc_production + _sc_translocation - _p_maintenance_resp)

        _p_daily_sc_consumption = self.get_time_dat('DailySucroseConsumption', True)
        self.Items['DailySucroseConsumption'] = _p_daily_sc_consumption + self.Items['SucroseConsumption']

        #print("D-SC:", self.Items['DailySucroseProduction'], _p_daily_sc_production, _sc_production, _sc_translocation, _p_maintenance_resp, self.Items['DailySucroseConsumption'])

        if self.check_sunrise():
            self.Items['SucroseForGrowth'] = min(self.Items['DailySucroseProduction'], self.Items['DailySucroseConsumption'])
            self.Items['SucroseAccumulation'] = max(0, self.Items['DailySucroseProduction'] - self.Items['DailySucroseConsumption'])
            self.Items['DailySucroseProduction'] = 0
            self.Items['DailySucroseConsumption'] = 0
        else:
            self.Items['SucroseForGrowth'] = 0
            self.Items['SucroseAccumulation'] = 0

    def calc_sum_of_sucrose_accumulation(self): # hour-sim
        _p_sum_of_sucrose_accumulation = self.get_time_dat('SumOfSucroseAccumulation', True)
        self.Items['SumOfSucroseAccumulation'] = _p_sum_of_sucrose_accumulation + self.Items['SucroseAccumulation'] - self.Items['SucroseTranslocation']

    def calc_sum_of_sucrose_accumulation_since_panicle_differentiation(self): # hour-sim
        _p_sum_of_sucrose_production_since_panicle_differentiation = self.get_time_dat('SumOfSucroseProductionSincePanicleDifferentiation', True)
        _p_elapsed_daya_since_panicle_differentiation = self.get_time_dat('ElapsedDaysSincePanicleDifferentiation', True)
        if _p_elapsed_daya_since_panicle_differentiation > 0:
            _sucrose_production = self.Items['SucroseProduction']
            _sum = _p_sum_of_sucrose_production_since_panicle_differentiation + _sucrose_production
        else:
            _sum = 0
        self.Items['SumOfSucroseProductionSincePanicleDifferentiation'] = _sum


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
