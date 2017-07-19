# Docker

## Useful commands

### Show the running containers

```bash
docker ps
```

### Run a command in a container

```bash
docker exec
```

Example:

If you want to run `bash` inside the container (say to check things out), run:
```bash
docker exec -it <container-name> /bin/bash
```

The `-it` part stands for `i`nteractive and `t`erminal (roughly).

### Start a container with a different command

```bash
docker run
```

Example:

You want to start a container from the image `test` with bash

```bash
docker run -it test /bin/bash
```

# Docker-compose

This is a program that simplifies working with `docker` commands.
`docker` commands can get quite verbose (just run `man docker run` to see what
I mean).

The `docker-compose.yaml` file is a configuration file for running and building
a docker container or iamge respectively.

## Build the image

```bash
docker-compose build
```

## Run the server image

```bash
docker-compose up -d
```

The `-d` part means run the container in the background.'

## Stop the server image

```bash
docker-compose stop
```

or if you _really_ want to stop it

```bash
docker-compose kill
```

## Restart the server container

```bash
docker-compose restart
```

Note: This does **not** rebuild the image.
It just restarts the container
