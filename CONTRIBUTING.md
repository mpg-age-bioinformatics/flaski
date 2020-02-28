# Contributing

Flaski is a flask based collection of web apps for life-sciences. Flaski can be deployed using the `docker-compose.yml` or on a [kubernetes](https://github.com/mpg-age-bioinformatics/flaski/tree/master/kubernetes#kubernetes) cluster. Within Flaski, `pyflaski` provides access to all the main functions used by the different web applications.

If you would like to contribute to flaski please make a fork and submit a pull request once you're ready with your changes and would like to see them merged to the main branch.

### Apps

Each app is made of 3 parts, `main`, `routes`, and `templates`:

```bash
├── CONTRIBUTING.md
├── Dockerfile
├── LICENSE.md
├── MANIFEST.in
├── README.md
├── config.py
├── docker-compose.yml
├── flaski
│   ├── __init__.py
│   ├── apps
│   │   ├── main  <<<<<<< This is where the main functions for the apps are stored >>>>>>>
│   │   │   ├── heatmap.py
│   │   │   ├── iheatmap.py
│   │   │   ├── iscatterplot.py
│   │   │   ├── scatterplot.py
│   │   │   └── venndiagram.py
│   │   └── routes  <<<<<<< This is where the main functions for the apps are connected to html output and input >>>>>>>
│   │       ├── heatmap.py
│   │       ├── iheatmap.py
│   │       ├── iscatterplot.py
│   │       ├── scatterplot.py
│   │       └── venndiagram.py
│   ├── email.py
│   ├── errors.py
│   ├── forms.py
│   ├── models.py
│   ├── routes.py
│   ├── routines.py
│   ├── static
│   ├── storage.py
│   └── templates
│       ├── 404.html
│       ├── 500.html
│       ├── apps  <<<<<<< This is where the html for the apps is coded >>>>>>>
│       │   ├── heatmap.html
│       │   ├── iheatmap.html
│       │   ├── iscatterplot.html
│       │   ├── scatterplot.html
│       │   └── venndiagram.html
│       ├── base.html
.       .
.       .
.       .
```
If adding new apps don't forget to edit `flaski/__init__.py` accordingly:
```python
from flaski.apps.routes import scatterplot, iscatterplot, heatmap, iheatmap, venndiagram
```
and to add the app description to `flaski/__init__.py`:
```python
FREEAPPS=[{ "name":"Scatter plot","id":'scatterplot_more', "link":'scatterplot' , "java":"javascript:ReverseDisplay('scatterplot_more')", "description":"A static scatterplot app." },\
        { "name":"iScatter plot", "id":'iscatterplot_more',"link":'iscatterplot' ,"java":"javascript:ReverseDisplay('iscatterplot_more')", "description":"An intreactive scatterplot app."},\
        { "name":"Heatmap", "id":'heatmap_more',"link":'heatmap' ,"java":"javascript:ReverseDisplay('heatmap_more')", "description":"An heatmap plotting app."},\
        { "name":"iHeatmap", "id":'iheatmap_more',"link":'iheatmap' ,"java":"javascript:ReverseDisplay('iheatmap_more')", "description":"An interactive heatmap plotting app."},\
        { "name":"Venn diagram", "id":'venndiagram_more',"link":'venndiagram' ,"java":"javascript:ReverseDisplay('venndiagram_more')", "description":"A venn diagram plotting app."} ]
```
If you're adding private apps to your deployment ie. apps that will only be available to certain users do not edit `flaski/__init__.py` but instead add the app description to `utils/private.apps.tsv`.
Use `all` for all logged in users and `#domain.com` if you want to add users from a specific email domain.

### jupyter

During development it can be useful to use a `jupyter` in the same build environment as Flaski. For this you can deploy Flaski locally using `docker-compose` 
and then get an interactive shell in the Flaski container with:
```bash
docker-compose exec server /bin/bash
```
Once inside the container start `jupyter` with:
```bash
jupyter notebook --allow-root --ip=0.0.0.0
```
You can now use the displayed link to access `jupyter` in Flaski build environment.

### pyflaski

`pyflaski` is maintained in the `pyflaski` folder with symbolic links to `flaski/apps/main`:
```
.
.
.
├── pyflaski
│   ├── README.rst
│   ├── conf.py
│   ├── dev
│   │   └── dev1.ipynb
│   ├── pyflaski
│   │   ├── __init__.py
│   │   ├── heatmap.py -> ../../flaski/apps/main/heatmap.py
│   │   ├── iheatmap.py -> ../../flaski/apps/main/iheatmap.py
│   │   ├── iscatterplot.py -> ../../flaski/apps/main/iscatterplot.py
│   │   ├── scatterplot.py -> ../../flaski/apps/main/scatterplot.py
│   │   └── venndiagram.py -> ../../flaski/apps/main/venndiagram.py
│   └── setup.py
├── requirements.txt
.
.
.
```
When adding new apps don't forget to generate the respective links in `pyflaski` as well as to add the respective imports
in `pyflaski/pyflaski/__init__.py`:
```python
""" Flaski companion package"""

import pyflaski.iscatterplot
import pyflaski.scatterplot
import pyflaski.heatmap
import pyflaski.iheatmap
import pyflaski.venndiagram
```
Please use `jupyter` as described above to test `pyflaski`.

### Dependencies

If new/additional python packages are required please don't forget to add them to `requirements.txt`. Alternatively, run 
```bash
./utils/getenv.sh > requirements.txt
```
If new system packages are required please edit the `Dockerfile` accordingly.
