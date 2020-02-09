#!/bin/bash
#pip3 list | egrep -v 'flaski|six|pip' | sed '1,2d' | awk '{ print $1"=="$2 }' | grep cython
echo "cython"
pip3 list | egrep -v 'flaski|six|pip' | sed '1,2d' | awk '{ print $1"=="$2 }' | grep numpy
pip3 list | egrep -v 'flaski|six|pip' | sed '1,2d' | awk '{ print $1"=="$2 }' | grep -v numpy