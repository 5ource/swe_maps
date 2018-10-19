#cdec data download
import datetime as dt
import pandas as pd
import numpy as np
import os
from dateutil import parser
import cPickle
from matplotlib import pyplot as plt

#interpolation
from sklearn.metrics import mean_squared_error
from math import sqrt
import tables
import time

import gdal

from collections import defaultdict