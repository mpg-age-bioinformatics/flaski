from myapp import app
import os

PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)

EXT_URL=os.environ["APP_URL"]
EXT_URL=f"{EXT_URL}/ext/"

v=app.config["APP_VERSION"]
v=str(v)

_about=f'''

Flaski is a [myapp]({EXT_URL}github.com/mpg-age-bioinformatics/myapp) based collection of web apps for data analysis and visualization in life sciences. 

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
- access to databases
- usage statistics
- on-the-fly error reporting
- scalable
- continuous delivery
- full stack ready
- multiplatform: *amd64*, *arm64*, and * aarch64*

Flaski can be used for free on [https://flaski.age.mpg.de](https://flaski.age.mpg.de).

Check our how-to videos on [YouTube]({EXT_URL}www.youtube.com/channel/UCQCHNHJ23FGyXo9usEC_TbA).

For Graphical User Interface to Programmatic Interface exchanges please install the [pyflaski]({EXT_URL}github.com/mpg-age-bioinformatics/pyflaski) companion package.

Issues: [https://github.com/mpg-age-bioinformatics/flaski/issues]({EXT_URL}github.com/mpg-age-bioinformatics/flaski/issues).

Source: [https://github.com/mpg-age-bioinformatics/flaski]({EXT_URL}github.com/mpg-age-bioinformatics/flaski).

Please check our [CODE_OF_CONDUCT.md]({EXT_URL}github.com/mpg-age-bioinformatics/flaski/blob/main/CODE_OF_CONDUCT.md) before doing any contribution or opening an issue.

##### Citing

Iqbal, A., Duitama, C., Metge, F., Rosskopp, D., Boucas, J. Flaski. (2021). doi:10.5281/zenodo.4849515

##### Versioning

We recommend that you allways export your session along with your results so that you can in future reproduce them.

Current version can be seen at the end of this page and old sessions version can be checked under [https://flaski.age.mpg.de/vcheck/](https://flaski.age.mpg.de/vcheck/).

If you wish to open an older session under the same package version please use the [pyflaski]({EXT_URL}github.com/mpg-age-bioinformatics/pyflaski) companion package. 

##### Credits

Flaski was build using the [Font-Awesome]({EXT_URL}github.com/FortAwesome/Font-Awesome) toolkit. Please consult the respective project for license information.

The Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing, Cologne, Germany.

##### Version

flaski: {v}

pyflaski: #{PYFLASKI_VERSION}
'''