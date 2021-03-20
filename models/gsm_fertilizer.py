import math
import json
import datetime
import pandas as pd

from .gsm_base import GsmBase

class GsmFertilizer(GsmBase):

    def __init__(self):
        self._sn_fertilizer_info = {}

        self.Items = {'SnChemicalFertilizer':0, 'SnCoatedFertilizer':0, 'SnOrganicFertilizer':0}

    def initialize(self):
        for item in self.Items:
            self.Items[item] = 0

    def calculate(self):
        self.calc_sn_chemical_fertilizer()
        self.calc_sn_coated_fertilizer()
        self.calc_sn_organic_fertilizer()

        self.update_timebase_db()
        self.count_up_time()

    ###
    def set_sn_feritilizer_info(self, _info):
        self._sn_fertilizer_info = _info
        print('Number of Ferilizer is ',len(self._sn_fertilizer_info))
        for i in range(len(self._sn_fertilizer_info)):
            d_date = datetime.datetime.strptime(self._sn_fertilizer_info[i]['date'],'%Y-%m-%d').date()
            self._sn_fertilizer_info[i]['date'] = d_date
            print(self._sn_fertilizer_info[i]['date'], type(self._sn_fertilizer_info[i]['date']))

            _snfi_coated = self._sn_fertilizer_info[i]['coated_fertilizer']
            for j in range(len(_snfi_coated)):
                _key = 'CoatedFertilizerElutionDays_' + str(j)
                self.Items[_key] = 0
    ###
    def calc_sn_chemical_fertilizer(self):
        _sn_chemical_fertilizer = 0
        for i in range(len(self._sn_fertilizer_info)):
            _snfi = self._sn_fertilizer_info[i]
            _elapsed_days = (self.TimeBaseDT[self.idx_time].date() - _snfi['date']).days
            if _elapsed_days < 1 or _elapsed_days > 20 :
                continue
            _amount = _snfi['amount']
            _snfi_chemi = _snfi['chemical_fertilizer']
            for j in range(len(_snfi_chemi)):
                _rate = _snfi_chemi[j]['rate'] / 100
                if _elapsed_days < 4:
                    _day_sn_chemical_fertilizer = 1 / 15 / 3 * _elapsed_days
                elif _elapsed_days < 14:
                    _day_sn_chemical_fertilizer = 1 / 15
                elif _elapsed_days < 21:
                    _day_sn_chemical_fertilizer = 1 / 15 / 7 * (7 - (_elapsed_days - 13))
                _sn_chemical_fertilizer += _amount * _rate * _day_sn_chemical_fertilizer / 24

        self.Items['SnChemicalFertilizer'] = _sn_chemical_fertilizer

    def _get_elution_in_coated_fertilizer(self, d, k, elution_days):
        return 1 / math.pow(1 + d * math.exp(math.exp(d + 1) - 1 - k * elution_days), 1/d)

    def calc_sn_coated_fertilizer(self):
        _sn_coated_fertilizer = 0
        _ccount = 0
        for i in range(len(self._sn_fertilizer_info)):
            _snfi = self._sn_fertilizer_info[i]
            _elapsed_days = (self.TimeBaseDT[self.idx_time].date() - _snfi['date']).days
            _elapsed_days = max(0, _elapsed_days)
            if _elapsed_days < 1:
                continue
            _amount = _snfi['amount']
            _snfi_coated = _snfi['coated_fertilizer']
            for j in range(len(_snfi_coated)):
                _elution = _snfi_coated[j]['80_persent_elution']
                _rate = _snfi_coated[j]['rate'] / 100

                _key = 'CoatedFertilizerElutionDays_' + str(_ccount)
                _ccount += 1
                _p_elution_days = self.get_time_dat(_key, True)
                _p_water_temperature = self.get_time_dat('SensorWaterTemperature', True)
                if _p_water_temperature == None:
                    _p_water_temperature = self.get_time_dat('eTMPW', True) - 273.15

                self.Items[_key] = _p_elution_days + _p_water_temperature / 25.0 / 24.0

                if _snfi_coated[j]['type'] == 'sigmoid':
                    _d = -0.007 * math.log(_elution) + 1.1774
                    _k = math.exp(-1.009 * math.log(_elution) + 2.1706)

                else:
                    _d = 0.00004 * _elution * _elution - 0.0095 * _elution - 0.1786
                    _k = math.exp(0.00015 * _elution * _elution - 0.0417 * _elution - 1.4629)

                _p_rate_sn_coated_fertilizer = self._get_elution_in_coated_fertilizer(_d, _k, _p_elution_days) if _elapsed_days > 0 else 0
                _rate_sn_coated_fertilizer = self._get_elution_in_coated_fertilizer(_d, _k, self.Items[_key])

                _day_sn_coated_fertilizer = (_rate_sn_coated_fertilizer - _p_rate_sn_coated_fertilizer) * _rate * _amount

                _sn_coated_fertilizer += _day_sn_coated_fertilizer

        self.Items['SnCoatedFertilizer'] = _sn_coated_fertilizer

    def _calc_elution(self, a, b, k, t):
        return a * (1 - math.exp(-k * t)) + b

    def calc_sn_organic_fertilizer(self):
        _sn_organic_fertilizer = 0
        _ocount = 0
        for i in range(len(self._sn_fertilizer_info)):
            _snfi = self._sn_fertilizer_info[i]
            if ((self.TimeBaseDT[self.idx_time].date() - _snfi['date']).days) < 0:
                continue

            _p_soil_temperature = self.get_time_dat('SensorSoilTemperature', True)
            if _p_soil_temperature == None:
                _p_soil_temperature = self.get_time_dat('eTMPS', True) - 273.15

            _amount = _snfi['amount']
            _snfi_organic = _snfi['organic_fertilizer']

            for j in range(len(_snfi_organic)):
                _rate = _snfi_organic[j]['rate'] / 100 * (_snfi_organic[j]['NO'] - _snfi_organic[j]['NI']) / 100
                _init_rate = _snfi_organic[j]['rate'] / 100 * _snfi_organic[j]['NI'] / 100

                _key = 'OrganicFertilizerElutionDays_' + str(_ocount)
                _p_elution_days = self.get_time_dat(_key, True)

                if _p_soil_temperature == -273.15:
                    _elapsed_days = _p_elution_days
                else:
                    _elapsed_days = _p_elution_days + math.exp(_snfi_organic[j]['Ea'] * (_p_soil_temperature - 25) / (298.15 * 8.31 * (_p_soil_temperature + 273.15))) / 24
                self.Items[_key] = _elapsed_days
                _init_dec = min(1.0, _elapsed_days / 24)
                _sum_of_sn_organic_fertilizer = self._calc_elution(_rate * _amount, _init_dec * _init_rate * _amount, _snfi_organic[j]['k'], _elapsed_days)

                _key = 'SumOfSnOrganicFertilizer_' + str(_ocount)
                self.Items[_key] = _sum_of_sn_organic_fertilizer
                _sn_organic_fertilizer += _sum_of_sn_organic_fertilizer - self.get_time_dat(_key, True)

                _ocount += 1

        self.Items['SnOrganicFertilizer'] = _sn_organic_fertilizer


