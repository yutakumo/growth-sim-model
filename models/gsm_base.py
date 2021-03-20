#import abc
import datetime
import pandas as pd
import numpy as np

class GsmBase:
    def __init__(self):
        self.Items = {}
        self.CoeffDB = None
        self.YesterdayDB = None
        self.YesterdayDT = None
        self.TodayDB = None
        self.TodayDT = None

        self.TimeBaseDB = None
        self.TimeBaseDT = None
        self.idx_time = 0

    def set_coeff_db(self, database):
        self.CoeffDB = database

    def get_coeff(self, keyword):
        return self.CoeffDB[keyword].iloc[0]

    '''
    def set_yesterday_db(self, _database):
        self.YesterdayDB = _database

    def set_today_db(self, _database):
        self.TodayDB = _database

    def update_daybase_db(self):
        for k in self.Items.keys():
            self.TodayDB[k][self.TodayDT] = self.Items[k]
    '''

    def set_timebase_db(self, _database, _datetime):
        self.TimeBaseDB = _database
        self.TimeBaseDT = _datetime
        self.idx_time = 1

    def update_timebase_db(self):
        #print('Update TimeBaseDB')
        for k in self.Items.keys():
            _datetime = self.TimeBaseDT[self.idx_time]
            #print(k, self.Items[k], self.TimeBaseDB[k][_datetime])
            self.TimeBaseDB[k][_datetime] = self.Items[k]

    def carry_previous_db(self):
        for k in self.Items.keys():
            self.Items[k] = self.TimeBaseDB[k][self.TimeBaseDT[self.idx_time-1]]

    def get_day_dat(self, keyword):
        _nlist = np.array(list(self.TimeBaseDB[keyword].values())[1:25])
        _nlist = _nlist[~np.isnan(_nlist)]
        return _nlist.sum()

    def count_up_time(self):
        self.idx_time += 1

    def get_time_dat(self, keyword, previous=False):
        if previous :
            _idx = self.idx_time-1
        else:
            _idx = self.idx_time

        _datetime = self.TimeBaseDT[_idx]
        return self.TimeBaseDB[keyword][_datetime]

    def get_time(self):
        return self.TimeBaseDT[self.idx_time]

    ###
    def check_key(self, _key):
        return _key in self.TimeBaseDB

    def check_sunset(self):
        _p_solar_radiation = self.get_time_dat('SolarRadiation', True)
        _solar_radiation = self.get_time_dat('SolarRadiation')
        return _p_solar_radiation > 0 and _solar_radiation == 0

    def check_sunrise(self):
        _p_solar_radiation = self.get_time_dat('SolarRadiation', True)
        _solar_radiation = self.get_time_dat('SolarRadiation')
        return _p_solar_radiation == 0 and _solar_radiation > 0

    ###
    def initialize(self):
        pass

    def initialize_values(self, _database, _datetime):
        self.TimeBaseDB = _database
        self.TimeBaseDT = _datetime
        self.idx_time = 0

        self.initialize()
        self.update_timebase_db()

class GsmDriveBase:
    def create_initdb(self, runList, sdate, edate):

        _items = {}
        for model in runList:
            _items.update(model.Items)

        _idf = pd.DataFrame(_items.values(), index=_items.keys()).T

        _sdate = datetime.datetime.strptime(sdate,'%Y-%m-%d')
        _edate = datetime.datetime.strptime(edate,'%Y-%m-%d').date()

        _idf['Date'] = _sdate - datetime.timedelta(hours=1)
        idf = _idf.set_index('Date')
        idf.loc[:] = np.nan
        simdays = (_edate - _sdate.date()).days

        key = list(_items.keys())[0]
        ddf = pd.DataFrame([[np.nan]], index=[_sdate + datetime.timedelta(hours=i) for i in range((simdays+1)*24)], columns=[key])
        ddf.index.name = 'Date'

        idf = pd.concat([idf, ddf], sort=True)

        return idf

    def simulate(self, n_sim, df, dfc, runList, custom_func):

        ind = df[0:1]
        indd = ind.to_dict()
        [runList[i].initialize_values(indd, ind.index) for i in range(len(runList))]
        idn = pd.DataFrame(indd)
        df.update(idn)

        for i in range(1, n_sim, 24): # days
            t_day = df.index[i]
            y_day = t_day - datetime.timedelta(hours=1)
            tc = dfc

            print(y_day.date(), t_day.date())

            custom_func(y_day, t_day, i)

            yd = df[i-1:i+24]
            ydd = yd.to_dict()

            for i in range(len(self.runList)):
                runList[i].set_timebase_db(ydd, yd.index)
                runList[i].set_coeff_db(tc)

            n_hours = yd.index.size
            for h in range(n_hours-1): ## hours
                [runList[i].calculate() for i in range(len(runList))]

            ydn = pd.DataFrame(ydd)
            df.update(ydn)
