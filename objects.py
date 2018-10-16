from imports import *

class station(object):
    def __init__(self, lat_lon, type=None, cdec_type_id=None, station_id=None, operator=None):
        self.lat_lon        = lat_lon
        self.type           = type
        self.cdec_type_id   = cdec_type_id
        self.cdec_id        = station_id
        self.operator       = operator
        self.data           = {}
        self.active         = True      #else station was retired
        # data is a dict
        #   'yyyy': dict
        #               {
        #                   PST date: value
        #               }
    #user
    #ds :   tif_ds
    def bound(self):
        for wy in self.data:
            for day in self.data[wy]:
                if self.data[wy][day] < 0:
                    self.data[wy][day] = 0.0

    def fill_gaps_linear(self):    #remove negatives
        for wy in self.data.keys():
            dates, values = self.get_time_series(wy)
            in_gap = False
            for i in range(len(values)):
                if np.isnan(values[i]) and not in_gap:
                    svi = i-1
                    in_gap = True
                if not(np.isnan(values[i])) and in_gap: #exiting gap
                    evi = i
                    rate = (values[evi] - values[svi])/(evi - svi)
                    j = 0
                    while j + svi < evi:
                        values[svi + j] = values[svi] + j * rate
                        j+=1
                    in_gap = False
            for d, v in zip(dates, values):
                self.data[wy][d] = v

    def get_measurement(self, day):
        wy = self.water_year(day)
        #print sorted(self.data[wy].keys())
        #exit(0)
        return self.data[wy][day]

    def get_rc(self, ds):
        if hasattr(self, 'rc'):
            return self.rc
        return self.latlon_2_rc(ds)

    def get_latlon(self):
        return self.lat_lon

    def print_station_info(self):
        print self.cdec_id, self.type, self.lat_lon, self.data

    def get_time_series(self, wy):
        if not self.active:
            return None
        dates = []
        values = []
        keylist = self.data[wy].keys()
        keylist.sort()
        for key in keylist:
            dates.append(key)
            values.append(self.data[wy][key])
        return [dates, values]

    #private
    def isPillow(self):
        return self.operator == "CA Dept of Water Resources/O & M"

    def parse_daily(self, wy, df):
        self.data[wy] = {}
        for index, row in df.iterrows():
            try:
                self.data[wy][(parser.parse(row["DATE / TIME (PST)"])).date()] = float(row["SNOW WC INCHES"])
            except Exception as e:
                if row["SNOW WC INCHES"] == "--":
                    self.data[wy][(parser.parse(row["DATE / TIME (PST)"])).date()] = np.nan
                else:
                    print "parse_daily Error = ", e
                    print "     >>> index = ", index, "row = ", row
                    exit(0)

    def parse_monthly(self, wy, df):
        self.data[wy] = {}
        for index, row in df.iterrows():
            try:
                self.data[wy][(parser.parse(row["Measured Date"])).date()] = float(row["W.C."])
            except Exception as e:
                print "parse_monthly Error = ", e
                print "     >>> index = ", index, "row = ", row
                exit(0)
        return

    def populate_data(self, wy, fpath, debug = 0):
        if not self.active:
            return
        if not os.path.exists(fpath):
            os.mkdir(fpath)
        fdest = fpath + str(wy) + "_" + self.cdec_id + ".csv"
        if not (os.path.isfile(fdest)):
            if debug: print "downloading ", self.cdec_id, "data from cdec to ", fdest, "..."
            if self.isPillow():    #if snow pillow
                df = self.download_daily_CDEC(self.cdec_id, dt.date(year=wy, month=10, day=1), "1year", debug=0)
                if df is not None:
                    df.to_csv(fdest)
                else:
                    self.active = False
                    return
            else:   #snow course
                df = self.download_monthly_CDEC(self.cdec_id, dt.date(year=wy, month=10, day=1), "1year", debug=0)
                if df is not None:
                    df.to_csv(fdest)
                else:
                    self.active = False
                    return

        if debug: print "loading file ", fdest, "..."
        if debug == 2:
            with pd.option_context('display.max_rows', None, 'display.max_columns', None):
                print(df)
        df = pd.read_csv(fdest)
        if self.isPillow():
            self.parse_daily(wy, df)
        else:
            self.parse_monthly(wy, df)
        #convert df into date : value

    def download_daily_CDEC(self, station_id, end_date, span, debug=0):
        assert(span == "1year")
        day = end_date.day
        month = end_date.month
        year = end_date.year
        #wq = "http://cdec.water.ca.gov/dynamicapp/QueryDaily?s=KTL&end=2015-10-01&span=1year"
        wq = "http://cdec.water.ca.gov/dynamicapp/QueryDaily?s=" + station_id + "&end="+str(year)+"-"+\
             str(month).zfill(2)+"-"+str(day).zfill(2)+"&span=" + span
        if debug: print wq
        #print wq
        #exit(0)
        tables = pd.read_html(wq, header=0)[0]
        return tables[:-1]

    def download_monthly_CDEC(self, station_id, end_date, span, debug=0):
        day = end_date.day; month = end_date.month; year = end_date.year
        #wq = "https://cdec.water.ca.gov/cgi-progs/queryMonthly?s=" + station_id + "&d=" + str(month).zfill(2) \
        #     + "%2F" + str(day).zfill(2) + "%2F" + str(year) + "&span=" + span
        #if debug: print wq
        #print wq
        wq = "http://cdec.water.ca.gov/dynamicapp/QueryMonthly?s=" + station_id + "&end=" + str(year) + "-" + \
        str(month).zfill(2) + "-" + str(day).zfill(2) + "&span=" + span
        #print wq
        #exit(0)
        try:
            df = pd.read_html(wq, header=0)[1]
            #print tables
            #exit(0)
        except Exception as e:
            print "download_monthly_CDEC Error: ", e
            print "     >>> no table found for query = ", wq
            df = None
            pass
        return df

    #================ convert lat lon to margulis tiff row col
    def coords_to_idx(self, coords_x, coords_y, gt):
        #print "coords_x - gt[0] = ", coords_x, " - ", gt[0]
        idx_x = np.floor((coords_x - gt[0]) / gt[1]).astype(int)
        idx_y = np.floor((coords_y - gt[3]) / gt[5]).astype(int)
        return idx_y, idx_x

    def idx_to_coords(self, idx_y, idx_x, gt):
        coords_x = gt[0] + idx_x * gt[1]
        coords_y = gt[3] + idx_y * gt[5]
        return coords_x, coords_y

    def latlon_2_rc(self, ds):
        #ds = gdal.Open(test_file)
        #ds_geo = ds.GetGeoTransform
        test_map = ds.GetRasterBand(1).ReadAsArray()
        R, C = np.shape(test_map)
        register_gt = ds.GetGeoTransform()
        rs, cs = self.coords_to_idx(np.array([self.lat_lon[1]]),
                                 np.array([self.lat_lon[0]]),
                                 register_gt)
        self.rc = [rs[0], cs[0]]
        return self.rc

    # helpers
    def water_year(self, day):
        if day.month >= 10:  # month is 10, 11, 12: water year is calendar year + 1
            return day.year + 1
        return day.year  # month is 1 -> 10: water year is calendar year


