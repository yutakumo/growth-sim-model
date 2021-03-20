#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
from datetime import datetime

from .microclimate.fieldmodel import FieldModel
from .microclimate.solarradiationmodel import SolarRadiationModel
from .microclimate.physicaltools import PhysicalTools
from .gsm_base import GsmBase

class GsmMicroClimate(GsmBase,FieldModel, PhysicalTools, SolarRadiationModel):
    
    eWDPcmMin = .5
    
    def __init__(self):
        super(GsmMicroClimate, self).__init__()
        self.Items = {'eWCPkg' : 0, 'eWDPcm' : 0, 'eVWCkg' : 0, 'eTMPW' : 0, 'eTMPS' : 0,
                      'STATUS' : 0, 'NR' : 0, 'SEF' : 0, 'COF_BT' : 0, 'COF_ER' : 0,
                      'WLHW' : 0, 'WLHA' : 0, 'WLHS' : 0, 'WSVP' : 0, 'TMPSdp' : 0,
                      'TMPAnight' : 0, 'SHMD' : 0, 'LHFLXpaddy' : 0, 'EVApaddy' : 0, 'EVAsoil' : 0, 'TPAcrop' : 0, 'EVPG' : 0,
                      'WFLXdown' : 0, 'WFLXair' : 0, 'WFLXsoil' : 0, 'LHFLX' : 0, 'RHFLX' : 0,
                      'HFLX2W' : 0, 'HFLX2S' : 0, 'HFLXR' : 0, 'HFLXR2W' : 0, 'HFLXR2S' : 0, 'HFLXWin' : 0,
                      'HFLXWout' : 0, 'HFLXWdown' : 0, 'HFLXSdown' : 0, 'HFLXSWdown' : 0,
                      'HFLXExAW' : 0, 'HFLXExWS' : 0, 'HFLXExSA' : 0, 'HFLXExSS' : 0
                      }

    def calculate(self):
        self.solve_timeEvolutionWaterContentSoil()
        self.solve_timeEvolutionWaterContentAir()
        self.solve_timeEvolutionStatus()
        self.solve_timeEvolutionTemperatureAirAndSoil()

        self.calc_netRadiation()
        self.calc_sunElevationFactor()
        self.calc_soilDepthTemperature()
        self.calc_midnightTimeAirTemperature()
        self.calc_evaporationFactors()
        self.calc_waterLatentHeat()
        self.calc_waterSaturationVaporPressure()
        self.calc_specificHumidity()
        self.calc_paddyLatentHeatFlux()
        self.calc_evaporationAmountPaddy()
        self.calc_cropTranspirationAmount()
        self.calc_groundEvapolativePower()
        self.calc_evaporationAmountSoil()
        self.calc_waterFluxDown()
        self.calc_waterFlux()

        self.calc_totalLatentHeatFlux()
        self.calc_remainingHeatFlux()
        self.calc_remainingHeatFluxDistribution()
        self.calc_rainfallHeatFlux()
        self.calc_heatFluxeDependOnTemperature()

        self.update_timebase_db()
        self.count_up_time()

    def set_param(self, _params:dict):
        self._initializeObtainVariables(_params)

    def initialize(self):
        self._initializeIntermediateVariables()

    def _initializeObtainVariables(self, _initialValues:dict):
        self.Items = {'eTMPW' : 293.15,
                      'eTMPS' : 293.15,
                      'eWDPcm' : .0,
                      'eVWCkg' : self.getMaxVolumeWaterContentKg()
                      }
        if 'waterTemperature' in _initialValues.keys():
            self.Items['eTMPW'] = _initialValues['waterTemperature']
        if 'soilTemperature' in _initialValues.keys():
            self.Items['eTMPS'] = _initialValues['soilTemperature']
        if 'waterDepthcm' in _initialValues.keys():
            self.Items['eWDPcm'] = _initialValues['waterDepthcm']
        if 'volumeWaterContent' in _initialValues.keys():
            self.Items['eVWCkg'] = _initialValues['volumeWaterContent']
        self.solve_timeEvolutionStatus()
        self.Items['eWCPkg'] = self._convertWDPcmWCPkg(_WDPcm=self.Items['eWDPcm'])

    def _initializeIntermediateVariables(self):
        self.calc_netRadiation()
        self.calc_sunElevationFactor()
        self.calc_soilDepthTemperature()
        self.calc_midnightTimeAirTemperature(True)
        self.calc_evaporationFactors()
        self.calc_waterLatentHeat()
        self.calc_waterSaturationVaporPressure()
        self.calc_specificHumidity()
        self.calc_paddyLatentHeatFlux()
        self.calc_evaporationAmountPaddy()
        self.calc_cropTranspirationAmount()
        self.calc_groundEvapolativePower()
        self.calc_evaporationAmountSoil()
        self.calc_waterFluxDown()
        self.calc_waterFlux(True)

        self.calc_totalLatentHeatFlux()
        self.calc_remainingHeatFlux()
        self.calc_remainingHeatFluxDistribution()
        self.calc_rainfallHeatFlux()
        self.calc_heatFluxeDependOnTemperature(True)
    
    def _convertWDPcmWCPkg(self, _WDPcm=None, _WCPkg=None):
        if _WCPkg == None:
            return _WDPcm / 1e2 * self.surfaceTVSAirXY() * self.waterDensity
        elif _WDPcm == None:
            return _WCPkg / self.waterDensity / self.surfaceTVSAirXY() * 1e2

    def _get_time_dat_HMD(self, _previous):
        return self.get_time_dat('Humidity', _previous) * 0.01

    def _get_time_dat_RFLkg(self, _previous):
        return self.get_time_dat('Rainfall', _previous)

    def _get_time_dat_TMPA(self, _previous):
        return self.celsius2kelvin(self.get_time_dat('AirTemperature', _previous))

    def _get_time_dat_SPDW(self, _previou):
        return self.get_time_dat('Wind', _previou)

    def _get_time_dat_SLR(self, _previous):
        return self.get_time_dat('SolarRadiation', _previous)

    def _get_time_str(self):
        return datetime.strftime(self.get_time(), '%Y%m%d%H%M')

    def _get_date_str(self):
        return datetime.strftime(self.get_time(), '%Y%m%d')
    
    def calc_netRadiation(self):
        self.Items['NR'] = self.getNetRadiationCoefficient() * self._get_time_dat_SLR(False) * 1e6

    def calc_sunElevationFactor(self):
        self.Items['SEF'] = self.calcSunElevationFactor(self.fieldPosition[0], self.fieldPosition[1], self._get_time_str())

    def calc_soilDepthTemperature(self):
        self.Items['TMPSdp'] = self.soilDeepPartTemperatureModel(_date=self._get_date_str(), _tmpCenter=self.getSoilDeepPartBaseTemperature(), _tmpWidth=self.getSoilDeepPartTemperatureAmplitude())

    def calc_midnightTimeAirTemperature(self, _initialize=False):
        if _initialize:
            self.Items['TMPAnight'] = self._get_time_dat_TMPA(False)
        else:
            self.Items['TMPAnight'] = self._get_time_dat_TMPA(False) if self.get_time().hour == 0 else self.get_time_dat('TMPAnight', True)

    def calc_evaporationFactors(self):
        self.Items['COF_BT'] = self.coeffBulkTrans(self.get_time_dat('PCR', False))
        self.Items['COF_ER'] = self.evaporationRate(self.get_time_dat('PCR', False))

    def calc_waterLatentHeat(self):
        self.Items['WLHW'] = self.waterLatentHeat(self.Items['eTMPW'])
        self.Items['WLHA'] = self.waterLatentHeat(self._get_time_dat_TMPA(False))
        self.Items['WLHS'] = self.waterLatentHeat(self.Items['eTMPS'])

    def calc_waterSaturationVaporPressure(self):
        self.Items['WSVP'] = self.saturationVaporPressure(_tmp=self.Items['eTMPW'])

    def calc_specificHumidity(self):
        self.Items['SHMD'] = self.specificHumidity(_pv=self._get_time_dat_HMD(False) * self.saturationVaporPressure(_tmp=self._get_time_dat_TMPA(False)))

    def calc_paddyLatentHeatFlux(self):
        ## LHFLXpaddy: latent heat flux from paddy J/m^2
        rhoa = self.airDensity(self._get_time_dat_TMPA(False))
        specificHumidityDifference = self.specificHumidity(_pv=self.Items['WSVP'])  - self.Items['SHMD']
        self.Items['LHFLXpaddy'] = self.Items['COF_BT'] * self.Items['WLHW'] * rhoa * self._get_time_dat_SPDW(False) * specificHumidityDifference * 3.6e3

    def calc_evaporationAmountPaddy(self):
        ## EVApaddy:  evaporation amount from paddy kg/m^2
        self.Items['EVApaddy'] = self.Items['LHFLXpaddy'] /  self.Items['WLHW']

    def calc_cropTranspirationAmount(self):
        self.Items['TPAcrop'] = self.Items['COF_ER'] * 9e-4 * (1 + max(0, self._get_time_dat_TMPA(False) - self.Items['TMPAnight']))

    def calc_groundEvapolativePower(self):
        ## kg/m^2
        self.Items['EVPG'] = self.Items['NR'] / self.waterLatentHeat(self._get_time_dat_TMPA(False))
    
    def calc_evaporationAmountSoil(self):
        self.Items['EVAsoil'] = self.Items['EVPG'] * self.getGroundEvaporativeDropCoefficient(self.Items['eVWCkg'])
    
    def calc_waterFluxDown(self):
        ## kg/h/TVS
        if self.getTVSdownstreamWaterFluxMin() < self.Items['eVWCkg'] / (self.volumeTVSSol() * self.waterDensity):
            self.Items['WFLXdown'] = -self.getTVSdownstreamWaterFluxDh()
        else:
            self.Items['WFLXdown'] = .0

    def calc_waterFlux(self, _initialize=False):
        ## kg/h/TVS
        if _initialize:
            wflx_inlet = 0
            wflx_outlet = 0
        else:
            wflx_inlet = self.get_time_dat('WFLXinlet', False)
            if math.isnan(wflx_inlet):
                wflx_inlet = self.get_time_dat('eWFLXinlet', False)
            wflx_outlet = self.get_time_dat('WFLXoutlet', False)
            if math.isnan(wflx_outlet):
                wflx_outlet = -self.get_time_dat('eWFLXoutlet', False)
        
        if self.Items['STATUS'] == 'plow':
            self.Items['WFLXair'] = .0
            self.Items['WFLXsoil'] = -self.Items['EVAsoil'] - self.Items['TPAcrop'] + self.Items['WFLXdown'] + self._get_time_dat_RFLkg(False) + wflx_inlet + wflx_outlet
        elif self.Items['STATUS'] == 'paddy':
            self.Items['WFLXair'] = -self.Items['EVApaddy'] - self.Items['TPAcrop'] + self.Items['WFLXdown'] + self._get_time_dat_RFLkg(False) + wflx_inlet + wflx_outlet
            self.Items['WFLXsoil'] = .0

    def calc_totalLatentHeatFlux(self):
        ## J/m^2
        if self.Items['STATUS'] == 'plow':
            self.Items['LHFLX'] = self.Items['EVAsoil'] * self.Items['WLHS'] + self.Items['TPAcrop'] * self.Items['WLHA']
        elif self.Items['STATUS'] == 'paddy':
            self.Items['LHFLX'] = self.Items['LHFLXpaddy'] + self.Items['TPAcrop'] * self.Items['WLHA']

    def calc_remainingHeatFlux(self):
        ## J/h/TVS
        self.Items['RHFLX'] = self.Items['NR'] - self.Items['LHFLX']

    def calc_remainingHeatFluxDistribution(self):
        ## J/h/TVS
        if self.Items['STATUS'] == 'plow':
            self.Items['HFLX2W'] = 0.0
            self.Items['HFLX2S'] = self.Items['RHFLX'] * self.distributionSoilStorageRate(self.get_time_dat('PCR', False))
        elif self.Items['STATUS'] == 'paddy':
            self.Items['HFLX2W'] = self.Items['RHFLX'] * self.distributionWaterStorageRate(self.get_time_dat('PCR', False))
            self.Items['HFLX2S'] = 0.0

    def calc_rainfallHeatFlux(self):
        ## J/h/TVS
        self.Items['HFLXR'] = self._get_time_dat_RFLkg(False) * self.waterSpecificHeat * self.getRainfallTemperature()
        if self.Items['STATUS'] == 'plow':
            self.Items['HFLXR2W'] = .0
            self.Items['HFLXR2S'] = self._get_time_dat_RFLkg(False) * self.waterSpecificHeat * self.getRainfallTemperature()
        elif self.Items['STATUS'] == 'paddy':
            self.Items['HFLXR2W'] = self._get_time_dat_RFLkg(False) * self.waterSpecificHeat * self.getRainfallTemperature()
            self.Items['HFLXR2S'] = .0

    def calc_heatFluxeDependOnTemperature(self, _initialize=False):
        if _initialize:
            wflx_inlet = 0
            wflx_outlet = 0
            dtAW = self._get_time_dat_TMPA(False) - self.Items['eTMPW']
            dtSA = self.Items['eTMPS'] - self._get_time_dat_TMPA(False)
            dtSS = self.Items['TMPSdp'] - self.Items['eTMPS']
            dtWS = self.Items['eTMPW'] - self.Items['eTMPS']
        else:
            wflx_inlet = self.get_time_dat('WFLXinlet', False)
            if math.isnan(wflx_inlet):
                wflx_inlet = self.get_time_dat('eWFLXinlet', False)
            wflx_outlet = self.get_time_dat('WFLXoutlet', False)
            if math.isnan(wflx_outlet):
                wflx_outlet = self.get_time_dat('eWFLXoutlet', False)
            dtAW = (self._get_time_dat_TMPA(True) + self._get_time_dat_TMPA(False) - self.get_time_dat('eTMPW', True) - self.Items['eTMPW']) * .5 ##add nbumerical viscosity
            dtSA = self.Items['eTMPS'] - self._get_time_dat_TMPA(False)
            dtSS = self.Items['TMPSdp'] - self.Items['eTMPS']
            dtWS = self.Items['eTMPW'] - self.Items['eTMPS']
        
        if self.Items['STATUS'] == 'plow':
            _tmp_win = self._get_time_dat_TMPA(False)
        elif self.Items['STATUS'] == 'paddy':
            _tmp_win = self.get_time_dat('TMPWin', False)
            if math.isnan(_tmp_win):
                _tmp_win = self.get_time_dat('eTMPWin', False)

        self.Items['HFLXWin'] = wflx_inlet * _tmp_win * self.waterSpecificHeat
        self.Items['HFLXWout'] = wflx_outlet * self.Items['eTMPW'] * self.waterSpecificHeat
        self.Items['HFLXWdown'] = self.Items['WFLXdown'] * self.Items['eTMPW'] * self.waterSpecificHeat
        self.Items['HFLXSdown'] = self.Items['WFLXdown'] * self.Items['eTMPS'] * self.waterSpecificHeat
        self.Items['HFLXSWdown'] = self.Items['WFLXdown'] * (self.Items['eTMPS'] - self.Items['eTMPW']) * self.waterSpecificHeat

        self.Items['HFLXExAW'] = self.htcAW(dtAW) * dtAW
        self.Items['HFLXExWS'] = self.htcWS(dtWS) * dtWS
        self.Items['HFLXExSA'] = self.htcSA(dtSA) * dtSA
        self.Items['HFLXExSS'] = dtSS * self.getHeatConvectionConstantSS()

    def solve_timeEvolutionWaterContentSoil(self):
        ## paddy water content change inside soil
        self.Items['eVWCkg'] = self.get_time_dat('eVWCkg', True) + self.get_time_dat('WFLXsoil', True)

    def solve_timeEvolutionWaterContentAir(self):
        self.Items['eWCPkg'] = self.get_time_dat('eWCPkg', True) + self.get_time_dat('WFLXair', True)
        if self.Items['eWCPkg'] <= self._convertWDPcmWCPkg(_WDPcm=self.eWDPcmMin):
            self.Items['eWCPkg'] = self._convertWDPcmWCPkg(_WDPcm=self.eWDPcmMin)
        self.Items['eWDPcm'] = self._convertWDPcmWCPkg(_WCPkg=self.Items['eWCPkg'])

    def solve_timeEvolutionStatus(self):
        if self.Items['eVWCkg'] < self.getMaxVolumeWaterContentKg():
            self.Items['STATUS'] = 'plow' #plow
        else:
            self.Items['STATUS'] = 'paddy' #paddy

    def solve_timeEvolutionTemperatureAirAndSoil(self):
        ## water and soil temperature
        if self.Items['STATUS'] == 'plow':
            termA = self.heatCapacityTVSSol() + self.waterSpecificHeat * self.get_time_dat('eVWCkg', True)
            termB = (-self.waterSpecificHeat * self.get_time_dat('eTMPS', True) * (self.Items['eVWCkg'] - self.get_time_dat('eVWCkg', True))
                     + self.get_time_dat('HFLX2S', True)
                     + self.get_time_dat('HFLXR2S', True)
                     + self.get_time_dat('HFLXSdown', True)
                     - (self.get_time_dat('EVAsoil', True) + self.get_time_dat('TPAcrop', True)) * self.waterSpecificHeat * self.get_time_dat('eTMPS', True)
                     - self.get_time_dat('HFLXExSA', True)
                     + self.get_time_dat('HFLXExSS', True)
                     )
            print(termA, termB)
            dts = termB / termA
            self.Items['eTMPW'] = self._get_time_dat_TMPA(True)
            self.Items['eTMPS'] = self.get_time_dat('eTMPS', True) + dts
        elif self.Items['STATUS'] == 'paddy':
            termA = self.waterSpecificHeat * self.get_time_dat('eWCPkg', True)
            termB = (- self.waterSpecificHeat * self.get_time_dat('eTMPW', True) * (self.Items['eWCPkg'] - self.get_time_dat('eWCPkg', True))
                     + self.get_time_dat('HFLX2W', True)
                     + self.get_time_dat('HFLXWin', True)
                     + self.get_time_dat('HFLXWout', True)
                     - self.get_time_dat('eTMPW', True) * self.waterSpecificHeat * (self.get_time_dat('EVApaddy', True) + self.get_time_dat('TPAcrop', True))
                     + self.get_time_dat('HFLXWdown', True)
                     + self.get_time_dat('HFLXR2W', True)
                     + self.get_time_dat('HFLXExAW', True)
                     - self.get_time_dat('HFLXExWS', True)
                     )
            dtw = 5 * (termB / termA) / abs(termB / termA) if 5 < abs(termB / termA) else termB / termA
            termC = self.heatCapacityTVSSol() + self.waterSpecificHeat * self.get_time_dat('eVWCkg', True)
            termD = self.get_time_dat('HFLX2S', True) - self.get_time_dat('HFLXSWdown', True) + self.get_time_dat('HFLXExWS', True) + self.get_time_dat('HFLXExSS', True)
            dts = termD / termC
            self.Items['eTMPW'] = self.get_time_dat('eTMPW', True) + dtw
            self.Items['eTMPS'] = self.get_time_dat('eTMPS', True) + dts

if __name__ == '__main__':
    import json
    common_info = '../../growth-sim-data/local/tsuburi_farmfieldNo3.2020/common_info.json'
    gmc = GsmMicroClimate()
    with open(common_info, mode='r') as f:
        data = json.load(f)
        gmc.setGlobalConstant(data['microclimate']['globalConstant'])
        gmc.setLocalConstant(data['microclimate']['localConstant'])
        gmc.setFieldPosition(data['field']['position'])
