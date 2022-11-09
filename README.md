![release](https://img.shields.io/badge/release-beta-green) ![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/mpg-age-bioinformatics/Flaski) [![DOI](https://zenodo.org/badge/227070034.svg)](https://zenodo.org/badge/latestdoi/227070034) [![Docker Image CI nightly](https://github.com/mpg-age-bioinformatics/flaski/actions/workflows/docker.nightly.yml/badge.svg)](https://github.com/mpg-age-bioinformatics/flaski/actions/workflows/docker.nightly.yml) [![Docker Image CI dev](https://github.com/mpg-age-bioinformatics/flaski/actions/workflows/docker.dev.yml/badge.svg)](https://github.com/mpg-age-bioinformatics/flaski/actions/workflows/docker.dev.yml) [![Docker Image CI nightly](https://github.com/mpg-age-bioinformatics/flaski/actions/workflows/docker.prod.yml/badge.svg)](https://github.com/mpg-age-bioinformatics/flaski/actions/workflows/docker.prod.yml)

# Flaski

Flaski is a flask & dash based collection of web apps for life sciences. 

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
- full stack

Flaski can be user for free on [https://flaski.age.mpg.de](https://flaski.age.mpg.de).

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

Feel free to contact us if you would like to deploy Flaski at your institution or if you would like to contribute to Flaski. 

```bash
mkdir -p ~/flaski_data/backup/stats ~/flaski_data/backup/users_data ~/flaski_data/backup/mariadb
git clone git@github.com:mpg-age-bioinformatics/flaski.git
cd flaski
cat << EOF > .env
MYSQL_PASSWORD=$(openssl rand -base64 20)
MYSQL_ROOT_PASSWORD=$(openssl rand -base64 20)
REDIS_PASSWORD=$(openssl rand -base64 20)
SECRET_KEY=$(openssl rand -base64 20)
EOF
docker-compose -f production-compose.yml up -d
```

Email logging:
```bash
docker-compose -f production-compose.yml exec server3 python3 -m smtpd -n -c DebuggingServer localhost:8025
```

Flaski is now accessible under [https://flaski.localhost](https://flaski.localhost). Depending on your local machine, it might take a few seconds until the server is up and running. You might need to edit your `/etc/hosts` file to include:
```
127.0.0.1       localhost
```
___

## Citing

Iqbal, A., Duitama, C., Metge, F., Rosskopp, D., Boucas, J. Flaski. (2021). doi:10.5281/zenodo.4849515
___

## Credits

Flaski was build using [Font-Awesome](https://github.com/FortAwesome/Font-Awesome) toolkit. Please consult the respective project for license information.

The Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing, Cologne, Germany.