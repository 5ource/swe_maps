from imports import *

verbose = 0

TYPE = "SWE"
#define water years and basin of interest
basins = ["Feather"]
#get cdec sensors locations

#wys = [2015, 2016, 2017]
wys = [2015, 2016, 2017]

TRAIN_ALPHAS = [0, 0.0001, 0.001, 0.5, 1]

DOWNLOADS       = "downloads/"
OUTPUT          = "output/"

if not os.path.exists(OUTPUT):
    os.mkdir(OUTPUT)


#interpolation
PERCENT_OBS_STD = 0.01
rowsThresh      = 100
TRUNCATION      = 0.999
MODE            = 12



CDEC_SENSOR_TYPES = {
    "SNOW DEPTH"            :   18,
    "SNOW, WATER CONTENT"   :   3,
    "SWE"                   :   3,
    "SD"                    :   18
}

CDEC_RIVER_BASIN = {
    "Feather"   :   "FEATHER+R",
    "American"  :   "AMERICAN+R",
    "Tuolumne"  :   "TUOLUMNE+R"
}
