#!/bin/bash

ROOT=../..
PORT=3006




python $ROOT/src/pso_trainer.py -g 10 -o . -p $PORT

