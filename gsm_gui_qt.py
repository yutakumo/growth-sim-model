import os
import sys
import argparse
import pandas as pd
import datetime
import math
import json
import csv
import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont

import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib as mpl

mpl.rcParams['font.family'] = 'Hiragino Maru Gothic Pro'

import gsm_simulator
import tools.update_db.insert_aveweather as ins_aw

parser = argparse.ArgumentParser()


parser.add_argument('-b', '--begin',
                    help='beginning date of simulator')
parser.add_argument('-f', '--finish',
                    help='finishing date of simulator')
parser.add_argument('-d', '--database', default='./sampledat/gsm_db.csv',
                    help='path of input database')
parser.add_argument('-iv', '--initvalues', default='./global/init_db.csv',
                    help='path of input initial database')
parser.add_argument('-o', '--output', default='./out.csv',
                    help='path of output database')
parser.add_argument('-c', '--coeff', default='./sampledat/coeff.csv',
                    help='path of coeffiecient database')
parser.add_argument('-cb', '--coeffcultivar', default='./sampledat/coeff_cultivar.csv',
                    help='path of cultivar specific coeffiecient database')
parser.add_argument('-id', '--idealdat', default='./sampledat/base_ideal_gindex.csv',
                    help='path of base ideal growth-index data')
parser.add_argument('-bw', '--baseweatherdb',
                    help='path of base weather information database')
parser.add_argument('-w', '--weatherdb',
                    help='path of weather information database')
parser.add_argument('-wfc', '--fcweatherdb',
                    help='path of weather forcast information database')
parser.add_argument('-aw', '--aveweatherdb', default='./sampledat/shirochi_summarize.csv',
                    help='path of average weather information database')
parser.add_argument('-fs', '--fieldsensor',
                    help='path of field sensor data')
parser.add_argument('-is', '--imsense', default='./sampledat/imsense.csv',
                    help='path of image sensing database')
parser.add_argument('-ci', '--commoninfo', default='./sampledat/common_info.json',
                    help='path of growth planning information file')
parser.add_argument('-wf', '--waterflux', default='./sampledat/wflux.csv',
                    help='path of water flux information file')
parser.add_argument('-hd', '--headingdate', choices=['fix', 'predict', 'simulate'], default='simulate',
                    help='select kind of heading date')

parser.add_argument('-gd', '--globaldir',
                    help='directory of global data')
parser.add_argument('-fd', '--fielddir',
                    help='directory of field data')
parser.add_argument('-wd', '--weatherdir',
                    help='directory of weather data')
parser.add_argument('-frtl', '--fertilizer',
                    help='path of fertilizer information file')

parser.add_argument('-gr', '--grab',
                    help='directory of grab file')

parser.add_argument('-nufs', '--nousefieldsensor', action='store_true')

parser.add_argument('-cmt', '--checkmtime', action='store_false',
                    help='check mtime of growth planning information file and database')

parser.add_argument('-dl','--drawlist', required=True)
parser.add_argument('-l', '--label', required=True)
parser.add_argument('-ds', '--displaysize', choices=['FHD', '4K'], default='4K')

