from imports import *
from funcDefines import *
from reduce_theo import reduce_ens
from settings import *
from confidential import *

IN_2_MM = 25.4

C_FILTER                = 1
C_PILLOWS_ONLY          = 0
C_GENERATE_MAPS         = 1
C_INTER_TEMP_COURSES    = 1
C_GENERATE_STATIC_TEMPORAL_ENS  =   1
#   VIZ_DATA_EXIT           = 0
C_GENERATE_STATIC_ENS   = 0
C_TEST                  = 1
C_RETRIEVE_MAPS         = 0         #retrives them from hsoc to WY/date.tif

C_VISU_MAPS             = 1

if C_TEST:
    RET_FROM_DIR            = OUTPUT #"/Volumes/Untitled/swe_maps/output/"# OUTPUT    #no more space
    RET_TO_DIR              = OUTPUT #"/Volumes/Untitled/swe_maps/output/" #OUTPUT
    VIZ_DIR                 = OUTPUT  #OUTPUT #"/Volumes/Untitled/swe_maps/output/" #OUTPUT
else:
    RET_FROM_DIR            = EXT_OUTPUT #"/Volumes/Untitled/swe_maps/output/"# OUTPUT    #no more space
    RET_TO_DIR              = EXT_OUTPUT #"/Volumes/Untitled/swe_maps/output/" #OUTPUT
    VIZ_DIR                 = EXT_OUTPUT

CONSTANTS = {
    "Margulis SWE Year Range"   :   [1985, 2016],
    "Margulis FCA Year Range"   :   []
}

