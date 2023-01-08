#!/bin/bash

python3 buildrom.py
minipro -p W27C512@DIP28 -w rom.bin -s
