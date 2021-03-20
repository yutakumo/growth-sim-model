import os
import sys
import argparse
import pandas as pd
import datetime

import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import tkinter as Tk

import gsm_simulator
import gsm_gui_select

parser = argparse.ArgumentParser()


parser.add_argument('-b', '--begin',
                    help='beginning date of simulator')
parser.add_argument('-f', '--finish',
                    help='finishing date of simulator')
parser.add_argument('-d', '--database', default='./sampledat/gsm_db.csv',
                    help='path of input database')
parser.add_argument('-o', '--output', default='./out.csv',
                    help='path of output database')
parser.add_argument('-c', '--coeff', default='./sampledat/coeff.csv',
                    help='path of coeffiecient database')
parser.add_argument('-cb', '--coeffbreed', default='./sampledat/coeff_breed.csv',
                    help='path of breed specific coeffiecient database')
parser.add_argument('-w', '--weatherdb', default='./sampledat/shirochi_summarize.csv',
                    help='path of weather information database')
parser.add_argument('-frtl', '--fertilizer', default='./sampledat/fertilizer.json',
                    help='path of fertilizer information file')
parser.add_argument('-ci', '--commoninfo', default='./sampledat/common_info.json',
                    help='path of growth planning information file')
parser.add_argument('-hd', '--headingdate', choices=['fix', 'predict', 'simulate'], default='simulate',
                    help='select kind of heading date')

parser.add_argument('-gd', '--globaldir',
                    help='directory of global data')
parser.add_argument('-fd', '--fielddir',
                    help='directory of field data')

parser.add_argument('-cmt', '--checkmtime', action='store_false',
                    help='check mtime of growth planning information file and database')

parser.add_argument('-gs', '--guiselect', default='./gui_select.csv',
                    help='path of gui_select.csv')

args = parser.parse_args()

class Application(Tk.Frame):
    def __init__(self,
                 begin, finish,
                 database, weatherdb, commoninfo, fertilizer,
                 coeff, coeffbreed, output,
                 headingdate, checkmtime,
                 guiselect,
                 master=None):
        Tk.Frame.__init__(self, master)
        self.begin = begin
        self.finish = finish
        self.database = database
        self.weatherdb = weatherdb
        self.commoninfo = commoninfo
        self.fertilizer = fertilizer
        self.coeff = coeff
        self.coeffbreed = coeffbreed
        self.output = output
        self.headingdate = headingdate
        self.checkmtime = checkmtime
        self.guiselect = guiselect
        self.guiselect.set_gui_select_coeff()
        self.pack(expand=0, fill=Tk.BOTH, anchor=Tk.NW)
        self.create_widgets(master)

    def create_widgets(self, master):
        self.frame = Tk.Frame(master)
        self.frame.pack(side=Tk.BOTTOM)

        # self.bt = Tk.Button(self.frame, text='UpLoad SIM', command=lambda:self.draw(self.F, self.canvas))
        # self.bt.grid(row=2, column=3)

        self.bt = Tk.Button(self.frame, text='SIMULATION!', command=self.simulation)
        self.bt.grid(row=2, column=2)

        self.button = Tk.Button(self.frame, text='Save', command=self.save)
        self.button.grid(row=2, column=3)

        self.sdate_label = Tk.Label(self.frame, text='Start Date:')
        self.sdate_label.grid(row=0, column=0)
        self.sdate = Tk.StringVar()
        self.sdate_entry = Tk.Entry(
            self.frame,
            textvariable=self.sdate,
            width=10)
        self.sdate_entry.grid(row=0, column=1)

        self.edate_label = Tk.Label(self.frame, text='End Date:')
        self.edate_label.grid(row=1, column=0)
        self.edate = Tk.StringVar()
        self.edate_entry = Tk.Entry(
            self.frame,
            textvariable=self.edate,
            width=10)
        self.edate_entry.grid(row=1, column=1)

        self.button = Tk.Button(self.frame, text='ReDraw', command=self.button_pushed)
        self.button.grid(row=2, column=1)

        initialFigSize = (16, 12)
        self.F = Figure(figsize=initialFigSize)

        self.canvas = FigureCanvasTkAgg(self.F, master=master)
        self.canvas.get_tk_widget().pack(fill=Tk.BOTH, side=Tk.BOTTOM, expand=1)
        self.canvas._tkcanvas.pack(side=Tk.BOTTOM, expand=1)
        self.draw(self.F, self.canvas)


    def button_pushed(self):
        self.sdatetime = datetime.datetime.strptime(self.sdate.get(),'%Y-%m-%d').date()
        self.edatetime = datetime.datetime.strptime(self.edate.get(),'%Y-%m-%d').date()
        print(self.sdatetime, self.edatetime)
        self.draw(self.F, self.canvas, self.sdatetime, self.edatetime)


    def draw(self, F, canvas, sdate=None, edate=None):
        if sdate is not None and edate is not None :
            self.df = self.df_org[sdate:edate]
        else:
            self.df_org = pd.read_csv(self.output, parse_dates=True, index_col='Date')
            self.sdate.set(self.df_org.index[0].date())
            self.edate.set(self.df_org.index[-1].date())
            self.df = self.df_org

        drawLists = self.guiselect.get_draw_list()
        maxIndex = self.guiselect.get_max_index()

        self.F.clear()
        verticalSize = min(12, (4 * (maxIndex + 1)))
        self.F.set_size_inches(16, verticalSize)


        for sublist in drawLists:
            fs = F.add_subplot(len(drawLists), 1, drawLists.index(sublist)+1)
            fs.cla()
            self.df.plot(ax=fs, y=sublist, alpha=0.5)
            fs.grid()

        canvas.draw()


    def simulation(self):
        self.guiselect.update_coeff()
        call_gsm_sim(self.begin, self.finish,
                     self.database, self.weatherdb, self.commoninfo, self.fertilizer,
                     self.coeff, self.coeffbreed, self.output,
                     self.headingdate, self.checkmtime)

        self.draw(self.F, self.canvas)

    def save(self):
        savePath = os.path.splitext(self.output)[0] + '_' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") +'.png'
        self.F.savefig(savePath)
        print("save plot image", savePath, sep=":")


