import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta

def insertAverageWeatherData(sim_db, weather_db):


    #del_years = datetime.date.today().year-weather_db.index[0].year
    del_years = sim_db.index[0].year-weather_db.index[0].year
    weather_db.index = [ index + relativedelta(years=+del_years) for index in weather_db.index]

    sim_db.update(weather_db)

    weather_db.rename(columns={
        'DaytimeTemperature':'AveDaytimeTemperature',
        'NighttimeTemperature':'AveNighttimeTemperature',
        'SolarRadiation': 'AveSolarRadiation'
    }, inplace=True)

    sim_db.update(weather_db)

def _main():
    import os
    import sys
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--database', required=True,
                        help='path of input database')
    parser.add_argument('-o', '--output', required=True,
                        help='path of output database')
    parser.add_argument('-w', '--weatherdb', required=True,
                        help='path of weather information database')

    args = parser.parse_args()

    if os.path.isfile(args.database) == False :
        print("ERROR: no input database")
        sys.exit(1)
    else:
        df = pd.read_csv(args.database, parse_dates=True, index_col='Date')

    if os.path.isfile(args.weatherdb) == False :
        print("ERROR: no weather information database")
        sys.exit(1)
    else:
        dw = pd.read_csv(args.weatherdb, parse_dates=True, index_col='Date', comment='#')

    insertAverageWeatherData(df, dw)

    df.to_csv(args.output)

    sys.exit(0)

if __name__ == '__main__':
    _main()
