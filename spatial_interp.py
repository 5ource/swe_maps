from imports import *
from funcDefines import *
from reduce_theo import reduce_ens
from settings import *
from confidential import *

import gdal

CONSTANTS = {
    "Margulis SWE Year Range"   :   [1985, 2016],
    "Margulis FCA Year Range"   :   []
}

PATHS = {
    "Feather Margulis SWE tif SER": "/media/raid0/zeshi/sn_reanalysis/data/processed_by_basin/feather/SWE/",
    "Feather Margulis SWE h5": "/Volumes/Untitled/zeshi/SWE/",
    "Feather Margulis SWE": "/Volumes/Untitled/feather/SWE/",
}

def add_years(d, years):
    """Return a date that's `years` years after the date (or datetime)
    object `d`. Return the same calendar date (month and day) in the
    destination year, if it exists, otherwise use the following day
    (thus changing February 29 to March 1).

    """
    try:
        return d.replace(year = d.year + years)
    except ValueError:
        return d + (dt.date(d.year + years, 1, 1) - dt.date(d.year, 1, 1))


C_GENERATE_STATIC_ENS = 0

if C_GENERATE_STATIC_ENS:
    fromDate = dt.date(CONSTANTS["Margulis SWE Year Range"][0] - 1, 5, 1)
    fromDate = fromDate.replace(year=2012)
    toDate = dt.date(CONSTANTS["Margulis SWE Year Range"][1], 10, 1)
    toDate = toDate.replace(year=2016)
    #src_swe_path =  PATHS["Feather Margulis SWE tif SER"]
    src_swe_path = PATHS["Feather Margulis SWE"]
    reduced_Path = "./testEns.npy"
    save_Ens_Margulis_fast(fromDate, toDate, src_swe_path, reduced_Path,
                      Years=None, debug=0, reduce=1, modis=0)

C_GEN_MAPS = 1

if C_GEN_MAPS:
    for basin_name in basins:
        # specify pillow IDS of interest
        PILLOW_IDS_OF_INTEREST    = ["BKL", "FOR", "GRZ", "HMB", "HRK", "KTL", "PLP", "RTL"]
        pillow_ids = PILLOW_IDS_OF_INTEREST

        #load basin obs
        basin_obj = cPickle.load(open(OUTPUT + basin_name + ".cPickle", "rb"))

        # filter gaps and negatives
        C_FILTER = 1
        if C_FILTER:
            basin_obj.bound_stations_data()

            #special intervention for FOR
            fromd   = dt.date(2017, 3, 27)
            tod     = dt.date(2017, 5, 12)
            while fromd < tod:
                basin_obj.stations["FOR"].data[2017][fromd] = np.nan
                fromd += dt.timedelta(days = 1)
            basin_obj.stations["FOR"].data[2017][fromd] = 0.0
            basin_obj.fill_stations_data_gap_linear()

        #visualize data
        if 0: basin_obj.show_stations_data(wys, station_ids=pillow_ids, show=True)

        # generate pillow rc locations of IDS
        ds = gdal.Open(PATHS["Feather Margulis SWE"] + "2016/20160401.tif")
        sample_map = ds.GetRasterBand(1).ReadAsArray()
        R, C = np.shape(sample_map)
        rcs = basin_obj.get_stations_rcs(ds, station_ids=pillow_ids)
        if 0: print rcs
        #alpha training

        # load static ensemble readonly
        static_ens = np.load("/Volumes/Untitled/testEns.npy", mmap_mode="r")
        print np.shape(static_ens)
        # 993525 x 100      #refill the invalid parts to preserve observation locations
        static_ens = np.transpose(static_ens)
        # load reference
        mask = ~np.logical_or(sample_map < 0, np.isnan(sample_map))
        lin_mask = mask.flatten()
        new_hist_ens = []
        for ens in static_ens:
            contain = -999 * np.ones(np.shape(lin_mask))
            contain[lin_mask] = ens
            new_hist_ens.append(contain)
        static_ens = np.transpose(new_hist_ens)
        print "static_ens shape = ", np.shape(static_ens)

        HIST_ENS_VISU = 0   #todo for paper
        if HIST_ENS_VISU:
            # id = 30
            # print "shpe, test = ", np.shape(hist_ens[id,:]), hist_ens[id,:]
            # exit(0)
            visualize_corr(static_ens, rcs[0], R, C)
            exit(0)

        if 0:   #plot map and sensors
            basin_obj.overlay_stations(ds, pillow_ids)

        rowsThresh = 100
        # delete compressed file
        # clear_output(OUTPUT_PATH)   #deletes all compressed files
        try:
            os.remove(OUTPUT + "menoi" + str(len(rcs)) + "_blosc.h5")
        except:
            pass
        rows = np.empty([0, 3 + R * C])

        for wy in wys:
            start_date = dt.date(wy-1,  month=10, day=1)
            end_date   = dt.date(wy,    month=10, day=1)
            d = start_date + dt.timedelta(days=30*3)
            while d < end_date:
                # 1. get observations
                obs = basin_obj.get_measurements(d, pillow_ids)
                obs = np.array(obs)
                print d, obs
                # 2. train optimal alpha
                MEnOI = predict_SWE_map(obs, rcs, static_ens, R, C, v=1)

                MEnOI[MEnOI < 0] = 0
                plt.imshow(MEnOI)
                plt.show()


                rows = save_compressed_output(rows, d, MEnOI, "menoi" + str(len(rcs)), OUTPUT,
                                              rowsThresh=rowsThresh, expectedrows=365*3, comp=1, v=0)
                # 3. assimilate with obtained alpha
                d += dt.timedelta(days=1)
