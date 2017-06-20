#!/usr/bin/env bash
# Change to the top level
cd ..

# Build the image for the server
sudo docker-compose build

# Export the image into a tar archive
sudo docker save -o server_image ehub_server

# Allow people to drag and drop the file
sudo chown $(whoami) server_image

# Now all you do is transfer it to a computer and look at load.sh
