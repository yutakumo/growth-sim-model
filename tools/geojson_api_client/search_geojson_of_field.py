import datetime
import numpy as np
import pandas as pd
from collections import defaultdict

import getGrowthData as gd

def get_colnum(row, key):
    ncol = [i for i, v in enumerate(row) if v == key]

    return ncol[0] if len(ncol) == 1 else -1

def set_field(
        icsv_data, target_date, fieldList,
        listId, invlistId,
        farmName, fieldName, breedName, areaName):

    farmCn = get_colnum(icsv_data[0], '農場')
    fieldCn = get_colnum(icsv_data[0], '圃場名')
    farmIdCn = get_colnum(icsv_data[0], '農場ID')
    fieldIdCn = get_colnum(icsv_data[0], '圃場ID')
    breedCn = get_colnum(icsv_data[0], '品種')
    areaCn = get_colnum(icsv_data[0], '地域')

    for i in range(1,len(icsv_data)):
        row = icsv_data[i]
        if icsv_data.index(row) == 0:
            continue
        #odat = row
        field = gd.fieldDat()
        field.FarmId = row[farmIdCn]
        field.FieldId = row[fieldIdCn]
        field.TargetDay = target_date
        fieldList.append(field)

        listId[field.FieldId] = row[0]
        invlistId[row[0]] = field.FieldId
        farmName[field.FieldId] = row[farmCn]
        fieldName[field.FieldId] = row[fieldCn]
        if breedCn != -1:
            breedName[field.FieldId] = row[breedCn]
        if areaCn != -1:
            areaName[field.FieldId] = row[areaCn]

def set_mesh(fieldList, red_hash, datelist, nileworks):
    for field in fieldList:
        for mesh in field.Meshes:
            #odat = [farmName[field.FieldId], fieldName[field.FieldId], mesh[0], mesh[1].date().isoformat(), mesh[2]]

            datelist.append(mesh[1].date().isoformat())
            if nileworks:
                result = mesh[2] if mesh[2] != '0.000' else 'ZERO'
            else:
                result = 'OK' if mesh[2] != '0.000' else 'TBV'

            if mesh[0] == 'red_absorption':
                red_hash[mesh[1].date().isoformat()][field.FieldId]['red'] = result
            elif mesh[0] == 'effective_sun_ray_receiving_area_rate':
                red_hash[mesh[1].date().isoformat()][field.FieldId]['eff'] = result

def insert_nulldata_field(icsv_data, ocsv_data,
                          invlistId,
                          farmName, fieldName,
                          existArea, areaName,
                          existBreed, breedName):
    c = 0
    for i in range(len(icsv_data)):
        if i > 0 and icsv_data[i][0] != c:
            while icsv_data[i][0] - c > 0:
                fieldid = invlistId[str(c)]
                t_data = [c]
                if existArea:
                    t_data.append(areaName[fieldid])
                t_data.append(farmName[fieldid])
                t_data.append(fieldName[fieldid])
                if existBreed:
                    t_data.append(breedName[fieldid])
                ocsv_data.append(t_data)
                c += 1
        ocsv_data.append(icsv_data[i])
        c += 1

    print(c, ocsv_data)

def create_temporal_view(df, datelist,
                         ocsv_data, existArea, existBreed):
    csv_index = ['id']
    if existArea:
        csv_index.append('area')
    csv_index.append('farmName')
    csv_index.append('fieldName')
    if existBreed:
        csv_index.append('breed')

    for d in datelist:
        csv_index.append(d+' (RED)')
        csv_index.append('(ESRRA)')

    #_ocsv_data = []
    ocsv_data.append(csv_index)

    for index, row in df.iterrows():
        csv_row = [row['id']]
        if existArea:
            csv_row.append(row['area'])
        csv_row.append(row['farmName'])
        csv_row.append(row['fieldName'])
        if existBreed:
            csv_row.append(row['breed'])

        for d in datelist:
            if type(row[d]) is float and np.isnan(row[d]):
                csv_row.append('')
                csv_row.append('')
            else:
                csv_row.append(str(row[d]['red'] if 'red' in row[d].keys() else 'None'))
                csv_row.append(str(row[d]['eff'] if 'eff' in row[d].keys() else 'None'))
        ocsv_data.append(csv_row)


