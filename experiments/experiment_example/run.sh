#!/bin/bash

ROOT=../..

PORT=3001

DRIVER=Driver1

python $ROOT/src/nn_evolve.py -g 100 -f 1 -o . -p $PORT -u -s -d $DRIVER -t 150

