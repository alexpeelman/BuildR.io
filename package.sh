#!/bin/bash
python setup.py bdist_wheel
pip install `find dist | grep .whl`

