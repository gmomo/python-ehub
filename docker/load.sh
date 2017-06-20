#!/usr/bin/env bash
# Load the tar archive into Docker
sudo docker load -i server_image

# Now all you do is run
#     docker-compose up -d
# to start up the server.
# If the server acts funny, all you do is
#     docker-compose restart
# This restarts the server container.
