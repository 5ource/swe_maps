# SWE_maps
Generates daily Snow Water Equivalent maps from historical maps and CDEC snow measurements.

### Setting up Conda
Create python virtual environment **swe_maps**

`conda -V`

`conda update conda`

`conda create -n swe_maps python=2.7.12 anaconda`

`source activate swe_maps`

to check location of virtual environment

`echo $CONDA_PREFIX`

### Install Ulmo	 	-	Aborted
Ulmo is a python library for clean, simple and fast access to public hydrology and climatology data.

We are interested in the APIs that connect to CDEC. Details available at:
<https://ulmo.readthedocs.io/en/latest/api.html>

`conda install -n swe_maps -c conda-forge ulmo`

<span style="color:red "> Ulmo functions are failing, so uninstall </span>

### Station Data

Custom functions are created to download and save sensor values into the following structure:

New class defined as dictionary:
Each 'yyyy' entry is a water year:
Ex: water year 2015 spans dates from 2015-10-01 to 2016-09-31

```
class station
{
'cdec_id': 
'lat_lon': [latitude, longitude]
'type':	type of values, here is SWE
'yyyy': dict {
				date: value
				}
'yyyy'...
}
```

`conda install -n swe_maps -c conda-forge matplotlib`\
