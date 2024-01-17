if [[ `ssh pi@172.17.21.2 test -d /home/pi/Projects/Inverted-Maze/ && echo exists` ]] ; then
  ssh pi@172.17.21.2 -f 'rm -rf /home/pi/Projects/Inverted-Maze/';
fi

# Copy Inverted-Maze Directory to Raspberry Pi
scp -pr /home/dpea/Documents/Inverted-Maze pi@172.17.21.2:/home/pi/Projects/Inverted-Maze/

# Execute client.py
ssh pi@172.17.21.2 'cd /home/pi/Documents/Azure-Maze-6.0/final/maze/; python3 client.py'