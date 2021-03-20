import os
import sys
import argparse
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import re
import datetime as dt
import csv
import matplotlib as mpl

mpl.rcParams['font.family'] = 'Hiragino Maru Gothic Pro'

parser = argparse.ArgumentParser()

parser.add_argument('-d', '--database', default='./sampledat/gsm_db.csv',
                    help='path of input database')
parser.add_argument('-dr', '--draw', nargs='+',
                    required = True)

parser.add_argument('-s', '--startdate')
parser.add_argument('-o', '--output')
parser.add_argument('-l', '--label')

args = parser.parse_args()

def set_label(sublist, labels, label_list):

    for row in sublist:
        if row in label_list:
            labels.append(label_list[row])
        else:
            lebels.append(row)

def gsm_draw(export_path, label_path):
    print(args.draw)

    df_org = pd.read_csv(args.database, parse_dates=True, index_col='Date')

    if args.startdate:
        sdate = dt.datetime.strptime(args.startdate,'%Y-%m-%d').date()
        df = df_org[sdate:]
    else:
        df = df_org

    drawLists=[]
    sublist = []

    for draw in args.draw:
        if re.match('and', draw):
            drawLists.append(sublist)
            sublist = []
        else:
            sublist.append(draw)

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
        df.plot(ax=fs, y=sublist, alpha=0.5, label=labels)
        fs.grid()


    if export_path is not None:
        dbname = os.path.basename(args.database)
        figure.savefig(export_path)
    else:
        plt.show()

def _main():
    if os.path.isfile(args.database) == False :
        print("ERROR: no input database")
        sys.exit(1)

    gsm_draw(args.output, args.label)

if __name__ == '__main__':
    _main()
