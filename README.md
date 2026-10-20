![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/mpg-age-bioinformatics/Flaski) [![DOI](https://zenodo.org/badge/227070034.svg)](https://zenodo.org/badge/latestdoi/227070034) [![Docker Image CI nightly](https://github.com/mpg-age-bioinformatics/flaski/actions/workflows/docker.nightly.yml/badge.svg)](https://github.com/mpg-age-bioinformatics/flaski/actions/workflows/docker.nightly.yml) [![Docker Image CI latest](https://github.com/mpg-age-bioinformatics/flaski/actions/workflows/docker.latest.yml/badge.svg)](https://github.com/mpg-age-bioinformatics/flaski/actions/workflows/docker.latest.yml) [![Docker Image CI Production](https://github.com/mpg-age-bioinformatics/flaski/actions/workflows/docker.tag.yml/badge.svg)](https://github.com/mpg-age-bioinformatics/flaski/actions/workflows/docker.tag.yml)

<!-- ![release](https://img.shields.io/badge/release-beta-green)  -->

# Flaski

Flaski is a [myapp](https://github.com/mpg-age-bioinformatics/myapp) based collection of web apps for data analysis and visualization in life sciences. 

![flaski](/Flaski.Readme.png)

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

<!-- Apps documentation can be found on the project's [wiki](https://github.com/mpg-age-bioinformatics/flaski/wiki).  -->

Check our how-to videos on [YouTube](https://www.youtube.com/channel/UCQCHNHJ23FGyXo9usEC_TbA).

Information on how to deploy Flaski on your own servers can be found in [DEPLOYING.md](DEPLOYING.md) and on Google Kubernetes Engine in [kubernetes](kubernetes).

For Graphical User Interface to Programmatic Interface exchanges please install the [pyflaski](https://github.com/mpg-age-bioinformatics/pyflaski) companion package.

Flaski sessions are versioned and you can check the respective version of any saved session [here](https://flaski.age.mpg.de/vcheck). For reproducting plots done with previous Flaski versions please use the [pyflaski](https://github.com/mpg-age-bioinformatics/pyflaski) companion package.

If you are looking to contribute to Flaski please check [CONTRIBUTING.md](CONTRIBUTING.md).

Issues: [https://github.com/mpg-age-bioinformatics/flaski/issues](https://github.com/mpg-age-bioinformatics/flaski/issues).

<!-- Source: [https://github.com/mpg-age-bioinformatics/flaski](https://github.com/mpg-age-bioinformatics/flaski). -->

Please check our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before doing any contribution or opening an issue.

___

## Local installation

For local installation and app development, follow [CONTRIBUTING.md](CONTRIBUTING.md).
It covers building with `docker-compose.yml`, starting the development server,
and capturing test emails. After completing setup and starting the development
server, the local app will be available at
[https://flaski.localhost/v3](https://flaski.localhost/v3).

Feel free to contact us if you would like to deploy Flaski at your institution or
contribute to Flaski.
___

## Citing

Iqbal, A., Duitama, C., Metge, F., Rosskopp, D., Amin, H., Boucas, J. Flaski. (2021). doi:10.5281/zenodo.4849515


## Versioning

We recommend that you allways export your session along with your results so that you can in future reproduce them.

Current version can be seen at the end of this page and old sessions version can be checked under [https://flaski.age.mpg.de/vcheck/](https://flaski.age.mpg.de/vcheck/).

If you wish to open an older session under the same package version please use the [pyflaski](https://github.com/mpg-age-bioinformatics/pyflaski) companion package. 

___

## Credits

Flaski was build using [Font-Awesome](https://github.com/FortAwesome/Font-Awesome) toolkit. Please consult the respective project for license information.

The Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing, Cologne, Germany.
