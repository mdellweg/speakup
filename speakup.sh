#!/bin/sh

cd $(dirname $0)

./input_screen.py | espeak
