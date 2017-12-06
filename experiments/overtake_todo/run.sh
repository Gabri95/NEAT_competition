#!/bin/bash

ROOT=../..
PORT=3003




python $ROOT/src/nn_evolve.py -g 100 -f 1 -o . -p $PORT

