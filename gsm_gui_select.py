
import os
import sys
import pandas as pd
import re
class GuiSelect():

    def __init__(self, guiselectPath, coeffPath, coeffBreedPath):
        self.guiselectPath = guiselectPath
        self.coeffPath = coeffPath
        self.coeffBreedPath = coeffBreedPath

    def get_max_index(self):
        guiSelectList = pd.read_csv(self.guiselectPath)

        selected = list(filter(lambda row:row.select == row.select, guiSelectList.itertuples()))
        maxIndex = int(max([x.select for x in selected]))

        return maxIndex

    def get_draw_list(self):
        guiSelectList = pd.read_csv(self.guiselectPath)

        selected = list(filter(lambda row:row.select == row.select, guiSelectList.itertuples()))
        maxIndex = int(max([x.select for x in selected]))

        drawLists = []

        for i in range(maxIndex + 1):
            targetList = list(filter(lambda row:row.select == i, selected ))
            sublist = [x.dbKey for x in targetList]
            drawLists.append(sublist)

        drawLists = list(filter(lambda sublist: len(sublist) != 0, drawLists))

        return drawLists

    def update_coeff(self):

        # コメントだけ取得
        coeffListDf = pd.read_csv(self.coeffPath)
        #coeffBreedListDf = pd.read_csv(self.coeffBreedPath)
        coeffComment = ','.join(coeffListDf.columns)
        #coeffBreedComment = ','.join(coeffBreedListDf.columns)


        coeffListDf = pd.read_csv(self.coeffPath, comment='#')
        #coeffBreedListDf = pd.read_csv(self.coeffBreedPath, comment='#')

        guiSelectDf = pd.read_csv(self.guiselectPath)

        selectCoeffList = list(filter(lambda row:row.coeff0 != 'coeff0' and row.coeff0 == row.coeff0, guiSelectDf.itertuples()))

        # 係数が1つあるもの
        selectCoeffList1 = list(filter(lambda row: row.coeff1 != row.coeff1, selectCoeffList))
        for selectCoeff in selectCoeffList1:
            coeffName = 'Coeff' + selectCoeff.dbKey
            #coeffListDf.at[0, coeffName] = selectCoeff.coeff0
            coeffListDf[coeffName] = selectCoeff.coeff0

        # 係数が2つあるもの
        selectCoeffList2 = list(filter(lambda row: row.coeff1 == row.coeff1, selectCoeffList))
        for selectCoeff in selectCoeffList2:
            coeffName = 'Coeff0' + selectCoeff.dbKey
            coeffListDf[ coeffName] = selectCoeff.coeff0
            coeffName = 'Coeff1' + selectCoeff.dbKey
            coeffListDf[coeffName] = selectCoeff.coeff1

        # 定数
        selectConstList = list(filter(lambda row: row.const == row.const, selectCoeffList))
        for selectCoeff in selectConstList:
            coeffName = 'Const' + selectCoeff.dbKey
            coeffListDf[coeffName] = selectCoeff.const

        '''
        # 品種係数
        selectBreedCoeffList = list(filter(lambda row:row.coeffBreed != 'coeffBreed' and row.coeffBreed == row.coeffBreed, guiSelectDf.itertuples()))

        for selectCoeff in selectBreedCoeffList:
            coeffName =selectCoeff.dbKey.replace('Rs', 'CoeffBreed')
            coeffBreedListDf[coeffName] = selectCoeff.coeffBreed
        '''

        try:
            with open(self.coeffPath, 'w', encoding="utf_8_sig") as f:
                f.write(coeffComment + '\r\n')
            coeffListDf.to_csv(self.coeffPath, mode='a', index=False, encoding="utf_8_sig", line_terminator="\r\n")

        except PermissionError:
            print('Cannot write' + self.coeffPath + '. Please close this file.')
            sys.exit()

        '''
        try:
            with open(self.coeffBreedPath, 'w', encoding="utf_8_sig") as f:
                f.write(coeffBreedComment + '\r\n')
            coeffBreedListDf.to_csv(self.coeffBreedPath, mode='a',index=False, encoding="utf_8_sig", line_terminator="\r\n")

        except PermissionError:
            print('Cannot write' + self.coeffBreedPath + '. Please close this file.')
            sys.exit()
        '''

    def set_gui_select_coeff(self):

        coeffListDf = pd.read_csv(self.coeffPath, comment='#')
        #coeffBreedListDf = pd.read_csv(self.coeffBreedPath, comment='#')

        guiSelectDf = pd.read_csv(self.guiselectPath)

        selectCoeffList = list(filter(lambda row:row.coeff0 != 'coeff0' and row.coeff0 == row.coeff0, guiSelectDf.itertuples()))

        # 係数が1つあるもの
        selectCoeffList1 = list(filter(lambda row: row.coeff1 != row.coeff1, selectCoeffList))
        for selectCoeff in selectCoeffList1:
            coeffName = 'Coeff' + selectCoeff.dbKey
            guiSelectDf.at[selectCoeff.Index, 'coeff0'] = coeffListDf.at[0, coeffName]

        # 係数が2つあるもの
        selectCoeffList2 = list(filter(lambda row: row.coeff1 == row.coeff1, selectCoeffList))
        for selectCoeff in selectCoeffList2:
            coeffName = 'Coeff0' + selectCoeff.dbKey
            guiSelectDf.at[selectCoeff.Index, 'coeff0'] = coeffListDf.at[0, coeffName]
            coeffName = 'Coeff1' + selectCoeff.dbKey
            guiSelectDf.at[selectCoeff.Index, 'coeff1'] = coeffListDf.at[0, coeffName]

        # 定数
        selectConstList = list(filter(lambda row: row.const == row.const, selectCoeffList))
        for selectCoeff in selectConstList:
            coeffName = 'Const' + selectCoeff.dbKey
            guiSelectDf.at[selectCoeff.Index, 'const'] = coeffListDf.at[0, coeffName]

        # 品種係数
        '''
        selectBreedCoeffList = list(filter(lambda row:row.coeffBreed != 'coeffBreed' and row.coeffBreed == row.coeffBreed, guiSelectDf.itertuples()))

        for selectCoeff in selectBreedCoeffList:
            coeffName =selectCoeff.dbKey.replace('Rs', 'CoeffBreed')
            guiSelectDf.at[selectCoeff.Index, 'coeffBreed'] = coeffBreedListDf.at[0, coeffName]
        '''

        try:
            guiSelectDf.to_csv(self.guiselectPath, mode='w', index=False, encoding="utf_8_sig", line_terminator="\r\n")
        except PermissionError:
            print('Cannot write' + self.guiselectPath + '. Please close this file.')
            sys.exit()
