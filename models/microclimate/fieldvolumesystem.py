#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import date
import numpy as np

class AirModel:
    airSpecificHeat = 1.006e3 ##J/kg K
    def airDensity(self, _tmp='K'):
        return 0.1/30 * _tmp +  .2395 ##kg/m^3
    
class WaterModel:
    waterDensity = 1.0e3 ##kg/m^3
    waterSpecificHeat = 4.19e3 ##J/kg K
    def waterLatentHeat(self, _tmp='K'):
        return -2.373e3 * _tmp + 3.1491e6 ##J/kg
    
    def saturationVaporPressure(self, _tmp='K'):
        return 610.78 * 10 ** (7.5 * (_tmp - 273.15) / (_tmp - 35.85)) ## August equation

class SoilModel:
    soilDensity = 1.6e3 ##kg/m^3
    soilSpecificHeat = 2.5e3 ##J/kg K
    coeffWaterContent = 1. ##VWC at 150mmdepth -> average VWC inside 500mmdepth
    
    def soilDeepPartTemperatureModel(self, _date='yyyymmdd', _tmpCenter='K', _tmpWidth='K'):
        numOfDate = (date(year=int(_date[:4]), month=int(_date[4:6]), day=int(_date[6:])) - date(year=int(_date[:4]), month=7, day=1)).days
        return _tmpCenter + _tmpWidth * np.sin(numOfDate / 365 * np.pi)
    
    def setSoilDensity(self, _density):
        self.soilDensity = _density ##kg/m^3
    
    def setSoilSpecificHeat(self, _specificHeat):
        self.soilSpecificHeat = _specificHeat ##J/kg K

    def getNitorogenContent(self):
        return 0

class FieldVolumeSystem(AirModel, WaterModel, SoilModel):
    lngxAir = 1.  ##m
    lngyAir = 1.  ##m
    lngzAir = 1.5 ##m
    lngxSol = 1.  ##m
    lngySol = 1.  ##m
    lngzSol = .5  ##m
    
    def surfaceTVSAirXY(self):
        return self.lngxAir * self.lngyAir ##m^2
    
    def volumeTVSAir(self):
        return self.lngxAir * self.lngyAir * self.lngzAir ##m^3

    def volumeTVSSol(self):
        return self.lngxSol * self.lngySol * self.lngzSol ##m^3
    
    def massTVSSol(self):
        return self.soilDensity * self.volumeTVSSol() ##kg
    
    def heatCapacityTVSSol(self):
        return self.massTVSSol() * self.soilSpecificHeat ##J/K
