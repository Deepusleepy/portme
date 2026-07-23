#!/usr/bin/env bash
set -eu
sleep 1
python3 -m unittest discover -s tests -v
python3 -m py_compile src/*.py
