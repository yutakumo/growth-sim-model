import math
import json
import datetime
import pandas as pd

from .gsm_base import GsmBase

class GsmNitrogenBalance(GsmBase):

    def __init__(self):
        self.WaterSupplyNitrogenContent = None
        self.WaterSupplyOxygenContent = 5
        self.SnManureInfo = {}
        self.SnManureIinit = 0
        #self.NitTransRate = 0.005
        self.Items = {'SnOrganicDecomposition':0, 'SumOfSnOrganicDecomposition':0, 'OrganicDecompositionElutionDays':0,
                      'SnWater':0, 'SnRain':0, 'SoilNitrogenFixation':0,
                      'SnSum':0,
                      'Loss':0, 'Denitrification':0,
                      'SoilNitrogenConcentration':0, 'NitrogenAssimilation':0, 'NitrogenTranslocation':0,
                      'SumOfNitrogenAssimilation':0,
                      'NitrogenTranslocationChoropalstBreakup':0,
                      'VariableForSurfaceDrainage':0}

    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):
        self.calc_sn_organic_decompostion()
        self.calc_sn_water()
        self.calc_sn_rain()
        self.calc_soil_nitrogen_fixation()
        self.calc_sum_of_supply_nitrogen()
        self.calc_soil_nitrogen_concentration()
        self.calc_nitrogen_assimilation()
        self.calc_nitrogen_translocation()
        self.calc_nitrogen_translocation_by_chloroplast_breakup()
        self.calc_loss()
        self.calc_denitrification()

        self.update_timebase_db()
        self.count_up_time()

    ###

    def set_sn_manure_info(self, _info):
        self.SnManureInfo = _info
        d_date = datetime.datetime.strptime(self.SnManureInfo['date'],'%Y-%m-%d').date()
        self.SnManureInfo['date'] = d_date
        if _info.get('init') is not None:
            self.SnManureIinit = _info['init']

    def set_water_supply_nitrogen_content(self, wss):
        self.WaterSupplyNitrogenContent = wss

    def _calc_elution(self, a, b, k, t):
        return a * (1 - math.exp(-k * t)) + b

    ###

    def calc_sn_organic_decompostion(self): # hour-sim
        _snmi = self.SnManureInfo
        _elapsed_days = (self.TimeBaseDT[self.idx_time].date() - _snmi['date']).days
        _elapsed_days = max(0, _elapsed_days)
        _bdate = _snmi['begin_elution']
        _fdate = _snmi['finish_elution']

        _amount = _snmi['amount']
        _rate = _snmi['rate'] / 100

        _p_elution_days = self.get_time_dat('OrganicDecompositionElutionDays', True)
        _p_soil_temperature = self.get_time_dat('SensorSoilTemperature', True)
        if _p_soil_temperature == None:
            _p_soil_temperature = self.get_time_dat('eTMPS', True) - 273.15

        if _p_soil_temperature == -273.15:
            _organic_decomposition_elution_days = _p_elution_days
        else:
            _organic_decomposition_elution_days = _p_elution_days + math.exp(70000 * (_p_soil_temperature - 25) / (298.15 * 8.31 * (_p_soil_temperature + 273.15))) / 24.0

        self.Items['OrganicDecompositionElutionDays'] = _organic_decomposition_elution_days

        _elapsed_days = self.Items['OrganicDecompositionElutionDays']
        _init_dec = min(1.0, _elapsed_days / 24)
        _sn_organic_decompostion = self._calc_elution(_rate * _amount, _init_dec * 0.01 / 100 * _amount, 0.005, _elapsed_days)
        self.Items['SumOfSnOrganicDecomposition'] = _sn_organic_decompostion
        self.Items['SnOrganicDecomposition'] = _sn_organic_decompostion - self.get_time_dat('SumOfSnOrganicDecomposition', True)

    def calc_sn_water(self): # day-sim or hour-sim
        _inlet = self.get_time_dat('WFLXinlet')
        if math.isnan(_inlet):
            _inlet = self.get_time_dat('eWFLXinlet')

        self.Items['SnWater'] = self.WaterSupplyNitrogenContent / 1000 * max(0, _inlet)

    def calc_sn_rain(self): # day-sim or hour-sim
        self.Items['SnRain'] = 0.4 / 1000 * self.get_time_dat('Rainfall', True)

    def calc_soil_nitrogen_fixation(self):
        self.Items['SoilNitrogenFixation'] = 0

    def calc_sum_of_supply_nitrogen(self): # day-sim or hour-sim
        self.Items['SnSum'] = self.get_time_dat('SnChemicalFertilizer') + self.get_time_dat('SnCoatedFertilizer') + self.get_time_dat('SnOrganicFertilizer') + self.Items['SnOrganicDecomposition'] + self.Items['SnWater'] + self.Items['SnRain'] + self.Items['SoilNitrogenFixation']

    def calc_soil_nitrogen_concentration(self): # day-sim
        _p_loss = self.get_time_dat('Loss', True)
        _p_denitrification = self.get_time_dat('Denitrification', True)
        _p_nitrogen_assimilation = self.get_time_dat('NitrogenAssimilation', True)
        _p_soil_nitrogen_concentration = self.get_time_dat('SoilNitrogenConcentration', True)
        if self.TimeBaseDT[self.idx_time].date() == self.SnManureInfo['date']:
            _p_soil_nitrogen_concentration += self.SnManureIinit
            self.SnManureIinit = 0
        _sn_sum = self.Items['SnSum']
        self.Items['SoilNitrogenConcentration'] = max(0, _p_soil_nitrogen_concentration - _p_nitrogen_assimilation - _p_loss - _p_denitrification) + _sn_sum

    ##---- soil

    def calc_nitrogen_assimilation(self): # day-sim
        _p_surface_area_of_rootage = self.get_time_dat('SurfaceAreaOfRootage', True)
        _p_water_depth = self.get_time_dat('eWDPcm', True) * 10.0
        _depth_th = 100 # tentative value
        if _p_water_depth < 0:
            _rate = max(0, (_depth_th + _p_water_depth)) / _depth_th
        else:
            _rate = 1

        _elapsed_days_since_heading = self.get_time_dat('ElapsedDaysSinceHeading', True)

        #if _elapsed_days_since_heading > 0:
        #_rate = _rate * max(0, (120 - _elapsed_days_since_heading) / 120)

        _c0 = self.get_coeff('Coeff0NitrogenAssimilation') * _rate * _p_surface_area_of_rootage * self.Items['SoilNitrogenConcentration']

        _p_weight_total = self.get_time_dat('WeightTotal', True)
        _red_absorption_rate = self.get_time_dat('RedAbsorptionRate')
        _c1 = self.get_coeff('Coeff1NitrogenAssimilation') * _p_weight_total * (1.0 - _red_absorption_rate)

        #print(_c0, _c1, _p_weight_total, _red_absorption_rate)

        #print("N-Assil", self.Items['NitrogenAssimilation'], _c0, _c1, self.get_time_dat('RnSum', True))
        #self.Items['NitrogenAssimilation'] = min(_c0, _c1) / 24
        self.Items['NitrogenAssimilation'] = min(_c0, (self.get_time_dat('RnSum', True) * 1.1 - self.get_time_dat('NitrogenTranslocationChoropalstBreakup', True))) / 24
        self.Items['SumOfNitrogenAssimilation'] = self.Items['NitrogenAssimilation'] + self.get_time_dat('SumOfNitrogenAssimilation',True)

        #self.Items['NitrogenAssimilation'] = min(_c0, self.get_time_dat('RnSum', True) * 1.1) / 24

    def calc_nitrogen_translocation(self): # day-sim
        _p_weight_total = self.get_time_dat('WeightTotal', True)
        if _p_weight_total > 0:
            _const = self.get_coeff('ConstNitrogenTranslocation')
            _coeff = self.get_coeff('CoeffNitrogenTranslocation')
            _nitrogen_assimilation = self.Items['NitrogenAssimilation']
            self.Items['NitrogenTranslocation'] = max(0, _const - _coeff * _nitrogen_assimilation / _p_weight_total)
        else:
            self.Items['NitrogenTranslocation'] = 0

    def calc_loss(self): # day-sim
        _soil_nitrogen_concentration = self.Items['SoilNitrogenConcentration']
        _coeff = self.get_coeff('CoeffLoss')
        self.Items['Loss'] = max(0, _coeff * _soil_nitrogen_concentration) / 24

    def calc_denitrification(self): #
        _coeff = self.get_coeff('CoeffDenitrification')
        _p_water_temperature = self.get_time_dat('SensorWaterTemperature', True)
        if _p_water_temperature == None:
            _p_water_temperature = self.get_time_dat('eTMPW', True) - 273.15
        _eff_temper = 1 + (_p_water_temperature - 20) * 0.05
        _soil_nitrogen_concentration = self.Items['SoilNitrogenConcentration']
        _p_soil_oxygen_concentration = self.get_time_dat('SoilOxygenConcentration', True)
        self.Items['Denitrification'] = _coeff * max(0, _p_soil_oxygen_concentration * _soil_nitrogen_concentration * _eff_temper) / 24


    def calc_nitrogen_translocation_by_chloroplast_breakup(self): # day-sim
        _p_effective_sunray_receiving_area_rate = self.get_time_dat('EffectiveSunRayReceivingAreaRate', True)
        if _p_effective_sunray_receiving_area_rate > 0.80:
            _p_sum_of_nitrogen_distribution_amount_of_leafblade = self.get_time_dat('SumOfNitrogenDistributionAmountOfLeafBlade', True)
            _coeff = self.get_coeff('CoeffNTranslocationChoropalstBreakup')
            self.Items['NitrogenTranslocationChoropalstBreakup'] = _p_sum_of_nitrogen_distribution_amount_of_leafblade * _coeff / 24
        else:
            self.Items['NitrogenTranslocationChoropalstBreakup'] = 0

def _main():

    df = pd.read_csv('./36.25913074_140.0676563.calc.csv', parse_dates=True, index_col='Date')
    df = df.fillna(0)

    dfcc = pd.read_csv('../global_param/coeff.csv', comment='#')
    dfcb = pd.read_csv('../global_param/coeff_breed.csv', comment='#')
    dfc = pd.concat([dfcc,dfcb], axis=1)

    print(df.shape, dfc.shape)
    gn = GsmNitrogenBalance()
    jma = {
        "date":"2019-06-01",
        "amount": 400,
        "rate": 5,
        "begin_elution": 0,
        "finish_elution": 360
    }
    gn.set_sn_manure_info(jma)
    gn.set_water_supply_nitrogen_content(0.8)

    n_row = df.index.size
    for i in range(1, n_row-1, 24):
        c_df = df[i-1:i+24]
        c_dfd = c_df.to_dict()
        gn.set_coeff_db(dfc)
        gn.set_timebase_db(c_dfd, c_df.index)

        gn.calculate()

        uc_df = pd.DataFrame(c_dfd)
        df.update(uc_df)

    df.to_csv('t.new.csv')

if __name__ == '__main__':
    _main()
