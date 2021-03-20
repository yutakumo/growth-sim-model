import os
import sys
import requests
import argparse
import csv
import json
import datetime
from pytz import timezone

def main():
    args = sys.argv

    parser = argparse.ArgumentParser(
        prog='halex_api_client.py -o <output directory> -c <target field csv file> ..',
        usage="python(3) %s -o <output directory> -c <target field csv file>" % args[0],
        description='under construction',
        add_help=True,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument('-c', '--csv', required=True, help='set csv file that is list of longitude and latitude, where you want to get weather data(required) \r\n')
    parser.add_argument('-o', '--output', required=True, help='specify the output directory (required)')
    parser.add_argument('-s', '--suffix', required=False, help='set suffix of output file name')
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


    if args.day is not None:
        checking_day = datetime.datetime.strptime(args.day,'%Y-%m-%d').date()

    meshes = []

    for row in csvdata:
        if csvdata.index(row) == 0:
            continue

        farmId = row[3]
        fieldId = row[4]

        urlBase = "https://app.nileworks.io/api/v1/mobile/agri/growths/?farm__id=farmreplace&field__id=fieldreplace&limit=200"

        url = urlBase.replace('farmreplace', farmId).replace('fieldreplace', fieldId)

        response = requests.get(url, headers=requestHeaders)

        if response.status_code != 200:
            continue

        body = response.json()

        if args.suffix:
            suffix = "_" + args.suffix
        else:
            suffix = ""

        farmName = row[1]
        fieldName = row[2]

        fileNameBase = "farmreplace_fieldreplace" + suffix + ".json"
        fileName = fileNameBase.replace('farmreplace', farmName).replace('fieldreplace', fieldName)

        if len(body['results']) == 0 and args.day is None:
            print(farmName, ',', fieldName, ',No-Data')
            mesh = [farmName, fieldName, 'No-Data', '00-00-00 00:00:00', 0.0]
            meshes.append(mesh)

        for i in range(len(body['results'])):

            #date_st = body['results'][i]['meshGeoJson']['createdat'][0]
            #date_st_iso = date_st.replace('+0000', '+00:00')
            #date_utc = datetime.datetime.fromisoformat(date_st_iso)
            #date_jst = date_utc.astimezone(timezone('Asia/Tokyo'))

            date_jst = datetime.datetime.strptime(body['results'][i]['analysisDate'],'%Y-%m-%d')
            if args.day is not None and date_jst.day != checking_day.day:
                continue

            print(farmName,
                  ',', fieldName,
                  ',', body['results'][i]['meshType'],
                  #body['results'][i]['meshGeoJson']['createdat'][0], body['results'][i]['created'],
                  ',', date_jst,
                  ',', body['results'][i]['meshGeoJson']['summaryData']['summaryData001'])
            mesh = [farmName, fieldName, body['results'][i]['meshType'], date_jst, body['results'][i]['meshGeoJson']['summaryData']['summaryData001']]
            meshes.append(mesh)

    #with open(args.outdir + "/" + fileName, 'w', encoding="utf-8" ) as file:
    #json.dump(body, file, indent=4)

    with open(args.output, 'w', encoding='utf_8_sig') as file:
        writer = csv.writer(file)
        writer.writerows(meshes)

    sys.exit()

if __name__ == '__main__' : main()
