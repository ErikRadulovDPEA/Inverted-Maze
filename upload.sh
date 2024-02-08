#!/bin/zsh

if [[ `ssh pi@172.17.21.2 test -d /home/pi/Projects/Inverted-Maze/ && echo exists` ]] ; then
  ssh pi@172.17.21.2 -f 'rm -rf /home/pi/Projects/Inverted-Maze/';
fi

# Copy Inverted-Maze Directory to Raspberry Pi
scp -pr /home/softdev/Documents/Inverted-Maze/ pi@172.17.21.2:/home/pi/Projects/Inverted-Maze/

# End previous process if it exists
ssh pi@172.17.21.2 'sudo lsof -i :5001 -t | xargs -r sudo kill -9'

# Execute client.py
ssh pi@172.17.21.2 'cd /home/pi/Projects/Inverted-Maze/; python3 client.py'



