import os
import argparse
import re
import math
import pymap3d as pm
import numpy as np
import cv2
import json

from multiprocessing import Pool
import multiprocessing as multi

# Key assignment (change to suit your environment)
CVKEY_ESCAPE = 27

# Value steps for Mesh image adjustment (change to suit your computer's performance)
STEP_MAG   = 0.1
STEP_ANGLE = math.pi / 180.0
STEP_SCALE = 0.01

def getCustomColor(a, min, max):
    aa = (a/256.0-min)/(max-min)
    if aa<0: aa=0
    if aa>1: aa=1
    if a == 0:
        g = 0
        r = 0
    elif aa < 0.5:
        g = aa*2
        r = 1.0
    elif aa < 0.75:
        g = 1.0
        r = 1.0*(1.0-((aa-0.5)*4)*((aa-0.5)*4))
    else:
        g = 1.0 - (aa-0.75)*3
        r = 0
    return (0, (g*255), (r*255))

def getCustomColor2(a, min, max):
    (_r1, _g1, _b1) = (0.656, 0.813, 0.551)
    (_r2, _g2, _b2) = (0.108, 0.224, 0.069)
    aa = (a/256.0-min)/(max-min)
    if aa<0: aa=0
    if aa>1: aa=1
    if a == 0:
        r = 0.0
        g = 0.0
        b = 0.0
    elif aa < 0.5:
        r = 1.0 + (_r1 - 1.0) * aa*2
        g = 1.0 + (_g1 - 1.0) * aa*2
        b = 1.0 + (_b1 - 1.0) * aa*2
    else:
        r = _r1 + (_r2 - _r1) * (aa-0.5)*2
        g = _g1 + (_g2 - _g1) * (aa-0.5)*2
        b = _b1 + (_b2 - _b1) * (aa-0.5)*2
    return ((b*255), (g*255), (r*255))

def getCustomColor3(a, min, max):
    _r1 = 0.746
    _g1 = 0.558
    aa = (a/256.0-min)/(max-min)
    if aa<0: aa=0
    if aa>1: aa=1
    if a == 0:
        r = 0.0
        g = 0.0
        b = 0.0
    else:
        r = 1.0 - (1.0 - _r1) * aa
        g = 1.0 - (1.0 - _g1) * aa
        b = 1.0 - aa
    return ((b*255), (g*255), (r*255))

def colcode2bgr(c):
    return (int(c[5:7],16),int(c[1:3],16),int(c[3:5],16)) # bgr

def getCustomIntensity(a, min, max):
    aa = int((a/256.0-min)/(max-min) * 255)
    return (aa,aa,aa)

def dispCustomScale(color, inv, min, max, scale):
    yof = 16
    xof = 16
    img = np.zeros((64,288,3), np.uint8)
    for i in range(0,256):
        if inv:
            val = int(min*256 + (256-i)*(max-min) + 0.5)
        else:
            val = int(min*256 + i*(max-min) + 0.5)
        if color:
            if scale == 0:
                (r,g,b) = getCustomColor(val,min,max)
            elif scale == 1:
                (r,g,b) = getCustomColor2(val,min,max)
            else:
                (r,g,b) = getCustomColor3(val,min,max)
            cv2.line(img, (xof+i,yof+8), (xof+i,yof+28), (r,g,b), 1, 4)
        else:
            cv2.line(img, (xof+i,yof+8), (xof+i,yof+28), getCustomIntensity(val,min,max), 1, 4)

    cv2.rectangle(img, (xof    ,yof+8), (xof+256,yof+28), (255,255,255), 1, 4)
    cv2.line     (img, (xof    ,yof+4), (xof    ,yof+32), (255,255,255), 1, 4)
    cv2.line     (img, (xof+ 64,yof+4), (xof+ 64,yof+32), (255,255,255), 1, 4)
    cv2.line     (img, (xof+128,yof+4), (xof+128,yof+32), (255,255,255), 1, 4)
    cv2.line     (img, (xof+192,yof+4), (xof+192,yof+32), (255,255,255), 1, 4)
    cv2.line     (img, (xof+256,yof+4), (xof+256,yof+32), (255,255,255), 1, 4)
    if scale == 2: numstr = "%d" % (int(min*1000+0.5))
    else         : numstr = "%.2f" % (min+0.001)
    cv2.putText(img, numstr, (xof-12 , yof), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255))
    if scale == 2: numstr = "%d" % (int((max+min)*500+0.5))
    else         : numstr = "%.2f" % ((max+min)/2+0.001)
    cv2.putText(img, numstr, (xof+112, yof), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255))
    if scale == 2: numstr = "%d" % (int(max*1000+0.5))
    else         : numstr = "%.2f" % (max+0.001)
    cv2.putText(img, numstr, (xof+232, yof), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255,255,255))
    return img