class basin(object):
    def __init__(self, basin_name, basin_cdec_id):
        self.name       = basin_name
        self.cdec_id    = basin_cdec_id
        self.stations   = {}    #list of stations indexed by id

    def print_stations_info(self):
        for sta in self.stations.itervalues():
            sta.print_station_info()

    def get_stations_time_series_data(self, wy, only_pillows=False):
        series = {}
        for sta in self.stations.itervalues():
            if only_pillows and not sta.isPillow():
                continue
            series[sta.cdec_id] = sta.get_time_series(wy)
        return series

    def get_stations(self, station_ids):
        stations = []
        for st_id in station_ids:
            stations.append(self.stations[st_id])

    def get_stations_rcs(self, ds, station_ids=None):
        rcs = []
        if not station_ids:
            station_ids = self.stations.keys()
        for station_id in station_ids:
            rcs.append(self.stations[station_id].get_rc(ds))
        return rcs

    def overlay_stations(self, ds, station_ids=None, show=True):
        if not station_ids:
            station_ids = self.stations.keys()
        rcs = self.get_stations_rcs(ds, station_ids)

        im = ds.GetRasterBand(1).ReadAsArray()
        im[im < 0] = np.nan
        rcs = np.array(rcs)
        fig, ax = plt.subplots()
        plt.imshow(im, interpolation="none")
        ax.scatter(rcs[:, 1], rcs[:, 0])
        for i, txt in enumerate(station_ids):
            ax.annotate(txt, (rcs[:, 1][i], rcs[:, 0][i]))
        if show:
            plt.show()

    def get_measurements(self, day, station_ids=None):
        measurements = []
        if not station_ids:
            station_ids = self.stations.keys()
        for sta_id in station_ids:
            measurements.append(self.stations[sta_id].get_measurement(day))
        return measurements

    def bound_stations_data(self, station_ids=None):
        if not station_ids:
            station_ids = self.stations.keys()
        for sta_id in station_ids:
            self.stations[sta_id].bound()

    def fill_stations_data_gap_linear(self, station_ids=None):
        if not station_ids:
            station_ids = self.stations.keys()
        for sta_id in station_ids:
            self.stations[sta_id].fill_gaps_linear()

    def show_stations_data_all(self, wys, only_pillows=False):
        for wy in wys:
            key_dt_val = self.get_stations_time_series_data(wy, only_pillows=only_pillows)
            for key in key_dt_val.keys():
                if key_dt_val[key] is not None:
                    plt.plot( key_dt_val[key][0], key_dt_val[key][1], label=key)
            plt.legend()
            plt.show()

    def show_stations_data(self, wys, station_ids=None, show=True):
        if not station_ids:
            station_ids = self.stations.keys()
        for wy in wys:
            plt.figure()
            for sta_id in station_ids:
                dt_val = self.stations[sta_id].get_time_series(wy)
                plt.plot(dt_val[0], dt_val[1], label=sta_id)
            plt.legend()
            plt.title("Water year = "+ str(wy))
        if show:
            plt.show()
