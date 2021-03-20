#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

class PhysicalTools:

    def __init__(self):
        self.bcMethod = {}
        self.fieldPosition = ()

    def setBcMethod(self, _dict):
        self.bcMethod = _dict
    
    def setFieldPosition(self, _dict):
        self.fieldPosition = (_dict['lat'], _dict['lon'])
        
    def celsius2kelvin(self, _degc):
        return _degc + 273.15
    
    def kelvin2celsius(self, _kelvin):
        return _kelvin - 273.15

    def celsiuss2kelvins(self, _celsiuss:list):
        return np.array([self.celsius2kelvin(val) for val in _celsiuss])

    def kelvins2celsiuss(self, _kelvins:list):
        return np.array([self.kelvin2celsius(val) for val in _kelvins])
    
    def specificHumidity(self, _pv='vapor pressure Pa', _pa=1.013e5):
        return 0.622 * _pv / (_pa - 0.378 * _pv)

    def mm2cm(self, _mm):
        return _mm * 0.1

    def cm2mm(self, _cm):
        return _cm * 10