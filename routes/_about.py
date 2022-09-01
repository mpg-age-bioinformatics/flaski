from myapp import app
import os

PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)

v=app.config["APP_VERSION"]
v=str(v)

_about=f'''
Flaski is a flask and dash based collection of web apps for life sciences. 

Flaski provides:

- interactive data analysis
- user level authentication
- Apps as plugins
- session management 
- server storage
- Graphic User Interface to Programmatic Interface
- App2App communication
- server based
- background jobs
- databases
- scalable
- continuous delivery
- usage statistics
- on-the-fly error reporting
- full stack

Check our how-to videos on [YouTube](https://www.youtube.com/channel/UCQCHNHJ23FGyXo9usEC_TbA).

For Graphical User Interface to Programmatic Interface exchanges please install the [pyflaski](https://github.com/mpg-age-bioinformatics/pyflaski) companion package.

Issues: [https://github.com/mpg-age-bioinformatics/flaski/issues](https://github.com/mpg-age-bioinformatics/flaski/issues).

Source: [https://github.com/mpg-age-bioinformatics/flaski](https://github.com/mpg-age-bioinformatics/flaski).

##### Citing

Iqbal, A., Duitama, C., Metge, F., Rosskopp, D., Boucas, J. Flaski. (2021). doi:10.5281/zenodo.4849515

We recommend that you allways export your session along with your results so that you can in future reproduce them.

Current version can be seen at the end of this page and old sessions version can be checked under [https://flaski.age.mpg.de/vcheck/](https://flaski.age.mpg.de/vcheck/).

If you wish to open an older session under the same package version please use the [pyflaski](https://github.com/mpg-age-bioinformatics/pyflaski) companion package. 

##### Credits

Flaski was build using the [Font-Awesome](https://github.com/FortAwesome/Font-Awesome) toolkit. Please consult the respective project for license information.

The Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing, Cologne, Germany.

##### Version

{v} // pyflaski #{PYFLASKI_VERSION}
'''