def call_gsm_sim(
        begin, finish,
        database, weatherdb, commoninfo, fertilizer,
        coeff, coeffbreed, output,
        headingdate, checkmtime):

    gsm_simulator.gsm_simulator(
        begin, args.finish,
        database, weatherdb, commoninfo, fertilizer,
        coeff, coeffbreed, output,
        headingdate, checkmtime)

def _main():
    # if os.path.isfile(args.database) == False :
    #     print("ERROR: no input database")
    #     sys.exit(1)

    if args.globaldir is not None:
        fertilizer = args.globaldir + '/fertilizer.json'
        coeff = args.globaldir + '/coeff.csv'
        coeffbreed = args.globaldir + '/coeff_breed.csv'
    else:
        fertilizer = args.fertilizer
        coeff = args.coeff
        coeffbreed = args.coeffbreed

    if args.fielddir is not None:
        database = args.fielddir + '/gsm_db.csv'
        weatherdb = args.fielddir + '/weatherdb.csv'
        commoninfo = args.fielddir + '/common_info.json'
        output = args.fielddir + '/out_gsm_db.csv'
    else:
        database = args.database
        weatherdb = args.weatherdb
        commoninfo = args.commoninfo
        output = args.output

    root = Tk.Tk()

    call_gsm_sim(args.begin, args.finish,
                 database, weatherdb, commoninfo, fertilizer,
                 coeff, coeffbreed, output,
                 args.headingdate, args.checkmtime)

    guiselect = gsm_gui_select.GuiSelect(args.guiselect, coeff, coeffbreed)

    app = Application(args.begin, args.finish,
                      database, weatherdb, commoninfo, fertilizer,
                      coeff, coeffbreed, output,
                      args.headingdate, args.checkmtime,
                      guiselect,
                      master=root)
    app.mainloop()

if __name__ == '__main__':
    _main()
