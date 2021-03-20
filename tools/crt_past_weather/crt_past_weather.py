import argparse
import pandas as pd

parser = argparse.ArgumentParser()

parser.add_argument('-hx', '--halex', required=True)
parser.add_argument('-ma', '--meterological_agency', required=True)
parser.add_argument('-o', '--out', required=True)

args = parser.parse_args()

kdf = pd.read_csv(args.meterological_agency, skiprows=[0,1,2,3,4,5], usecols=[0,8,11], index_col=[0], header=None, parse_dates=True, names=["DateTime", "sr", "hu"])

hdf = pd.read_csv(args.halex, index_col=[0], parse_dates=True)

df = pd.concat([kdf,hdf], axis=1, join='inner')


period = int(df.index.size/24)
outList = [['Date', 'DaytimeTemperature', 'NighttimeTemperature', 'Rainfall', 'Humidity', 'SolarRadiation']]
for i in range(period-1):
    yd = df[df.index[i*24]:df.index[i*24+47]]

    status = 0
    lastnightIndex, morningIndex, nightIndex = 0, 0, 0
    for j in range(yd.index.size-1):
        #print('DEBUG:', yd.index[j], status, yd.loc[yd.index[j],'sr'], yd.loc[yd.index[j+1],'sr'])
        if status == 0 and yd.loc[yd.index[j],'sr'] > 0 and yd.loc[yd.index[j+1],'sr'] > 0:
            status = 1
        elif status == 1 and yd.loc[yd.index[j],'sr'] == 0 and yd.loc[yd.index[j+1],'sr'] == 0:
            lastnightIndex = j
            status = 2
        elif status == 2 and yd.loc[yd.index[j],'sr'] > 0 and yd.loc[yd.index[j+1],'sr'] > 0:
            morningIndex = j
            status = 3
        elif status == 3 and yd.loc[yd.index[j],'sr'] == 0 and yd.loc[yd.index[j+1],'sr'] == 0:
            nightIndex = j
            break

    #print(yd.index[lastnightIndex], yd.index[morningIndex], yd.index[nightIndex])
    ndf = yd[lastnightIndex:morningIndex]
    ddf = yd[morningIndex:nightIndex]
    tdf = yd[24:48]

    #print(ndf)
    #print(ddf)
    #print(tdf)

    nighttemper = ndf['tempr'].mean()
    datetemper = ddf['tempr'].mean()
    sr = ddf['sr'].sum()
    rain = tdf['1hpre'].sum()
    hu = tdf['hu'].mean()

    dList = []
    dList.append(yd.index[27].date())
    dList.append('{:4.2f}'.format(datetemper))
    dList.append('{:4.2f}'.format(nighttemper))
    dList.append('{:3.1f}'.format(rain))
    dList.append('{:2.0f}'.format(hu))
    dList.append('{:4.2f}'.format(sr))

    outList.append(dList)

_odf = pd.DataFrame(outList[1:], columns=outList[0])
odf = _odf.set_index('Date')

print(odf)

odf.to_csv(args.out, sep=',')