def _main():
    df = pd.read_csv('./36.25913074_140.0676563.calc.csv', parse_dates=True, index_col='Date')
    df = df.fillna(0)

    dfcc = pd.read_csv('../global_param/coeff.csv', comment='#')
    dfcb = pd.read_csv('../global_param/coeff_breed.csv', comment='#')
    dfc = pd.concat([dfcc,dfcb], axis=1)

    print(df.shape, dfc.shape)
    gf = GsmFertilizer()

    ff = open('../global_param/fertilizer.json')
    jf = json.load(ff)

    sch_fertilizer = [ {
        "date":"2019-04-12",
        "fertilizer_id":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa50",
        "amount": 100
        } ]
    for i in range(len(sch_fertilizer)):
        print(sch_fertilizer[i])
        for j in range(len(jf)):
            if sch_fertilizer[i]['fertilizer_id'] == jf[j]['id']:
                sch_fertilizer[i].update(jf[j])
    gf.set_sn_feritilizer_info(sch_fertilizer)

    print(sch_fertilizer)

    n_row = df.index.size
    for i in range(1, n_row-1, 24):
        c_df = df[i-1:i+24]
        c_dfd = c_df.to_dict()
        gf.set_coeff_db(dfc)
        gf.set_timebase_db(c_dfd, c_df.index)

        gf.calculate()

        uc_df = pd.DataFrame(c_dfd)
        df.update(uc_df)

    df.to_csv('t.new.csv')

if __name__ == '__main__':
    _main()