args = parser.parse_args()

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self,
                 titleName,
                 jci, fert,
                 begin, finish,
                 initvalues, baseweatherdb, weatherdb, fcweatherdb,
                 fieldsensor, commoninfo, fertilizer, idealdat,
                 avewdb, imsense,
                 coeff, coeffcultivar, wflux, output,
                 headingdate, checkmtime,
                 labels,
                 drawLists,
                 displaysize):

        QtWidgets.QMainWindow.__init__(self)

        if displaysize == '4K':
            self._tfontsize = 24
            self._bfontsize = 18
            self._gfontsize = 5
        elif displaysize == 'FHD':
            self._tfontsize = 18
            self._bfontsize = 12
            self._gfontsize = 3

        self._font = 'Hiragino Maru Gothic Pro'

        self.begin = begin
        self.finish = finish
        self.initvalues = initvalues
        self.baseweatherdb = baseweatherdb
        self.weatherdb = weatherdb
        self.fcweatherdb = fcweatherdb
        self.fieldsensor = fieldsensor
        self.commoninfo = commoninfo
        self.wflux = wflux
        self.fertilizer = fertilizer
        self.idealdat = idealdat
        self.coeff = coeff
        self.coeffcultivar = coeffcultivar
        self.output = output
        self.headingdate = headingdate
        self.checkmtime = checkmtime
        self.drawLists = drawLists

        self.avewdb = avewdb
        self.ims = imsense

        self.fert = fert

        self.initUI(titleName,jci)

        self.read_label(labels)

        if self.begin is not None:
            self.sdate = datetime.datetime.strptime(self.begin,'%Y-%m-%d')
            self.sim_sdate = datetime.datetime.strptime(self.begin,'%Y-%m-%d')
        else:
            self.sdate = None

        if self.finish is not None:
            self.edate = datetime.datetime.strptime(self.finish,'%Y-%m-%d')
            self.sim_edate = datetime.datetime.strptime(self.finish,'%Y-%m-%d')
        else:
            self.edate = None

        self.gsim = gsm_simulator.gsm_simulator(
            begin, finish,
            avewdb, imsense,
            initvalues, idealdat, baseweatherdb, weatherdb, fcweatherdb,
            fieldsensor,
            commoninfo, fertilizer,
            coeff, coeffcultivar, wflux, output,
            headingdate, checkmtime)

        self.simulation()

    def initUI(self, titleName, jci):

        self.main_widget = QtWidgets.QWidget(self)
        self.l = QtWidgets.QHBoxLayout(self.main_widget)

        self.sim_bt = QtWidgets.QPushButton('SIMULATION')
        self.sim_bt.clicked.connect(self.simulation)
        self.sim_bt.setParent(self.main_widget)

        '''
        self.button = Tk.Button(self.frame, text='Save', command=self.save)
        self.button.grid(row=2, column=3)
        '''

        self.grid_l = QtWidgets.QGridLayout()
        self.grid_l.setSpacing(2)

        self.simver_label = QtWidgets.QLabel('Sim-Version:')
        self.simver_ver = QtWidgets.QLabel()
        self.simtime_label = QtWidgets.QLabel('Sim-Date:')
        self.simtime_entry = QtWidgets.QLabel()

        self.simver_label.setFont(QFont(self._font, self._bfontsize))
        self.simver_ver.setFont(QFont(self._font, self._bfontsize))
        self.simtime_label.setFont(QFont(self._font, self._bfontsize))
        self.simtime_entry.setFont(QFont(self._font, self._bfontsize))


        self.title_label = QtWidgets.QLabel(titleName)
        self.title_label.setFont(QFont(self._font, self._tfontsize))

        self._line0 = QtWidgets.QLabel('------------')
        self._line1 = QtWidgets.QLabel('------------')
        self._line2 = QtWidgets.QLabel('------------')
        self._line3 = QtWidgets.QLabel('------------')
        self._line4 = QtWidgets.QLabel('============')
        self._line5 = QtWidgets.QLabel('============')

        self.sdate_label = QtWidgets.QLabel('Start Date:')
        self.sdate_entry = QtWidgets.QLineEdit()
        self.edate_label = QtWidgets.QLabel('End Date:')
        self.edate_entry = QtWidgets.QLineEdit()

        _cultivar_name_jp = {'tsukiakari-d': 'つきあかり',
                             'tsukiakari': 'つきあかり',
                             'sasanishiki': 'ササニシキ',
                             'koshihikari': 'コシヒカリ',
                             'nijinokirameki': 'にじのきらめき',
                             'hoshijirushi': 'ほしじるし',
                             'hitomebore': 'ひとめぼれ',
                             'moeminori-d': '萌みのり',
                             'moeminori': '萌みのり',
                             'asahinoyume': 'あさひの夢',
                             'akitakomachi': 'あきたこまち',
                             'sd1': 'コシヒカリつくばSD1',
                             'sd2': 'コシヒカリつくばSD2',
                             'nanatsuboshi': 'ななつぼし',
                             'koisomeshi': '恋初めし',
                             'momiroman': 'モミロマン',
                             'yamadawara': 'やまだわら',
                             'hinohikari': 'ヒノヒカリ',
                             'morinokumasan': '森のくまさん'
        }

        self.cultivar = QtWidgets.QLabel(_cultivar_name_jp[jci['planting']['cultivar']])
        _plant_method_jp = {'direct_sowing': '直播', 'transplantation': '移植'}
        self.method = QtWidgets.QLabel(_plant_method_jp[jci['planting']['method']])
        self.cultivar.setFont(QFont(self._font, self._bfontsize))
        self.method.setFont(QFont(self._font, self._bfontsize))

        self.swdate_label = QtWidgets.QLabel('播種日:')
        self.swdate_date = QtWidgets.QLabel(jci['schedule']['sowing_date']['date'])
        self.tpdate_label = QtWidgets.QLabel('移植日:')
        self.tpdate_date = QtWidgets.QLabel(jci['schedule']['transplanting_date']['date'])
        self.pddate_label = QtWidgets.QLabel('幼穂分化日(推定):')
        self.pddate_date = QtWidgets.QLabel()
        self.ehddate_label = QtWidgets.QLabel('出穂日(推定):')
        self.ehddate_date = QtWidgets.QLabel()
        self.hddate_label = QtWidgets.QLabel('出穂日:')
        self.hddate_date = QtWidgets.QLabel(jci['schedule']['heading_date']['date'])
        self.rpdate_label = QtWidgets.QLabel('刈取日:')
        self.rpdate_date = QtWidgets.QLabel(jci['schedule']['reaping_date']['date'])

        self.swdate_label.setFont(QFont(self._font, self._bfontsize))
        self.swdate_date.setFont(QFont(self._font, self._bfontsize))
        self.tpdate_label.setFont(QFont(self._font, self._bfontsize))
        self.tpdate_date.setFont(QFont(self._font, self._bfontsize))
        self.pddate_label.setFont(QFont(self._font, self._bfontsize))
        self.pddate_date.setFont(QFont(self._font, self._bfontsize))
        self.ehddate_label.setFont(QFont(self._font, self._bfontsize))
        self.ehddate_date.setFont(QFont(self._font, self._bfontsize))
        self.hddate_label.setFont(QFont(self._font, self._bfontsize))
        self.hddate_date.setFont(QFont(self._font, self._bfontsize))
        self.rpdate_label.setFont(QFont(self._font, self._bfontsize))
        self.rpdate_date.setFont(QFont(self._font, self._bfontsize))

        self.so_label = QtWidgets.QLabel('有機物分解:')
        self.so_value = QtWidgets.QLabel()
        self.so_label.setFont(QFont(self._font, self._bfontsize))
        self.so_value.setFont(QFont(self._font, self._bfontsize))

        self.gfdate_label = QtWidgets.QLabel('基肥:')
        if jci['schedule']['ground_fertilizer_date'].get('date') != None:
            ground_fer = True
            self.gfdate_date = QtWidgets.QLabel(jci['schedule']['ground_fertilizer_date']['date'])
            #_fert = self.search_ferti(jci['schedule']['ground_fertilizer_date']['fertilizer_id'])
            self.gfdate_name = QtWidgets.QLabel()
            #v = "{0:,.1f} [kg/10a]".format(jci['schedule']['ground_fertilizer_date']['amount'])
            self.gfdate_weight = QtWidgets.QLabel()
            self.gfdate_name.setFont(QFont(self._font, self._bfontsize))
            self.gfdate_weight.setFont(QFont(self._font, self._bfontsize))
        else:
            ground_fer = False
            self.gfdate_date = QtWidgets.QLabel('なし')
        self.gfdate_label.setFont(QFont(self._font, self._bfontsize))
        self.gfdate_date.setFont(QFont(self._font, self._bfontsize))

        self.afdate_label = []
        self.afdate_date = []
        self.afdate_name = []
        self.afdate_weight = []

        for i, afer in enumerate(jci['schedule']['additional_fertilizer_date']):
            self.afdate_label.append(QtWidgets.QLabel('追肥:'))
            self.afdate_date.append(QtWidgets.QLabel(afer['date']))
            #_fert = self.search_ferti(afer['fertilizer_id'])
            self.afdate_name.append(QtWidgets.QLabel())
            #v = "{0:,.1f} [kg/10a]".format(afer['amount'])
            self.afdate_weight.append(QtWidgets.QLabel())
            print('addtional_fer', i,' : ', afer['date'])
            self.afdate_label[i].setFont(QFont(self._font, self._bfontsize))
            self.afdate_date[i].setFont(QFont(self._font, self._bfontsize))
            self.afdate_name[i].setFont(QFont(self._font, self._bfontsize))
            self.afdate_weight[i].setFont(QFont(self._font, self._bfontsize))

        self.wgbr_label = QtWidgets.QLabel('粗玄米重量:')
        self.wgbr_value = QtWidgets.QLabel()
        self.wbr_label = QtWidgets.QLabel('精玄米重量:')
        self.wbr_value = QtWidgets.QLabel()
        self.loss_label = QtWidgets.QLabel('くず米率:')
        self.loss_value = QtWidgets.QLabel()
        self.protein_label = QtWidgets.QLabel('タンパク質:')
        self.protein_value = QtWidgets.QLabel()
        self.numrice_label = QtWidgets.QLabel('籾数:')
        self.numrice_value = QtWidgets.QLabel()
        self.wgbr_label.setFont(QFont(self._font, self._bfontsize))
        self.wgbr_value.setFont(QFont(self._font, self._bfontsize))
        self.wbr_label.setFont(QFont(self._font, self._bfontsize))
        self.wbr_value.setFont(QFont(self._font, self._bfontsize))
        self.loss_label.setFont(QFont(self._font, self._bfontsize))
        self.loss_value.setFont(QFont(self._font, self._bfontsize))
        self.protein_label.setFont(QFont(self._font, self._bfontsize))
        self.protein_value.setFont(QFont(self._font, self._bfontsize))
        self.numrice_label.setFont(QFont(self._font, self._bfontsize))
        self.numrice_value.setFont(QFont(self._font, self._bfontsize))


        self.awgbr_label = QtWidgets.QLabel('粗玄米重量(実測):')
        if jci['actual_measurement']['gross_brown_rice_weight'] > 0:
            v = "{0:,.2f} [kg/10a]".format(jci['actual_measurement']['gross_brown_rice_weight'])
        else:
            v = "-"
        self.awgbr_value = QtWidgets.QLabel(v)
        self.awbr_label = QtWidgets.QLabel('精玄米重量(実測):')
        if jci['actual_measurement']['brown_rice_weight'] > 0:
            v = "{0:,.2f} [kg/10a]".format(jci['actual_measurement']['brown_rice_weight'])
        else:
            v = "-"
        self.awbr_value = QtWidgets.QLabel(v)
        self.aloss_label = QtWidgets.QLabel('くず米率:(実測)')
        if jci['actual_measurement']['rice_screenings_rate'] > 0:
            v = "{0:,.2f} [%]".format(jci['actual_measurement']['rice_screenings_rate']*100)
        else:
            v = "-"
        self.aloss_value = QtWidgets.QLabel(v)
        self.aprotein_label = QtWidgets.QLabel('タンパク質(実測):')
        if jci['actual_measurement']['protein'] > 0:
            v = "{0:,.2f} [%]".format(jci['actual_measurement']['protein']*100)
        else:
            v = "-"
        self.aprotein_value = QtWidgets.QLabel(v)
        self.awgbr_label.setFont(QFont(self._font, self._bfontsize))
        self.awgbr_value.setFont(QFont(self._font, self._bfontsize))
        self.awbr_label.setFont(QFont(self._font, self._bfontsize))
        self.awbr_value.setFont(QFont(self._font, self._bfontsize))
        self.aloss_label.setFont(QFont(self._font, self._bfontsize))
        self.aloss_value.setFont(QFont(self._font, self._bfontsize))
        self.aprotein_label.setFont(QFont(self._font, self._bfontsize))
        self.aprotein_value.setFont(QFont(self._font, self._bfontsize))

        n_row = 1
        self.grid_l.addWidget(self.title_label, n_row, 0, 1, 3)

        n_row += 1
        self.grid_l.addWidget(self.cultivar, n_row, 0)
        self.grid_l.addWidget(self.method, n_row, 1)

        n_row += 1
        self.grid_l.addWidget(self._line0, n_row, 0)

        n_row += 1
        self.grid_l.addWidget(self.simver_label, n_row, 0)
        self.grid_l.addWidget(self.simver_ver, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.simtime_label, n_row, 0)
        self.grid_l.addWidget(self.simtime_entry, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self._line1, n_row, 0)

        n_row += 1
        self.grid_l.addWidget(self.swdate_label, n_row, 0)
        self.grid_l.addWidget(self.swdate_date, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.tpdate_label, n_row, 0)
        self.grid_l.addWidget(self.tpdate_date, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.pddate_label, n_row, 0)
        self.grid_l.addWidget(self.pddate_date, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.ehddate_label, n_row, 0)
        self.grid_l.addWidget(self.ehddate_date, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.hddate_label, n_row, 0)
        self.grid_l.addWidget(self.hddate_date, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.rpdate_label, n_row, 0)
        self.grid_l.addWidget(self.rpdate_date, n_row, 1)

        n_row += 1
        self.grid_l.addWidget(self._line2, n_row, 0)

        n_row += 1
        self.grid_l.addWidget(self.so_label, n_row, 0)
        self.grid_l.addWidget(self.so_value, n_row, 1, 1, 2)

        n_row += 1
        self.grid_l.addWidget(self.gfdate_label, n_row, 0)
        self.grid_l.addWidget(self.gfdate_date, n_row, 1)
        if ground_fer:
            n_row += 1
            self.grid_l.addWidget(self.gfdate_name, n_row, 1)
            self.grid_l.addWidget(self.gfdate_weight, n_row, 2)

        for i, afer in enumerate(jci['schedule']['additional_fertilizer_date']):
            n_row += 1
            self.grid_l.addWidget(self.afdate_label[i], n_row, 0)
            self.grid_l.addWidget(self.afdate_date[i], n_row, 1)
            n_row += 1
            self.grid_l.addWidget(self.afdate_name[i], n_row, 1)
            self.grid_l.addWidget(self.afdate_weight[i], n_row, 2)

        n_row += 1
        self.grid_l.addWidget(self._line3, n_row, 0)

        n_row += 1
        self.grid_l.addWidget(self.wgbr_label, n_row, 0)
        self.grid_l.addWidget(self.wgbr_value, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.wbr_label, n_row, 0)
        self.grid_l.addWidget(self.wbr_value, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.loss_label, n_row, 0)
        self.grid_l.addWidget(self.loss_value, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.protein_label, n_row, 0)
        self.grid_l.addWidget(self.protein_value, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.numrice_label, n_row, 0)
        self.grid_l.addWidget(self.numrice_value, n_row, 1)

        n_row += 1
        self.grid_l.addWidget(self._line4, n_row, 0)

        n_row += 1
        self.grid_l.addWidget(self.awgbr_label, n_row, 0)
        self.grid_l.addWidget(self.awgbr_value, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.awbr_label, n_row, 0)
        self.grid_l.addWidget(self.awbr_value, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.aloss_label, n_row, 0)
        self.grid_l.addWidget(self.aloss_value, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.aprotein_label, n_row, 0)
        self.grid_l.addWidget(self.aprotein_value, n_row, 1)

        n_row += 1
        self.grid_l.addWidget(self._line5, n_row, 0)

        n_row += 1
        self.grid_l.addWidget(self.sdate_label, n_row, 0)
        self.grid_l.addWidget(self.sdate_entry, n_row, 1)
        n_row += 1
        self.grid_l.addWidget(self.edate_label, n_row, 0)
        self.grid_l.addWidget(self.edate_entry, n_row, 1)

        n_row += 1
        self.grid_l.addWidget(self.sim_bt, n_row, 0)

        self.rd_bt = QtWidgets.QPushButton('ReDraw')
        self.rd_bt.clicked.connect(self.button_pushed)
        self.grid_l.addWidget(self.rd_bt, n_row, 1)

        self.F = plt.figure()

        self.canvas = FigureCanvas(self.F)
        self.canvas.setParent(self.main_widget)

        self.l.addLayout(self.grid_l)
        self.l.addWidget(self.canvas, stretch=1)
        self.setCentralWidget(self.main_widget)

    def read_label(self, label_path):
        self.label_list = {}
        f = open(label_path, 'r')
        reader = csv.reader(f)

        for row in reader:
            self.label_list[row[0]] = row[1]

    def set_label(self, sublist, labels, label_list):
        for row in sublist:
            if row in label_list:
                labels.append(label_list[row])
            else:
                labels.append(row)

    def button_pushed(self):
        self.sdate = datetime.datetime.strptime(self.sdate_entry.text(),'%Y-%m-%d')
        self.edate = datetime.datetime.strptime(self.edate_entry.text(),'%Y-%m-%d')
        print(self.sdate, self.edate)
        self.draw(self.F, self.canvas, False)

    def search_ferti(self, id):
        for _f in self.fert:
            if _f['id'] == id:
                _fert = _f
                break
        return _fert

    def draw(self, F, canvas, reLoad = False):
        if reLoad :
            self.df_org = pd.read_csv(self.output, parse_dates=True, index_col='Date')

        if self.sdate is None:
            self.sdate = self.df_org.index[1].date()

        if self.edate is None:
            self.edate = self.df_org.index[-1].date()

        self.df = self.df_org[self.sdate:self.edate]

        self.sdate_entry.setText(self.sdate.strftime('%Y-%m-%d'))
        self.edate_entry.setText(self.edate.strftime('%Y-%m-%d'))

        self.F.clear()

        n_row = min(5,len(self.drawLists))
        n_col = math.ceil(len(self.drawLists) / n_row)
        n_row = math.ceil(len(self.drawLists) / n_col)
        n_fig = 0
        for sublist in self.drawLists:
            plt.rcParams['font.size'] = self._gfontsize
            fs = F.add_subplot(n_row, n_col, self.drawLists.index(sublist)+1)
            fs.cla()
            labels = []
            self.set_label(sublist, labels, self.label_list)
            self.df.plot(ax=fs, y=sublist, alpha=0.5, label=labels, linewidth=1.0)
            plt.subplots_adjust(left=0.05, right=0.95, bottom=0.1, top=0.95)
            #plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0, fontsize=5)
            fs.grid()

        canvas.draw()

    def set_sim_prop(self):
        df = pd.read_csv(self.output, parse_dates=True, index_col='Date')
        self.simver_ver.setText(df.iloc[0]['cgsm-version'])
        ntime = datetime.datetime.now()
        self.simtime_entry.setText(ntime.strftime('%Y-%m-%d %H:%M:%S'))

    def set_pdhd_date(self):
        df = pd.read_csv(self.output, parse_dates=True, index_col='Date')
        df_pd = df[df['ElapsedDaysSincePanicleDifferentiation'] == 1].index
        if len(df_pd) == 24:
            pdd = df_pd[1].strftime('%Y-%m-%d')
            self.pddate_date.setText(pdd)

        df_hd = df[df['ElapsedDaysSinceHeading'] == 1].index
        self.hdd = ''
        if len(df_hd) == 24:
            hdd = df_hd[1].strftime('%Y-%m-%d')
            self.ehddate_date.setText(hdd)

    def set_manure_info(self, jci):
        v = "{0:,.1f} (x 5%) [kg/10a/year]".format(jci['schedule']['manure']['amount'])
        self.so_value.setText(v)

    def set_fer_info(self, jci):
        _fert = self.search_ferti(jci['schedule']['ground_fertilizer_date']['fertilizer_id'])
        self.gfdate_name.setText(_fert['name'])
        v = "{0:,.1f} [kg/10a]".format(jci['schedule']['ground_fertilizer_date']['amount'])
        self.gfdate_weight.setText(v)
        for i, afer in enumerate(jci['schedule']['additional_fertilizer_date']):
            _fert = self.search_ferti(afer['fertilizer_id'])
            self.afdate_name[i].setText(_fert['name'])
            v = "{0:,.1f} [kg/10a]".format(afer['amount'])
            self.afdate_weight[i].setText(v)


    def set_rice_info(self):
        df = pd.read_csv(self.output, parse_dates=True, index_col='Date')
        v = "{0:,.2f} [kg/10a]".format(df['WeightBrownRice'][self.sim_edate])
        self.wbr_value.setText(v)
        v = "{0:,.2f} [kg/10a]".format(df['WeightGrossBrownRice'][self.sim_edate])
        self.wgbr_value.setText(v)
        v = "{0:,.2f} [%]".format(df['RiceScreeningsRate'][self.sim_edate]*100)
        self.loss_value.setText(v)
        v = "{0:,.0f} [個/m2]".format(df['NumberOfRoughRice'][self.sim_edate])
        self.numrice_value.setText(v)
        v = "{0:,.2f} [%]".format(df['Protein'][self.sim_edate]*100)
        self.protein_value.setText(v)

    def create_initdb(self, initdb, sdate, edate, avewdb, imsdb):
        _idf = pd.read_csv(initdb)
        _idf['Date'] = sdate - datetime.timedelta(hours=1)
        print(sdate)
        print(_idf)
        idf = _idf.set_index('Date')
        idf.loc[:] = np.nan
        simdays = (edate - sdate).days

        ddf = pd.DataFrame([[np.nan]], index=[sdate + datetime.timedelta(hours=i) for i in range((simdays+1)*24)], columns=['RedAbsorptionRate'])
        ddf.index.name = 'Date'

        idf = pd.concat([idf, ddf], sort=True)

        ims = pd.read_csv(imsdb, parse_dates=True, index_col='Date')
        idf.update(ims)

        dw = pd.read_csv(avewdb, parse_dates=True, index_col='Date', comment='#')
        ins_aw.insertAverageWeatherData(idf,dw)
        print(idf['AveSolarRadiation'])
        idf['AveSolarRadiation'] = idf['AveSolarRadiation'].fillna(method='ffill')

        adt, ant = np.nan, np.nan
        for index, row in idf.iterrows():
            if np.isnan(row['AveNighttimeTemperature']):
                idf.at[index,'AveDaytimeTemperature'] = adt
                idf.at[index,'AveNighttimeTemperature'] = ant
            else:
                adt = row['AveDaytimeTemperature']
                ant = row['AveNighttimeTemperature']

        idf.to_csv('.tmp.csv')
        self.df = '.tmp.csv'

    def simulation(self):

        #self.create_initdb(self.initvalues, self.sim_sdate, self.sim_edate, self.avewdb, self.ims)


        self.gsim.initialize_db()
        self.gsim.run()

        self.set_pdhd_date()
        with open(self.commoninfo) as fjci:
            jci = json.load(fjci)
            fjci.close()
        self.set_manure_info(jci)
        self.set_fer_info(jci)
        self.set_rice_info()
        self.set_sim_prop()
        self.draw(self.F, self.canvas, True)

    def save(self):
        savePath = os.path.splitext(self.output)[0] + '_' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") +'.png'
        self.F.savefig(savePath)
        print("save plot image", savePath, sep=":")


