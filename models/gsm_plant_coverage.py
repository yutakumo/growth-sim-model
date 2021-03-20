#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import date, datetime

from .gsm_base import GsmBase

class GsmPlantCoverage(GsmBase):
    plantSpecificHeat = 1e3 ##J/kg K
    #coverageParams = {'2020-03-01' : 0.2,
    #                  '2020-04-15' : 0.95
    #                  } ## for wheat

    def __init__(self):
        self.Items = {'PCR' : 0}
        self.coverageParams = {}
        self.growthDay0:date
        self.growthDay1:date

    def calculate(self):
        self.calc_plantCoverageRatio()

        self.update_timebase_db()
        self.count_up_time()

    def initialize(self):
        self.calc_plantCoverageRatio()

    def setCoverageParams(self, _dict):
        self.coverageParams = _dict
        days = sorted(list(self.coverageParams.keys()))
        self.growthDay0 = datetime.strptime(days[0], '%Y-%m-%d').date()
        self.growthDay1 = datetime.strptime(days[1], '%Y-%m-%d').date()

    def plantCoverageRatioLinearBase(self, _t0:date, _t1:date, _date='yyyymmdd', _c0=0.2, _c1=0.95):
        t = date(int(_date[:4]), int(_date[4:6]), int(_date[6:8]))
        if t <= _t0:
            return _c0
        elif _t0 < t < _t1:
            return _c0 + (_c1 - _c0) / (_t1 - _t0).days * (t - _t0).days
        else:
            return _c1

    def plantCoverageRatioLinear(self, _date='yyyymmdd'):
        c0 = self.coverageParams[self.growthDay0.strftime('%Y-%m-%d')]
        c1 = self.coverageParams[self.growthDay1.strftime('%Y-%m-%d')]
        return self.plantCoverageRatioLinearBase(_date=_date, _t0=self.growthDay0, _t1=self.growthDay1, _c0=c0, _c1=c1)

    def calc_plantCoverageRatio(self):
        self.Items['PCR'] = self.plantCoverageRatioLinear(self.get_time().strftime('%Y%m%d'))

if __name__ == '__main__':
    import json
    common_info = '../../growth-sim-data/local/tsuburi_farmfieldNo3.2020/common_info.json'
    gpc = GsmPlantCoverage()
    with open(common_info, mode='r') as f:
        data = json.load(f)
        gpc.setCoverageParams(data['schedule']['crop_growth'])
