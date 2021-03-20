import sys
import pandas as pd
from collections import defaultdict

sys.path.append('..')
import geojson_api_client.getGrowthData as gd

def insertMeshData(auth, df, fieldid):
    field_dat = gd.fieldDat()
    field_dat.FieldId = fieldid

    gd.getGrowthData(auth, [field_dat])
    print(field_dat.Meshes)

    nested_dict = lambda: defaultdict(nested_dict)
    mesh_hash = nested_dict()

    for mesh in field_dat.Meshes:
        #datelist.append(mesh[1].date().isoformat())
        result = mesh[2] if mesh[2] != '0.000' else 'ZERO'

        if mesh[0] == 'red_absorption':
            mesh_hash['T19RedAbsorptionRate'][mesh[1].date()] = result
        elif mesh[0] == 'effective_sun_ray_receiving_area_rate':
            mesh_hash['T19EffectiveSunRayReceivingAreaRate'][mesh[1].date()] = result
    print(mesh_hash)

    df.update(mesh_hash)

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

    insertMeshData(auth, df, jci['field']['id'])

    df.to_csv(args.output)

    sys.exit(0)

if __name__ == '__main__':
    _main()
