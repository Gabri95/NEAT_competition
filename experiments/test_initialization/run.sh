#!/bin/bash

ROOT=../..
PORT=3008
DRIVER=Driver1




python $ROOT/src/nn_evolve.py -g 1 -f 1 -o . -p $PORT -u -d $DRIVER -t 110