def help():
	print("======================================")
	print("1/2 : angle +(2)/-(1)")
	print("3/4 : zoom +(4)/-(3)")
	print("5/6 : Adjust min color scale +(6)/-(5)")
	print("7/8 : Adjust max color scale +(8)/-(7)")
	print("C   : Change color/mono")
	print("G   : Grid on/off")
	print("H   : Show this message")
	print("I   : Invert of value")
	print("M   : Display Mesh properties")
	print("R   : Reset all")
	print("S   : Save an image")
	print("Z   : Select Color Scale")
	print("Q   : Quit")

def readGeoJson(jsondict, index, value, status, vn, ve):
    # analyze geojson file
    #print("jsondict:{}".format(jsondict))
    #jsonstr  = json.dumps(jsondict)
    #print("jsonstr :{}".format(jsonstr))
    if("global"      in jsondict): print("global     :",jsondict["global"])
    if("survey"      in jsondict): print("survey     :",jsondict["survey"])
    if("mission"     in jsondict): print("mission    :",jsondict["mission"])
    if("flightGroup" in jsondict): print("flightGroup:",jsondict["flightGroup"])
    if("createdat"   in jsondict): print("createdat  :",jsondict["createdat"])
    if("summaryData" in jsondict): print("summaryData:",jsondict["summaryData"])
    '''
    index = []
    value = []
    status = []
    #color = []
    vn = []
    ve = []
    '''
    firstllh = 1
    for i in jsondict["features"]:
        #jcol = i["properties"]["fillColor"]
        #color.append(colcode2bgr(jcol))
        jidx = i["properties"]["meshId"]
        index.append(int(jidx))
        jval = i["properties"]["value"]
        value.append(int(jval))
        if("status" in i["properties"]):
            jsta = i["properties"]["status"]
            status.append(jsta)
        else:
            status.append("")
        jvtx = i["geometry"]["coordinates"]
        for j in jvtx[0]:
            if(firstllh):
                baselat = j[1]
                baselon = j[0]
                basealt = 0.0
                #print(baselat,baselon,basealt)
                firstllh = 0
            #vlat.append(j[1])
            #vlon.append(j[0])
            x,y,z = pm.geodetic2ecef(j[1],j[0],basealt)
            n,e,d = pm.ecef2ned(x,y,z,baselat,baselon,basealt)
            vn.append(n)
            ve.append(e)

    print("Detected %d meshes" % (len(value)))

def drawMesh(title, value, index, status, vn, ve,
             margin, col, inv, grid, val_min, val_max,
             mag, ang, scale, minfo, isSave=False):
    # get field size & image size
    tvn = [0] * len(vn)
    tve = [0] * len(vn)
    for i in range(0,len(vn)):
        tve[i] = ve[i] * math.cos(ang) + vn[i] * math.sin(ang)
        tvn[i] = ve[i] * math.sin(ang) - vn[i] * math.cos(ang)

    xmin, xmax = min(tve), max(tve)
    ymin, ymax = min(tvn), max(tvn)
    x_size = xmax - xmin
    y_size = ymax - ymin
    width = int(x_size * mag + margin * 2)
    height = int(y_size * mag + margin * 2)
    img = np.zeros((height,width,3), np.uint8)

    # draw meshes
    pts = np.empty((4,2), int)
    for i in range(0,len(value)):
        cx = 0
        cy = 0
        for j in range(0,4):
            pts[j] = np.array([[int((tve[i*5+j]-xmin)*mag)+margin, int((tvn[i*5+j]-ymin)*mag)+margin]])
            cx = cx + pts[j,0]
            cy = cy + pts[j,1]
        cx = int(cx / 4 + 0.5)
        cy = int(cy / 4 + 0.5)+2
        if value[i] == 0:
            val = 0
        else:
            if inv:
                val = int((65536 - value[i])/256)
            else:
                val = int(value[i]/256)
        if col:
            if scale == 0:
                (b,g,r) = getCustomColor(val,val_min,val_max)
            elif scale == 1:
                (b,g,r) = getCustomColor2(val,val_min,val_max)
            else:
                (b,g,r) = getCustomColor3(val,val_min,val_max)
            cv2.fillPoly(img, [pts], (b,g,r))
        else:
            cv2.fillPoly(img, [pts], getCustomIntensity(val,val_min,val_max))
        if grid:
            cv2.polylines(img, [pts], True, (96,96,96))
        if minfo == 1:
            mstr = "%d" % (index[i])
            cv2.putText(img, mstr, (cx-len(mstr)*4,cy), cv2.FONT_HERSHEY_DUPLEX, 0.2+mag/50, (255,0,0))
        elif minfo == 2:
            mstr = "%d" % (val)
            cv2.putText(img, mstr, (cx-len(mstr)*4,cy), cv2.FONT_HERSHEY_DUPLEX, 0.2+mag/50, (255,0,0))
        elif minfo == 3:
            if status[i] == "normal":
                mstr = "N"
            elif status[i] == "empty":
                mstr = "E"
            else:
                if len(status[i]) < 15:
                    mstr = ""
                else:
                    mstr = "i" + status[i][14]
            cv2.putText(img, mstr, (cx-len(mstr)*4,cy), cv2.FONT_HERSHEY_DUPLEX, 0.3+mag/50, (255,0,0))

    cv2.imshow(title, img)
    cv2.imshow("Scale:"+title, dispCustomScale(col, inv, val_min, val_max, scale))
    if isSave:
        cv2.imwrite(title+".png", img)
        #cv2.imwrite(title+"_scale.png", dispCustomScale(col, inv, val_min, val_max, scale))


