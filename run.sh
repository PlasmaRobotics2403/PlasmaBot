#!/bin/bash

# Pull from Github
git pull

# Install the required packages
pip3 install --upgrade -r requirements.txt

# Remove Matplotlib Cache
python3 utils/removeCache.py

# Copy required fonts to the correct directory depending on system
case "$(uname -sr)" in

   Darwin*)
     cp -r plasmaBot/resources/fonts/*.ttf /Library/Fonts/
     ;;

   Linux*Microsoft*)
     cp -r plasmaBot/resources/fonts/*.ttf /usr/share/fonts/
     ;;

   Linux*)
     cp -r plasmaBot/resources/fonts/*.ttf /usr/share/fonts/
     ;;

   CYGWIN*|MINGW*|MINGW32*|MSYS*)
     echo 'Running in CYGWIN or MINGW: Cannot copy font.'
     ;;

   *)
     echo 'Unknown OS: Cannot copy font.' 
     ;;
esac

# Run the starting Python file
python3 run.py