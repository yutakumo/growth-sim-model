#!/usr/bin/env python3
# coding: utf-8

import math

def getSunDirection(_lat, _lon, _month, _day, _hour, _min, _sec):
  # refer: http://k-ichikawa.blog.enjoy.jp/etc/HP/js/sunShineAngle/ssa.html
  #               1  2  3  4  5  6  7  8  9 10 11 12
  daytotal = [ 0,31,28,31,30,31,30,31,31,30,31,30,31 ]
  jd = 0
  for i in range(1, _month):
    jd = jd + daytotal[i]
  jd = jd + _day - 0.5
  wj = 2.0 * math.pi/365.0 * jd
  delta = 0.33281 - 22.984*math.cos(wj) - 0.34990*math.cos(2*wj) - 0.13980*math.cos(3*wj) + 3.7872*math.sin(wj) + 0.03250*math.sin(2*wj) + 0.07187*math.sin(3*wj)
  e = 0.0072*math.cos(wj) - 0.0528*math.cos(2*wj) - 0.0012*math.cos(3*wj) - 0.1229*math.sin(wj) - 0.1565*math.sin(2*wj) - 0.0041*math.sin(3*wj)
  t = (_hour + _min/60.0 + _sec/3600.0) + (_lon - 135)/15.0 + e
  phi = _lat * math.pi/180.0
  delt = delta * math.pi/180.0
  tt = (15*t - 180) * math.pi/180.0
  height = math.asin(math.sin(phi)*math.sin(delt) + math.cos(phi)*math.cos(delt)*math.cos(tt)); # sun height (rad)
  sinA = math.cos(delt)*math.sin(tt) / math.cos(height)
  cosA = (math.sin(height)*math.sin(phi) - math.sin(delt))/math.cos(height) / math.cos(phi)
  direct = math.atan2(sinA, cosA) + math.pi; # sun direction (rad)
  return (direct, height)

def getSunriseAndSunsetTime(_lat, _lon, _month, _day):
    """
    restriction: must has sunrise and sunset time a day(no midnight sun)
    return (sunriseTime(hour, min), sunsetTime(hour, min))
    """
    result = []
    previousHeight = -1
    residual = 1e-2
    for t in range(1, 24):
        #if not sunriseTime == None and not sunsetTime == None: break
        if len(result) == 2: break
        tDirection = getSunDirection(_lat=_lat, _lon=_lon, _month=_month, _day=_day, _hour=t, _min=0, _sec=0)
        if (previousHeight < 0 and 0 <= tDirection[1]) or (0 < previousHeight and tDirection[1] <= 0):
            smin = int(60 * abs(previousHeight / (previousHeight - tDirection[1])) - 1)
            for m in range(smin, smin + 10):
                tmDirection = getSunDirection(_lat=_lat, _lon=_lon, _month=_month, _day=_day, _hour=t - 1, _min=m, _sec=0)
                if abs(tmDirection[1]) < residual:
                    result.append((t - 1, m))
                    break
        previousHeight = tDirection[1]
    
    return result
