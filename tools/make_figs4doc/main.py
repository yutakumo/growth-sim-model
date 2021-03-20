import sys
import requests
import json
import pandas as pd

import drawmesh2019 as dm
import gsm_drawer as gsmd

def getGeojsons(auth, fieldid):
    requestHeaders = {'Accept': 'application/json'}
    requestHeaders['Authorization'] = auth

    urlBase = "https://app.nileworks.io/api/v1/mobile/agri/growths/?field__id=fieldreplace&limit=32767"
    url = urlBase.replace('fieldreplace', fieldid)

    response = requests.get(url, headers=requestHeaders)

    body = []
    if response.status_code == 200:
        body = response.json()

    return body

def writeMeshData(auth, fieldid, fieldname):

    print(fieldid)
    geojsons = getGeojsons(auth, fieldid)
    if len(geojsons) == 0 :
        return

    for i in range(len(geojsons['results'])):

        mesh = geojsons['results'][i]

        index = []
        value = []
        status = []
        vn = []
        ve = []

        dm.readGeoJson(mesh['meshGeoJson'], index, value, status, vn, ve)
        margin = 16
        col = 1
        inv = 0
        grid = 1
        val_max = 1.0
        mag = 10.0
        ang = 0
        minfo = 0
        if mesh['meshType'] == 'red_absorption':
            val_min = 0.4
            scale = 0
            kindname = '_red_'

        elif mesh['meshType'] == 'effective_sun_ray_receiving_area_rate':
            val_min = 0.0
            scale = 1
            kindname = '_esrrar_'
        elif mesh['meshType'] == 'volume_of_crops':
            val_min = 0.0
            scale = 2
            kindname = '_crops_'
        else:
            continue

        filename = fieldname + kindname + mesh['recordedAt']
        dm.drawMesh(filename, value, index, status, vn, ve,
                    margin, col, inv, grid, val_min, val_max,
                    mag, ang, scale, minfo, True)


def _main():
    import os
    import argparse
    import json

    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--database', required=True,
                        help='path of input database')
    parser.add_argument('-o', '--output', required=True,
                        help='path of output database')
    parser.add_argument('-ci', '--commoninfo', required=True,
                        help='path of growth planning information file')
    parser.add_argument('-l', '--label', required=True,
                        help='')
    parser.add_argument('-t', '--token', required=False, default='.token',
                        help='set the token file')

    args = parser.parse_args()

    if os.path.isfile(args.database) == False :
        print("ERROR: no input database")
        sys.exit(1)
    else:
        df = pd.read_csv(args.database, parse_dates=True, index_col='Date')

    with open(args.commoninfo) as fci:
        jci = json.load(fci)
        fci.close()

    requestHeaders = {'Accept': 'application/json'}

    with open(args.token) as ft:
        auth = ft.read().strip()

    requestHeaders['Authorization'] = auth

    output = args.output + "/" + jci['field']['name']
    writeMeshData(auth, jci['field']['id'], output)

    _plant_method = {'direct_sowing': 'sowing_date', 'transplantation': 'transplanting_date'}
    plant_method = _plant_method[jci['planting']['method']]
    sdate = jci['schedule'][plant_method]['date']
    edate = jci['schedule']['reaping_date']['date']

    drawlist = "./temper_draw.json"
    output = args.output + "/" + jci['field']['name'] + "_temper.png"
    gsmd.gsm_draw(sdate, edate, df, drawlist, output, args.label)

    drawlist = "./nitro_sup_draw.json"
    output = args.output + "/" + jci['field']['name'] + "_nit_sup.png"
    gsmd.gsm_draw(sdate, edate, df, drawlist, output, args.label)

    drawlist = "./growth_draw.json"
    output = args.output + "/" + jci['field']['name'] + "_growth.png"
    gsmd.gsm_draw(sdate, edate, df, drawlist, output, args.label)

    drawlist = "./sucrose_draw.json"
    output = args.output + "/" + jci['field']['name'] + "_sucrose.png"
    gsmd.gsm_draw(sdate, edate, df, drawlist, output, args.label)

    drawlist = "./sucrose_dist_draw.json"
    output = args.output + "/" + jci['field']['name'] + "_sucrose_dist.png"
    gsmd.gsm_draw(sdate, edate, df, drawlist, output, args.label)

    drawlist = "./nitro_dist_draw.json"
    output = args.output + "/" + jci['field']['name'] + "_nitor_dist.png"
    gsmd.gsm_draw(sdate, edate, df, drawlist, output, args.label)

    sys.exit(0)

if __name__ == '__main__':
    _main()
