#!/bin/bash
set -x #echo on
cd "$(dirname "$0")"

OUTPUT_DIR=/home/$USER/plot/lab2
SIM_PATH=/home/$USER/exp/simulations
DESCRIPTOR_PATH=/home/$USER/$EXPERIMENT.json

mkdir -p $OUTPUT_DIR

python3 lab2_part4.py -o $OUTPUT_DIR -d $DESCRIPTOR_PATH -s $SIM_PATH
#python3 delete.py -d $DESCRIPTOR_PATH -s $SIM_PATH