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
                self.data[wy][parser.parse(row["DATE / TIME (PST)"])] = float(row["SNOW WC INCHES"])
            except Exception as e:
                if row["SNOW WC INCHES"] == "--":
                    self.data[wy][parser.parse(row["DATE / TIME (PST)"])] = np.nan
                else:
                    print "parse_daily Error = ", e
                    print "     >>> index = ", index, "row = ", row
                    exit(0)

    def parse_monthly(self, wy, df):
        self.data[wy] = {}
        for index, row in df.iterrows():
            try:
                self.data[wy][parser.parse(row["Measured Date"])] = float(row["W.C."])
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


