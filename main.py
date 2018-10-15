from funcDefines import *
import confidential

DOWNLOADS = "downloads/"

verbose = 0

TYPE = "SWE"
#define water years and basin of interest
basins = ["Feather"]
#get cdec sensors locations

wys = [2015, 2016, 2017]

for basin_name in basins:
    #download or load basin stations meta data
    basin_obj = cdec_get_basin_stations_meta(basin_name, TYPE, DOWNLOADS, debug = 0)
    if verbose: basin_obj.print_stations_info()
    #correct for imprecise lat lon
    correct_latlon(basin_obj, confidential.CDEC_CORRECTED_ID_LATLON)
    if verbose: basin_obj.print_stations_info()
    for wy in wys:
        cdec_get_basin_stations_data(basin_obj, wy, DOWNLOADS + basin_name + "/", debug = 1)
        #download or load data for each basin station and each water year of interest
        pass


