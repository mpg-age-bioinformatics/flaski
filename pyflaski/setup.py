import codecs
import os
import re
import sys
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()

setup(name = 'pyflaski',
      version = '0.1.0',
      description = 'Flaski companion package for python.',
      long_description = read('README.rst'),
      url = 'https://github.com/mpg-age-bioinformatics/flaski',
      author = 'Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing',
      author_email = 'bioinformatics@age.mpg.de',
      license = 'MIT',
      packages = [ 'pyflaski' ],
      zip_safe = False )