import datetime as dt
import json
import pandas as pd

def make_ideal_gindex(sdate, edate, bdat):

    _period = int(bdat.tail(1)['ElapsedDays'])
    bperiod = int((edate-sdate).days)
    rate = bperiod/_period
    bdat['Date'] = sdate
    for index, item in bdat.iterrows():
        bdat.loc[index,'Date'] = item['Date'] + dt.timedelta(days=int(round(item['ElapsedDays'] * rate)))

    idat = bdat.drop('ElapsedDays', axis=1)
    ibat_d = idat.set_index('Date')
    return ibat_d

def _main():
    import os
    import sys
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('-ci', '--commoninfo', required = True)
    parser.add_argument('-bd', '--basedat', required = True)
    parser.add_argument('-s', '--startdate')
    parser.add_argument('-e', '--enddate')
    args = parser.parse_args()

    basedat = args.basedat
    commoninfo = args.commoninfo

    if os.path.isfile(basedat) == False :
        print("ERROR: no base data")
        sys.exit(1)
    else:
        bdat = pd.read_csv(basedat)

    if os.path.isfile(commoninfo) == False:
        print("ERROR: no common infomation")
    else:
        with open(commoninfo) as fjci:
            jci = json.load(fjci)
            fjci.close()

    if args.startdate:
        _start = args.startdate
    else:
        _plant_method = {'direct_sowing': 'sowing_date', 'transplantation': 'transplanting_date'}
        plant_method = _plant_method[jci['planting']['method']]
        _start = jci['schedule']['manure']['date']

    sdate = dt.datetime.strptime(_start,'%Y-%m-%d').date()

    if args.enddate:
        _end = args.enddate
    else:
        _end = jci['schedule']['reaping_date']['date']

    edate = dt.datetime.strptime(_end,'%Y-%m-%d').date()

    idat = make_ideal_gindex(sdate, edate, bdat)

    print(idat)

if __name__ == '__main__':
    _main()
