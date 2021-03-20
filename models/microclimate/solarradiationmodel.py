#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

from .sun import getSunDirection, getSunriseAndSunsetTime


class SolarRadiationModel:
    def calcSunElevationFactor(self, _lat='deg', _lon='deg', _datetime='yyyymmddhhmm'):
        """
        calc sun solid anngle
        """
        sunElevation = getSunDirection(_lat=_lat, _lon=_lon, _month=int(_datetime[4:6]), _day=int(_datetime[6:8]), _hour=int(_datetime[8:10]), _min=int(_datetime[10:12]), _sec=0)[1]
        solidAng = sunElevation if 0 < sunElevation else .0
        return np.sin(solidAng)
    
    def calcSunriseAndSunsetTime(self, _lat='deg', _lon='deg', _datetime='yyyymmdd'):
        return getSunriseAndSunsetTime(_lat=_lat, _lon=_lon, _month=int(_datetime[4:6]), _day=int(_datetime[6:8]))
    
