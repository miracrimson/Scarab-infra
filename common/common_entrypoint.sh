#!/bin/bash

# Check scarab and pin already exist after the container runs with mounted $OUTDIR. Copy them only if not exist.
shopt -s extglob
if [ -d "/home/$username/scarab" ] && [ -d "/home/$username/pin-3.15-98253-gb56e429b1-gcc-linux" ]; then
  cp -r /tmp_home/!(scarab | pin-3.15-98253-gb56e429b1-gcc-linux) /home/$username
elif [ -d "/home/$username/scarab" ] && [ ! -d "/home/$username/pin-3.15-98253-gb56e429b1-gcc-linux" ]; then
  cp -r /tmp_home/!(scarab) /home/$username
elif [ ! -d "/home/$username/scarab" ] && [ -d "/home/$username/pin-3.15-98253-gb56e429b1-gcc-linux" ]; then
  cp -r /tmp_home/!(pin-3.15-98253-gb56e429b1-gcc-linux) /home/$username
else
  cp -r /tmp_home/* /home/$username
fi
rm -r /tmp_home/*

cd /home/$username/scarab/src && make