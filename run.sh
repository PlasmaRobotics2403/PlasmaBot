#!/bin/bash

# Pull from Github
git pull

# Install the required packages
pip3 install -r --upgrade requirements.txt

# Run the starting Python file
python3 run.py