#!/bin/bash

ROOT=../..
PORT=3008




python $ROOT/src/nn_evolve.py -g 50 -f 1 -o . -p $PORT

