#!/bin/bash

ROOT=../..
PORT=3004




python $ROOT/src/nn_evolve.py -g 100 -f 1 -o . -p $PORT -c checkpoints/neat_gen_22.checkpoint
