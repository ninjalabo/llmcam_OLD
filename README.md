# llmcam


<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

This file will become your README and also the index of your
documentation.

## Developer Guide

If you are new to using `nbdev` here are some useful pointers to get you
started.

### Install llmcam in Development mode

``` sh
# make sure llmcam package is installed in development mode
$ pip install -e .

# make changes under nbs/ directory
# ...

# compile to have changes apply to llmcam
$ nbdev_prepare
```

## Usage

### Installation

Install latest from the GitHub
[repository](https://github.com/ninjalabo/llmcam):

``` sh
$ pip install git+https://github.com/ninjalabo/llmcam.git
```

or from [conda](https://anaconda.org/ninjalabo/llmcam)

``` sh
$ conda install -c ninjalabo llmcam
```

or from [pypi](https://pypi.org/project/llmcam/)

``` sh
$ pip install llmcam
```

### Documentation

Documentation can be found hosted on this GitHub
[repository](https://github.com/ninjalabo/llmcam)’s
[pages](https://ninjalabo.github.io/llmcam/). Additionally you can find
package manager specific guidelines on
[conda](https://anaconda.org/ninjalabo/llmcam) and
[pypi](https://pypi.org/project/llmcam/) respectively.

## How to use

In development mode, navigate to the local repository and install the
editable version:

``` sh
$ cd /path/to/llmcam/repository
$ pip install -e . ['dev']
```

Start by importing our modules:

``` python
from llmcam.vision.ytlive import NHsta
from llmcam.vision.gpt4v import ask_gpt4v_about_image_file
from llmcam.application.runner import run_llmcam
```

``` python
fn = NHsta()()
fn
```

    [youtube] Extracting URL: https://www.youtube.com/watch?v=LMZQ7eFhm58
    [youtube] LMZQ7eFhm58: Downloading webpage
    [youtube] LMZQ7eFhm58: Downloading ios player API JSON
    [youtube] LMZQ7eFhm58: Downloading web creator player API JSON
    [youtube] LMZQ7eFhm58: Downloading m3u8 information
    11.11.2024 17:50:38
    cap_2024.11.11_17:58:09_unclear.jpg

    Path('../data/cap_2024.11.11_17:58:09_unclear.jpg')

``` python
ask_gpt4v_about_image_file(fn)
```

    {'timestamp': '2024-10-30T21:55:57',
     'location': 'Tuomiokirkko',
     'dimensions': {'width': 1280, 'height': 720},
     'buildings': {'number_of_buildings': 15,
      'building_height_range': '2-5 stories'},
     'vehicles': {'number_of_vehicles': 0},
     'waterbodies': {'visible': False},
     'street_lights': {'number_of_street_lights': 25},
     'people': {'approximate_number': 0},
     'lighting': {'time_of_day': 'night', 'artificial_lighting': 'prominent'},
     'visibility': {'clear': True},
     'sky': {'visible': True, 'light_conditions': 'night'}}

``` python
# Start the application on port 5001
run_llmcam()
```
