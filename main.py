from funcDefines import *
import confidential

DOWNLOADS       = "downloads/"
OUTPUT          = "output/"

C_DOWNLOAD_PARSE_CDEC   =   0 #False
C_VIZ_CDEC              =   1

if not os.path.exists(OUTPUT):
    os.mkdir(OUTPUT)

verbose = 0

TYPE = "SWE"
#define water years and basin of interest
basins = ["Feather"]
#get cdec sensors locations

wys = [2015, 2016, 2017]

if C_DOWNLOAD_PARSE_CDEC:
    for basin_name in basins:
        #download or load basin stations meta data
        basin_obj = cdec_get_basin_stations_meta(basin_name, TYPE, DOWNLOADS, debug = 0)
        if verbose: basin_obj.print_stations_info()
        #correct for imprecise lat lon
        correct_latlon(basin_obj, confidential.CDEC_CORRECTED_ID_LATLON)
        if verbose: basin_obj.print_stations_info()
        for wy in wys:
            # download or load data for each basin station and each water year of interest
            cdec_get_basin_stations_data(basin_obj, wy, DOWNLOADS + basin_name + "/", debug = 1)
            pass
        cPickle.dump(basin_obj, open( OUTPUT + basin_name + ".cPickle", "wb" ))

if C_VIZ_CDEC:
    for basin_name in basins:
        for wy in wys:
            basin_obj = cPickle.load(open(OUTPUT + basin_name + ".cPickle", "rb"))
            key_dt_val = basin_obj.get_stations_time_series_data(wy, only_pillows=True)
            for key in key_dt_val.keys():
                if key_dt_val[key] is not None:
                    plt.plot( key_dt_val[key][0], key_dt_val[key][1], label=key)
            plt.legend()
            plt.show()


