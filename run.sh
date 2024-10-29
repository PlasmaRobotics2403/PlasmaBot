#!/bin/bash

# Pull from Github
git pull

# Install the required packages
pip3 install --upgrade -r requirements.txt

# Run the starting Python file
python3 run.py