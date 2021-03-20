import requests
import json
import datetime

class fieldDat():
    def __init__(self):
        self.FarmId = None
        self.FieldId = None
        self.TargetDay = None
        self.Meshes = None

def checkVersion(ver_s):
    ver_n = 100

    if 'devVersion' in ver_s:
        ver_n = int(ver_s['devVersion'].replace('Nile-T19_','').split('_')[1].replace('.',''))

    return ver_n

def diffFromNoon(cdate):
    noon = datetime.datetime(cdate.year, cdate.month, cdate.day, 12)

    if cdate.hour < 12 :
        delta_time = noon - cdate
    else:
        delta_time = cdate - noon

    return delta_time

def checkUpdate(meshes, cmesh):
    _uid = None
    for i, mesh in enumerate(meshes):
        if mesh[0] == cmesh[0] and mesh[1].date() == cmesh[1].date():
            _uid = i
            break

    if _uid is None:
        uid = -1
    elif cmesh[2] == 0.0:
        uid = -2
    elif meshes[_uid][2] == 0.0:
        # check value
        uid = _uid
    elif meshes[_uid][3] < cmesh[3]:
        # check number of calculated area
        uid = _uid
    elif meshes[_uid][3] == cmesh[3] and diffFromNoon(meshes[_uid][1]) > diffFromNoon(cmesh[1]):
        # check date of flight
        uid = _uid
    else:
        uid = -2

    return uid

def getGrowthData(auth, fieldList, required=False):
    requestHeaders = {'Accept': 'application/json'}
    requestHeaders['Authorization'] = auth

    for field in fieldList:
        FarmId = field.FarmId if field.FarmId is not None else ""
        FieldId = field.FieldId
        TargetDay = field.TargetDay

        urlBase = "https://app.nileworks.io/api/v1/mobile/agri/growths/?farm__id=farmreplace&field__id=fieldreplace&limit=32767"
        url = urlBase.replace('farmreplace', FarmId).replace('fieldreplace', FieldId)

        response = requests.get(url, headers=requestHeaders)

        if response.status_code != 200:
            continue

        body = response.json()

        meshes = []
        for i in range(len(body['results'])):

            #date_jst = datetime.datetime.strptime(body['results'][i]['analysisDate'],'%Y-%m-%d')
            date_jst = datetime.datetime.strptime(body['results'][i]['recordedAt'],'%Y-%m-%dT%H:%M:%S+09:00')

            '''
            if TargetDay is not None:
                print(date_jst.date(), TargetDay.date())
            '''

            if TargetDay is not None and date_jst.date() != TargetDay.date():
                continue

            mesh = [body['results'][i]['meshType'], date_jst, body['results'][i]['meshGeoJson']['summaryData']['summaryData001']]
            if checkVersion(body['results'][i]['meshGeoJson']['global']) > 104 :
                if 'calcuratedMeshes' in body['results'][i]['meshGeoJson']['summaryData']:
                    print(body['results'][i]['meshGeoJson']['global']['devVersion'])
                    mesh.append(body['results'][i]['meshGeoJson']['summaryData']['calcuratedMeshes'])
                else:
                    mesh.append(body['results'][i]['meshGeoJson']['summaryData']['calculatedMeshes'])
            else:
                mesh.append(len(body['results'][i]['meshGeoJson']['createdat']))

            uid = checkUpdate(meshes, mesh)
            if uid == -1:
                meshes.append(mesh)
            elif uid >= 0:
                meshes[uid] = mesh

        if TargetDay is not None and required and len(meshes) == 0:
            mesh = ['red_absorption', TargetDay, 'None', 0]
            meshes.append(mesh)
            mesh = ['effective_sun_ray_receiving_area_rate', TargetDay, 'None', 0]
            meshes.append(mesh)

        field.Meshes = meshes


def main():
    args = sys.argv

    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--csv', required=True, help='set csv file that is list of longitude and latitude, where you want to get weather data(required) \r\n')
    parser.add_argument('-o', '--output', required=True, help='specify the output directory (required)')
    parser.add_argument('-d', '--day', required=False, help='define the checking day')
    parser.add_argument('-t', '--token', required=False, default='.token', help='set the token file')
    args = parser.parse_args()

    if os.path.exists(args.csv):
        csvfile = open(args.csv, encoding="utf_8_sig")
        csvdata = list(csv.reader(csvfile))
    else:
        print('No specified csv file')
        sys.exit()

    requestHeaders = {'Accept': 'application/json'}

    with open('.token') as ft:
        auth = ft.read().strip()

    requestHeaders['Authorization'] = auth

    target_day = None
    if args.day is not None:
        target_day = datetime.datetime.strptime(args.day,'%Y-%m-%d').date()

    fieldList = []
    farmName = {}
    fieldName = {}

    for row in csvdata:
        if csvdata.index(row) == 0:
            continue

        field = fieldDat()
        field.FarmId = row[3]
        field.FieldId = row[4]
        field.TargetDay = target_day

        farmName[field.FieldId] = row[1]
        fieldName[field.FieldId] = row[2]

        fieldList.append(field)

    getGrowthData(auth, fieldList)

    results = []
    for field in fieldList:
        for mesh in field.Meshes:
#            dat = [farmName[field.FieldId], fieldName[field.FieldId], mesh[0], mesh[1].date().isoformat(), mesh[2]]
            dat = [farmName[field.FieldId], fieldName[field.FieldId], mesh[0], mesh[1].isoformat(), mesh[2]]
            results.append(dat)

    with open(args.output, 'w', encoding='utf_8_sig') as file:
        writer = csv.writer(file)
        writer.writerows(results)

if __name__ == '__main__' :
    import os
    import sys
    import argparse
    import csv
    main()
