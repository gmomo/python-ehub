# Docker Server

This is documentation on how the XMLRPC Docker-based server works.

### XMLRPC

Stands for XML Remote-Procedure Call.
It allows code to call a method or procedure but have it execute code on 
another machine (remote).

Example:

Here is the code to create a XMLRPC server:
```python
from xmlrpc import server

def remote_method(x, y):
    return x + y

with server.SimpleXMLRPCServer('http://<ip>:<port>') as server:
    server.register_function(remote_method)
    
    server.serve_forever()
```

Here is the code to call the server:
```python
from xmlrpc import client

with client.ServerProxy('http://<ip>:<port>') as server:
    result = server.remote_method(1, 2)
    
    assert result == 3
```

### Docker

Docker is an open-source project that allows developers to easily create 
software containers.

Software containers are a construct that groups everything (the code, 
configuration files, libraries, OS, etc.) into a single thing (a container).
This allows someone to pickup a container and then run it on any machine that 
has Docker installed on it.
The container will run exactly the same on any computer.
This prevents problems such as "well it worked on my computer".

Docker confuses this terminology a little bit because it uses Docker images 
and Docker containers.

#### Docker Image

This is the "blueprint" of the files, programs, and OS that are needed for the
software container.

#### Docker Container

This is a running instance of an image.

Much like a blueprint of a building, you can have one blueprint and multiple 
buildings that use that blueprint.

## How it works

We essentially create a XMLRPC server, which is much like the above example, 
and have that server run inside a Docker container.
The host machine that is running the Docker container then links the outside
world with the Docker container.
When sending a message to the Docker container, the IP and port of the host 
machine is used; not the Docker container's IP and port.

## How to create the image

When in the root directory, do
```bash
docker-compose build
```

This creates a new image of the XMLRPC server.

## How to run the server

In the root directory, do
```bash
docker-compose up -d
```

Docker-compose is a utility for Docker that allows having a configuration file
`docker-compose.yml` for all the runtime options for `docker`.

## How to stop the server

To gracefully stop:
```bash
docker-compose down
```

To kill it with fire:
```bash
docker-compose kill
```
