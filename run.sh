#!/bin/bash

# Pull from Github
git pull

# Install the required packages
pip3 install --upgrade -r requirements.txt

# Remove Matplotlib Cache
python3 plasmaBot/utils/removeCache.py

# Run the starting Python file
python3 run.py