def search_geojson_of_field(auth, icsv_data, ocsv_data, target_date, nileworks=True):

    fieldList = []
    listId = {}
    invlistId = {}
    farmName = {}
    fieldName = {}
    breedName = {}
    areaName = {}

    set_field(
        icsv_data, target_date, fieldList,
        listId, invlistId,
        farmName, fieldName, breedName, areaName)

    existBreed = True if len(breedName) > 0 else False
    existArea = True if len(areaName) > 0 else False

    gd.getGrowthData(auth, fieldList)

    datelist = []
    nested_dict = lambda: defaultdict(nested_dict)
    red_hash = nested_dict()
    eff_hash = nested_dict()

    set_mesh(fieldList, red_hash, datelist, nileworks)
    datelist = sorted(list(set(datelist)))

    red_df = pd.DataFrame(red_hash)

    id_df = []
    farm_df = []
    field_df = []
    breed_df = []
    area_df = []
    for field_id in red_df.index:
        id_df.append(int(listId[field_id]))
        farm_df.append(farmName[field_id])
        field_df.append(fieldName[field_id])
        if existBreed:
            breed_df.append(breedName[field_id])
        if existArea:
            area_df.append(areaName[field_id])

    red_df['id'] = id_df
    red_df['farmName'] = farm_df
    red_df['fieldName'] = field_df
    if existBreed:
        red_df['breed'] = breed_df
    if existArea:
        red_df['area'] = area_df

    df = red_df.sort_values('id')
    print(df)

    _ocsv_data = []
    create_temporal_view(df, datelist, _ocsv_data, existArea, existBreed)

    # add null field
    insert_nulldata_field(_ocsv_data, ocsv_data,
                          invlistId,
                          farmName, fieldName,
                          existArea, areaName,
                          existBreed, breedName)
    '''
    c = 0
    for i in range(len(_ocsv_data)):
        if i > 0 and _ocsv_data[i][0] != c:
            while _ocsv_data[i][0] - c > 0:
                fieldid = invlistId[str(c)]
                t_data = [c]
                if existArea:
                    t_data.append(areaName[fieldid])
                t_data.append(farmName[fieldid])
                t_data.append(fieldName[fieldid])
                if existBreed:
                    t_data.append(breedName[fieldid])
                ocsv_data.append(t_data)
                c += 1
        ocsv_data.append(_ocsv_data[i])
        c += 1

    print(c, ocsv_data)
    '''

def main():
    import os
    import sys
    import csv
    import argparse
    if sys.version_info.major != 3:
        print('Please use python3')
        sys.exit(1)

    args = sys.argv

    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--csv', required=True, help='set csv file that is list of longitude and latitude, where you want to get weather data(required) \r\n')
    parser.add_argument('-o', '--output', required=True, help='specify the output directory (required)')
    parser.add_argument('-t', '--token', required=False, default='.token', help='set the token file')
    parser.add_argument('-d', '--day', required=False, help='define the checking day')
    parser.add_argument('--nileworks', required=False, action='store_true', help='set output format')
    args = parser.parse_args()

    if os.path.exists(args.csv):
        csvfile = open(args.csv, encoding="utf_8_sig")
        icsvdata = list(csv.reader(csvfile))
    else:
        print('No specified csv file')
        sys.exit()

    requestHeaders = {'Accept': 'application/json'}

    with open(args.token) as ft:
        auth = ft.read().strip()

    requestHeaders['Authorization'] = auth

    ocsvdata = []
    search_geojson_of_field(auth, icsvdata, ocsvdata, args.day, args.nileworks)

    with open(args.output, 'w', encoding='utf_8_sig') as file:
        writer = csv.writer(file)
        writer.writerows(ocsvdata)

if __name__ == '__main__' : main()
