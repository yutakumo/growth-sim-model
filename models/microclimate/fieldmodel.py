#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .fieldvolumesystem import FieldVolumeSystem

class FieldModel(FieldVolumeSystem):
    
    def __init__(self):
        self.globalConstant = {}
        self.localConstant = {}
    
    def setGlobalConstant(self, _dict):
        self.globalConstant = _dict
        self.updateSoilParameters()
    
    def setLocalConstant(self, _dict):
        self.localConstant = _dict
    
    def updateSoilParameters(self):
        if 'soilDensity' in self.globalConstant.keys(): self.setSoilDensity(self.globalConstant['soilDensity'])
        if 'soilSpecificHeat' in self.globalConstant.keys(): self.setSoilSpecificHeat(self.globalConstant['soilSpecificHeat'])
    
    def getNetRadiationCoefficient(self):
         ## Rn(net radiation) ~ coeffNR * St(global solar radiation)
        return self.globalConstant['netRadiation']
    
    def getEvaporativeDropCoefficient(self):
         ## experimental coefficient for crossing point between evaporative power and evaporative amount
        return self.globalConstant['evaporativeDrop']
    
    def getSoilMaxVolumeWaterConteneRate(self):
         ## %/100
        return self.globalConstant['soilMaxVolumeWaterContentRate']
    
    def getDistributionWaterStorage(self):
         ## coeff heat flux distribution to water storage
        return self.globalConstant['distributionWaterStorage']
    
    def getDistributionSoilStorage(self):
         ## coeff heat flux distribution to soil storage
        return self.globalConstant['distributionSoilStorage']
    
    def getRainfallTemperature(self):
         ## K
        return self.globalConstant['rainfallTemperature']
    
    def getHTCAWbase(self):
         ## J/h/K/m^2 heat transfer coefficient between air and water
        return self.globalConstant['htcAW']
    
    def getHTCWSbase(self):
         ## J/h/K/m^2 heat transfer coefficient between water and soil
        return self.globalConstant['htcWS']
    
    def getHTCSAbase(self):
         ## J/h/K/m^2 heat transfer coefficient between water and soil
        return self.globalConstant['htcSA']
    
    def getHTCAWtemperatureCor(self):
         ## K specified period for heat transfer coefficient between air and water
        return self.globalConstant['tAW']
    
    def getHTCWStemperatureCor(self):
         ## K specified period for heat transfer coefficient between water and soil
        return self.globalConstant['tWS']
    
    def getHTCSAtemperatureCor(self):
         ## K specified period for heat transfer coefficient between soil and air
        return self.globalConstant['tSA']
    
    def getHeatConvectionConstantSS(self):
         ## J/h/K heat convection coefficient between TVS and soil deep part
        return self.globalConstant['lambdaSS']
    
    def getSoilDeepPartBaseTemperature(self):
         ## K soil deep part base temperature
        return self.globalConstant['depthTmps']
    
    def getSoilDeepPartTemperatureAmplitude(self):
         ## K soil deep part year difference
        return self.globalConstant['depthTmpsDelta']
    
    def getTVSdownstreamWaterFluxDh(self):
        ## kg/h/TVS
        return self.localConstant['downstreamWaterFluxDh']

    def getTVSdownstreamWaterFluxMin(self):
        ##kg/TVS
        return self.localConstant['downstreamWaterFluxMin']

    def getMaxVWCkgCapacity(self):
        return self.localConstant['maxVWCCapacity'] * self.waterDensity * self.lngzSol

    def getMinVWCkgCapacity(self):
        return self.localConstant['minVWCCapacity'] * self.waterDensity * self.lngzSol

    def evaporationRate(self, _plantCoverageRatio='0 ~ 1'):
        return self.localConstant['cropDensityCoeff'] * _plantCoverageRatio**1.5
    
    def coeffBulkTrans(self, _plantCoverageRatio='0 ~ 1'):
        return self.localConstant['bulkCoeff'] * (1 - _plantCoverageRatio**1.5)
    
    def distributionWaterStorageRate(self, _plantCoverageRatio='0 ~ 1'):
        return self.getDistributionWaterStorage() * (1 - _plantCoverageRatio)
    
    def distributionSoilStorageRate(self, _plantCoverageRatio='0 ~ 1'):
        return self.getDistributionSoilStorage()* (1 - _plantCoverageRatio)
    
    def htcAW(self, _dt='K'):
        ## J/h/K/m^2 heat transfer coefficient between air and water
        resulut = self.getHTCAWbase() if self.getHTCAWtemperatureCor() <= abs(_dt) else self.getHTCAWbase() * (_dt / self.getHTCAWtemperatureCor()) ** 2
        return resulut
    
    def htcWS(self, _dt='K'):
        ## J/h/K/m^2 heat transfer coefficient between water and soil
        resulut = self.getHTCWSbase() if self.getHTCWStemperatureCor() <= abs(_dt) else self.getHTCWSbase() * (_dt / self.getHTCWStemperatureCor()) ** 2
        return resulut

    def htcSA(self, _dt='K'):
        ## J/h/K/m^2 heat transfer coefficient between air and soil
        result = self.getHTCSAbase() if self.getHTCSAtemperatureCor() <= abs(_dt) else self.getHTCSAbase() * (_dt / self.getHTCSAtemperatureCor()) ** 2
        return result
    
    def minimumWindSpeed(self):
        return .1
    
    def getMaxVolumeWaterContentKg(self):
        return self.getSoilMaxVolumeWaterConteneRate() * self.volumeTVSSol() * self.waterDensity
    
    def getGroundEvaporativeDropCoefficient(self, _vwckg='kg'):
        if _vwckg - self.getMinVWCkgCapacity() <= 0:
            return .0
        else:
            return (_vwckg - self.getMinVWCkgCapacity()) / (self.getEvaporativeDropCoefficient() * (self.getMaxVWCkgCapacity() - self.getMinVWCkgCapacity()))