def main(filepath):

    tmpname = os.path.basename(filepath)
    filename, ext = os.path.splitext(tmpname)

    index = []
    value = []
    status = []
    vn = []
    ve = []

    jsonpath = open(filepath, "r")
    jsondict = json.load(jsonpath)

    readGeoJson(jsondict, index, value, status, vn, ve)

    '''
    # analyze geojson file
    jsonpath = open(filepath, "r")
    jsondict = json.load(jsonpath)
    #print("jsondict:{}".format(jsondict))
    #jsonstr  = json.dumps(jsondict)
    #print("jsonstr :{}".format(jsonstr))
    if("global"      in jsondict): print("global     :",jsondict["global"])
    if("survey"      in jsondict): print("survey     :",jsondict["survey"])
    if("mission"     in jsondict): print("mission    :",jsondict["mission"])
    if("flightGroup" in jsondict): print("flightGroup:",jsondict["flightGroup"])
    if("createdat"   in jsondict): print("createdat  :",jsondict["createdat"])
    if("summaryData" in jsondict): print("summaryData:",jsondict["summaryData"])
    index = []
    value = []
    status = []
    #color = []
    vn = []
    ve = []
    firstllh = 1
    for i in jsondict["features"]:
        #jcol = i["properties"]["fillColor"]
        #color.append(colcode2bgr(jcol))
        jidx = i["properties"]["meshId"]
        index.append(int(jidx))
        jval = i["properties"]["value"]
        value.append(int(jval))
        if("status" in i["properties"]):
            jsta = i["properties"]["status"]
            status.append(jsta)
        else:
            status.append("")
        jvtx = i["geometry"]["coordinates"]
        for j in jvtx[0]:
            if(firstllh):
                baselat = j[1]
                baselon = j[0]
                basealt = 0.0
                #print(baselat,baselon,basealt)
                firstllh = 0
            #vlat.append(j[1])
            #vlon.append(j[0])
            x,y,z = pm.geodetic2ecef(j[1],j[0],basealt)
            n,e,d = pm.ecef2ned(x,y,z,baselat,baselon,basealt)
            vn.append(n)
            ve.append(e)
    print("Detected %d meshes" % (len(value)))
    '''

    # initialize parameters
    margin = 16
    col = 1
    inv = 0
    grid = 1
    val_min = 0.0
    val_max = 1.0
    mag = 10.0
    ang = 0
    scale = 0
    minfo = 0

    help()
    while(1):
        drawMesh(filename, value, index, status, vn, ve,
                 margin, col, inv, grid, val_min, val_max,
                 mag, ang, scale, minfo)
        '''
        # get field size & image size
        tvn = [0] * len(vn)
        tve = [0] * len(vn)
        for i in range(0,len(vn)):
            tve[i] = ve[i] * math.cos(ang) + vn[i] * math.sin(ang)
            tvn[i] = ve[i] * math.sin(ang) - vn[i] * math.cos(ang)

        xmin, xmax = min(tve), max(tve)
        ymin, ymax = min(tvn), max(tvn)
        x_size = xmax - xmin
        y_size = ymax - ymin
        width = int(x_size * mag + margin * 2)
        height = int(y_size * mag + margin * 2)
        img = np.zeros((height,width,3), np.uint8)

        # draw meshes
        pts = np.empty((4,2), int)
        for i in range(0,len(value)):
            cx = 0
            cy = 0
            for j in range(0,4):
                pts[j] = np.array([[int((tve[i*5+j]-xmin)*mag)+margin, int((tvn[i*5+j]-ymin)*mag)+margin]])
                cx = cx + pts[j,0]
                cy = cy + pts[j,1]
            cx = int(cx / 4 + 0.5)
            cy = int(cy / 4 + 0.5)+2
            if value[i] == 0:
                val = 0
            else:
                if inv:
                    val = int((65536 - value[i])/256)
                else:
                    val = int(value[i]/256)
            if col:
                if scale == 0:
                    (b,g,r) = getCustomColor(val,val_min,val_max)
                elif scale == 1:
                    (b,g,r) = getCustomColor2(val,val_min,val_max)
                else:
                    (b,g,r) = getCustomColor3(val,val_min,val_max)
                cv2.fillPoly(img, [pts], (b,g,r))
            else:
                cv2.fillPoly(img, [pts], getCustomIntensity(val,val_min,val_max))
            if grid:
                cv2.polylines(img, [pts], True, (96,96,96))
            if minfo == 1:
                mstr = "%d" % (index[i])
                cv2.putText(img, mstr, (cx-len(mstr)*4,cy), cv2.FONT_HERSHEY_DUPLEX, 0.2+mag/50, (255,0,0))
            elif minfo == 2:
                mstr = "%d" % (val)
                cv2.putText(img, mstr, (cx-len(mstr)*4,cy), cv2.FONT_HERSHEY_DUPLEX, 0.2+mag/50, (255,0,0))
            elif minfo == 3:
                if status[i] == "normal":
                    mstr = "N"
                elif status[i] == "empty":
                    mstr = "E"
                else:
                    if len(status[i]) < 15:
                        mstr = ""
                    else:
                        mstr = "i" + status[i][14]
                cv2.putText(img, mstr, (cx-len(mstr)*4,cy), cv2.FONT_HERSHEY_DUPLEX, 0.3+mag/50, (255,0,0))

        cv2.imshow(filename,img)
        cv2.imshow("Scale:"+filename,dispCustomScale(col, inv, val_min, val_max, scale))
        '''
        # user operations
        key = cv2.waitKey(0)

        if key == ord('1'):
            mag = mag - STEP_MAG if mag > STEP_MAG else mag
        elif key == ord('2'):
            mag = mag + STEP_MAG
        elif key == ord('3'):
            ang = ang - STEP_ANGLE
        elif key == ord('4'):
            ang = ang + STEP_ANGLE
        elif key == ord('5'):
            val_min = val_min - STEP_SCALE if val_min > 0.0 else val_min
        elif key == ord('6'):
            val_min = val_min + STEP_SCALE if val_min < val_max else val_min
        elif key == ord('7'):
            val_max = val_max - STEP_SCALE if val_max > val_min else val_max
        elif key == ord('8'):
            val_max = val_max + STEP_SCALE if val_max < 1.0 else val_max
        elif key == ord('c'):
            col = col ^ 1
        elif key == ord('g'):
            grid = grid ^ 1
        elif key == ord('h'):
            help()
        elif key == ord('i'):
            inv = inv ^ 1
        elif key == ord('m'):
            minfo = minfo + 1 if minfo < 3 else 0
            if   minfo==1: print("Display Mesh ID")
            elif minfo==2: print("Display Mesh 8bit-Value")
            elif minfo==3: print("Display Mesh status(Normal/Empty/Interpolation)")
        elif key == ord('r'):
            col = 1
            inv = 0
            grid = 1
            val_min = 0.0
            val_max = 1.0
            mag = 10.0
            ang = 0
            scale = 0
            minfo = 0
        elif key == ord('s'):
            cv2.imwrite("_meshimage.png",img)
            cv2.imwrite("_scale.png",dispCustomScale(col, inv, val_min, val_max, scale))
            print("Write: _meshimage.png, _scale.png")
        elif key == ord('z'):
            scale = scale + 1 if scale < 2 else 0

        elif key == ord('q') or key == CVKEY_ESCAPE:
            break

    cv2.destroyAllWindows()
    quit()

if __name__ == '__main__' :
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str, nargs='+')
    args = parser.parse_args()

    fnum = len(args.filename)
    #print(fnum)

    if fnum == 1:
        main(args.filename[0])
    else:
        #p = Pool(multi.cpu_count())
        p = Pool(fnum)
        p.map(main, args.filename)
        p.close()

    quit()