PATHS = {
    "Feather Margulis SWE": MARG_SWE_PATH
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

def save_metrics_2_csv(d_Basinmean_cverror, dest):
    with open(dest, 'wb') as file:
        file.write("date, basin SWE mean (mm), CV error pillows (mm)\n")
        for d_mean_cve in d_Basinmean_cverror:
            d = fromTS(d_mean_cve[0])
            Basinmean = d_mean_cve[1]
            cve     = d_mean_cve[2]
            file.write(str(d) + "," + str(Basinmean) + "," + str(cve)+"\n")

if C_GENERATE_MAPS:
    if C_GENERATE_STATIC_ENS:
        fromDate = dt.date(CONSTANTS["Margulis SWE Year Range"][0] - 1, 5, 1)
        fromDate = fromDate.replace(year=2012)
        toDate = dt.date(CONSTANTS["Margulis SWE Year Range"][1], 10, 1)
        toDate = toDate.replace(year=2016)
        #src_swe_path =  PATHS["Feather Margulis SWE tif SER"]
        src_swe_path = PATHS["Feather Margulis SWE"]
        reduced_Path = STATIC_ENS_PATH
        save_Ens_Margulis_fast(fromDate, toDate, src_swe_path, reduced_Path,
                          Years=None, debug=0, reduce=1, modis=0)

    for basin_name in basins:
        #load basin obs
        basin_obj = cPickle.load(open(OUTPUT + basin_name + ".cPickle", "rb"))

        # specify pillow IDS of interest
        PILLOW_IDS_OF_INTEREST = ["BKL", "FOR", "GRZ", "HMB", "HRK", "KTL", "PLP", "RTL"]
        #pillow_ids = PILLOW_IDS_OF_INTEREST

        if not C_PILLOWS_ONLY:
            # find stations in bound of map area
            ds = gdal.Open(PATHS["Feather Margulis SWE"] + "2016/20160401.tif")
            # sample_map = ds.GetRasterBand(1).ReadAsArray()
            active_inbound_sta = basin_obj.get_stations_in_bound(ds, activeOnly=True, noVal=-999)
            if 1:
                print active_inbound_sta
                print basin_obj.get_stations_ids()
                # basin_obj.show_stations_data(wys, station_ids=active_inbound_sta, show=True)
                # checking the difference
                # exit(0)

        if C_PILLOWS_ONLY:
            station_ids_of_interest = PILLOW_IDS_OF_INTEREST
        else:
            station_ids_of_interest = active_inbound_sta

        # generate pillow rc locations of IDS
        ds = gdal.Open(PATHS["Feather Margulis SWE"] + "2016/20160401.tif")
        sample_map = ds.GetRasterBand(1).ReadAsArray()
        R, C = np.shape(sample_map)
        rcs = basin_obj.get_stations_rcs(ds, station_ids=station_ids_of_interest)

        #if 1: print rcs

        if C_GENERATE_STATIC_TEMPORAL_ENS:
            fromDate = dt.date(CONSTANTS["Margulis SWE Year Range"][0] - 1, 10, 1)
            toDate = dt.date(CONSTANTS["Margulis SWE Year Range"][1], 10, 1)
            src_swe_path = PATHS["Feather Margulis SWE"]
            reduced_Path = STATIC_TENS_PATH
            save_Ens_Margulis_temporal(fromDate, toDate, src_swe_path, reduced_Path, rcs)
            #   rc1_SWE_365_days \  rc2_SWE_365_days \ ...
            exit(0)

        # filter gaps and negatives
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
            if 0: basin_obj.show_stations_data(wys, station_ids=station_ids_of_interest, show=True)
            #exit(0)

        # temporally interpolate snowcourses to form "snowpillows"
        if not C_PILLOWS_ONLY:
            basin_obj.temp_interp_courses(active_inbound_sta, ds)
            if 1: basin_obj.show_stations_data(wys, station_ids=active_inbound_sta, show=True)
        #visualize data
        if 0: basin_obj.show_stations_data(wys, station_ids=station_ids_of_interest, show=True)

        if 1:
            # load static ensemble readonly
            static_ens = np.load(STATIC_ENS_PATH, mmap_mode="r")
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
            basin_obj.overlay_stations(ds, station_ids_of_interest, show=False)
            plt.colorbar()
            plt.show()
            exit(0)

        rowsThresh = 10
        # delete compressed file
        # clear_output(OUTPUT_PATH)   #deletes all compressed files
        try:
            os.remove(OUTPUT + "menoi" + str(len(rcs)) + "_blosc.h5")
            print "removed ", OUTPUT + "menoi" + str(len(rcs)) + "_blosc.h5"
        except:
            pass
        rows = np.empty([0, 3 + R * C])

        #plt.ion()
        #plt.figure()
        #plt.show()
        #plt.colorbar()
        for wy in wys:
            d_Basinmean_cverror = []        #date, basin mean, pillow LOO cv error
            start_date = dt.date(wy-1,  month=10, day=1)
            end_date   = dt.date(wy,    month=10, day=1)
            if C_TEST:
                d = start_date + dt.timedelta(days=30 * 5)
                end_date = d + dt.timedelta(days=2)
            else:
                d = start_date
            while d < end_date:
                if wy == wys[-1] and d == end_date - dt.timedelta(days=1):
                    print "rowsThresh = 0"
                    rowsThresh = 0
                # 1. get observations
                obs = basin_obj.get_measurements(d, station_ids_of_interest)
                obs = np.array(obs) * IN_2_MM
                print d, obs
                if (obs <= 0).all():
                    #all zero
                    MEnOI = np.zeros(np.shape(mask))
                    MEnOI[~mask] = np.nan
                    cv_error = np.nan
                    mean = np.nanmean(MEnOI)
                else:
                    # 2. train optimal alpha
                    MEnOI, cv_error = predict_SWE_map(obs, rcs, static_ens, R, C, v=1)
                    MEnOI[MEnOI < 0] = 0.0
                    MEnOI[~mask] = np.nan
                    mean = np.nanmean(MEnOI)
                    #MEnOI[MEnOI < 0] = np.nan
                    #plt.imshow(MEnOI, interpolation="none")
                    #plt.colorbar()
                    #plt.show()
                    #plt.pause(0.05)
                    #plt.colorbar()
                d_Basinmean_cverror.append([toTS(d), mean, cv_error])
                rows = save_compressed_output(rows, d, MEnOI, "menoi" + str(len(rcs)), OUTPUT,
                                              rowsThresh=rowsThresh, expectedrows=365*3, comp=1, v=0)
                # 3. assimilate with obtained alpha
                d += dt.timedelta(days=1)
            save_metrics_2_csv(d_Basinmean_cverror, OUTPUT + "/" + str(wy) + "meta.csv")


if C_RETRIEVE_MAPS:
    maxR = 365 * len(wys)
    r = 0
    sample_ds = gdal.Open(PATHS["Feather Margulis SWE"] + "2016/20160401.tif")
    for r in range(maxR):
        try:
            trclinmap = load_row_from_map("menoi8", r, RET_FROM_DIR)
        except:
            break
        d = fromTS(trclinmap[0])
        R = int(trclinmap[1])
        C = int(trclinmap[2])
        map = trclinmap[3:].reshape([R, C])
        save_array_as_tif_similar_to(map, sample_ds, str(d), RET_TO_DIR+ str(water_year(d)))
        if 0:
            map[map < 0] = np.nan
            plt.imshow(map)
            plt.colorbar()
            plt.show()
            exit(0)


if C_VISU_MAPS:
    ax1 = plt.subplot(111)
    plt.ion()
    for wy in wys:
        start_date = dt.date(wy - 1, month=10, day=1)
        im1 = ax1.imshow(get_map(dt.date(wy, 4, 1), VIZ_DIR))
        plt.colorbar(im1)
        end_date = dt.date(wy, month=10, day=1)
        d = start_date
        while d < end_date:
            #print d
            try:
                map = get_map(d, VIZ_DIR)
                #map[np.isnan(map)] = 0.0
                #map[map <= 0] = 0.0
                im1.set_data(map)
                plt.title(str(d))
                plt.pause(0.01)

            except:
                pass
            d += dt.timedelta(days=1)

