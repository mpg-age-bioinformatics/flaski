pip3 list | sed '1,2d' | awk '{ print $1"=="$2 }' 
