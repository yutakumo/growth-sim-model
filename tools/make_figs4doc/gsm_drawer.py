import os
import matplotlib
import matplotlib.pyplot as plt
import re
import datetime as dt
import csv
import matplotlib as mpl
import json

mpl.rcParams['font.family'] = 'Hiragino Maru Gothic Pro'

def set_label(sublist, labels, label_list):

    for row in sublist:
        if row in label_list:
            labels.append(label_list[row])
        else:
            lebels.append(row)

def get_marker(glist):
    if glist.startswith('T19'):
        return 'o'
    else:
        return ''

def gsm_draw(sdate, edate, database, draws, export_path, label_path):
    df_org = database

    if sdate is not None:
        _df = df_org[sdate:]
    else:
        _df = df_org

    if edate is not None:
        df = _df[:edate]
    else:
        df = _df

#    df = df.interpolate(method='spline', order=2)
    df = df.interpolate(method='time')

    drawLists=[]
    ylabels=[]
    with open(draws) as f:
        jd = json.load(f)
        for i in range(len(jd['figures'])):
            sublist = []
            ylabels.append(jd['figures'][i]['ylabel'])
            for j in range(len(jd['figures'][i]['dbkey'])):
                sublist.append(jd['figures'][i]['dbkey'][j])
            drawLists.append(sublist)

    figure = plt.figure(figsize=(16, 4 * len(drawLists)))

    label_list = {}
    if label_path is not None:
        with open(label_path, 'r') as f:
            reader = csv.reader(f)
            next(f)

            for row in reader:
                label_list[row[0]] = row[1]

    for i, sublist in enumerate(drawLists):
        fs = figure.add_subplot(len(drawLists), 1, drawLists.index(sublist)+1)
        fs.cla()
        labels = []
        set_label(sublist, labels, label_list)
        for j, dlist in enumerate(sublist):
            _marker = get_marker(dlist)
            df.plot(ax=fs, y=dlist, alpha=0.5, label=labels[j], linewidth = 3, marker='')
        plt.ylabel(ylabels[i])
        fs.grid()

    plt.tight_layout()
    figure.suptitle(jd['title'])
    plt.subplots_adjust(top=0.95)

    if export_path is not None:
        figure.savefig(export_path)
    else:
        plt.show()

def _main():
    import sys
    import argparse
    import pandas as pd

    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--database', default='./sampledat/gsm_db.csv',
                        help='path of input database')
    #parser.add_argument('-dr', '--draw', nargs='+',
    #                    required = True)

    parser.add_argument('-dr', '--draw', required = True)

    parser.add_argument('-s', '--startdate')
    parser.add_argument('-e', '--enddate')
    parser.add_argument('-o', '--output')
    parser.add_argument('-l', '--label')
    parser.add_argument('-fd', '--fielddir')
    parser.add_argument('-ci', '--commoninfo')

    args = parser.parse_args()

    if args.fielddir is not None:
        commoninfo = args.fielddir + '/common_info.json'
        result_db = args.fielddir + '/out_gsm_db.csv'
    else:
        result_db = args.database
        commoninfo = args.commoninfo

    if os.path.isfile(result_db) == False :
        print("ERROR: no input database")
        sys.exit(1)
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

    print(args.draw)

    database = pd.read_csv(result_db, parse_dates=True, index_col='Date')
    gsm_draw(sdate, edate, database, args.draw, args.output, args.label)

if __name__ == '__main__':
    _main()