def call_gsm_sim(
        begin, finish,
        initvalues, idealdat, database,
        baseweatherdb, weatherdb, fcweatherdb,
        fieldsensor,
        commoninfo, fertilizer,
        coeff, coeffcultivar, output,
        headingdate, checkmtime):

    gsm_simulator.gsm_simulator(
        begin, args.finish,
        initvalues, idealdat, database, baseweatherdb, weatherdb, fcweatherdb,
        fieldsensor,
        commoninfo, fertilizer,
        coeff, coeffcultivar, output,
        headingdate, checkmtime)

def _main():
    # if os.path.isfile(args.database) == False :
    #     print("ERROR: no input database")
    #     sys.exit(1)

    if args.globaldir is not None:
        initvalues = args.globaldir + '/init_db.csv'
        #fertilizer = args.globaldir + '/fertilizer.json'
        coeff = args.globaldir + '/coeff.csv'
        coeffcultivar = args.globaldir + '/coeff_cultivar.csv'
        idealdat = args.globaldir + '/base_ideal_gindex.csv'
    else:
        initvalues = args.initvalues
        coeff = args.coeff
        coeffcultivar = args.coeffcultivar
        idealdat = args.idealdat
    fertilizer = args.fertilizer

    if args.fielddir is not None:
        baseweatherdb = args.fielddir + '/weatherdb.csv'
        weatherdb = None
        imsense = args.fielddir + '/imsense.csv'
        commoninfo = args.fielddir + '/common_info.json'
        output = args.fielddir + '/out_gsm_db.csv'
        fieldsensor = args.fielddir + '/fieldsensor.csv'
        fcweatherdb = args.fielddir + '/weatherdb_fc.csv'
        wflux = args.fielddir + '/wflux.csv'
        if os.path.isfile(fieldsensor) == False or args.nousefieldsensor == True:
            fieldsensor = None
        if os.path.isfile(baseweatherdb) == False:
            baseweatherdb = None
        if os.path.isfile(fcweatherdb) == False:
            fcweatherdb = None
    else:
        baseweatherdb = args.baseweatherdb
        weatherdb = args.weatherdb
        fcweatherdb = args.fcweatherdb
        imsense = args.imsense
        commoninfo = args.commoninfo
        output = args.output
        fieldsensor = args.fieldsensor
        wflux = agrgs.watrerflux

    '''
    call_gsm_sim(args.begin, args.finish,
                 database, weatherdb, commoninfo, fertilizer,
                 coeff, coeffcultivar, output,
                 args.headingdate, args.checkmtime)
    '''

    drawLists = []
    with open(args.drawlist) as fjdr:
        jd = json.load(fjdr)
        for i in range(len(jd['figures'])):
            sublist = []
            #ylabels.append(jd['figures'][i]['ylabel'])
            for j in range(len(jd['figures'][i]['dbkey'])):
                sublist.append(jd['figures'][i]['dbkey'][j])
            drawLists.append(sublist)

    with open(commoninfo) as fjci:
        jci = json.load(fjci)
        fjci.close()

    if args.weatherdir is not None and jci['field'].get('mesh3code') is not None:
        weatherdb = args.weatherdir + '/w-' + str(jci['field']['mesh3code']) + '.csv'
        fcweatherdb = args.weatherdir + '/fcw-' + str(jci['field']['mesh3code']) + '.csv'

    with open(fertilizer) as ffert:
        fert = json.load(ffert)
        ffert.close()

    app = QtWidgets.QApplication([])
    if args.begin is not None:
        sbegin = args.begin
    else:
        _plant_method = {'direct_sowing': 'sowing_date', 'transplantation': 'transplanting_date'}
        plant_method = _plant_method[jci['planting']['method']]
        #sbegin = jci['schedule'][plant_method]['date']
        sbegin = jci['schedule']['manure']['date']

    if args.finish is not None:
        sfinish = args.finish
    elif 'date' in jci['schedule']['reaping_date']:
        sfinish = jci['schedule']['reaping_date']['date']
    else:
        sfinish = None

    awin = ApplicationWindow(jci['field']['farm']+" "+jci['field']['name'],
                             jci, fert,
                             sbegin, sfinish,
                             initvalues, baseweatherdb, weatherdb, fcweatherdb,
                             fieldsensor, commoninfo, fertilizer, idealdat,
                             args.aveweatherdb, imsense,
                             coeff, coeffcultivar, wflux, output,
                             args.headingdate, args.checkmtime,
                             args.label,
                             drawLists,
                             args.displaysize)

    awin.setWindowTitle(jci['field']['farm']+" "+jci['field']['name'])
    if args.grab is not None:
        awin.showFullScreen()
        awin.grab().save(args.grab+"/"+jci['field']['farm']+jci['field']['name']+".png")
        QTimer.singleShot(1000, awin.close)
    else:
        awin.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    _main()
