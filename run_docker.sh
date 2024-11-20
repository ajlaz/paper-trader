#!/bin/bash

# Environment Variables
IMAGE_NAME="paper-trader"
CONTAINER_TAG="latest"
HOST_PORT=5002 # host port
HTTP_PORT=5002 # container port
BUILD=true # build image

# Check if we need to build the Docker image
if [ "$BUILD" = true ]; then
    echo "Building Docker image..."
    docker build --build-arg HTTP_PORT=${HTTP_PORT} -t ${IMAGE_NAME}:${CONTAINER_TAG} .
else
  echo "Skipping Docker image build..."
fi

# Stop and remove the running container if it exists
if [ "$(docker ps -q -a -f name=${IMAGE_NAME}_container)" ]; then
    echo "Stopping running container: ${IMAGE_NAME}_container"
    docker stop ${IMAGE_NAME}_container

    # Check if the stop was successful
    if [ $? -eq 0 ]; then
        echo "Removing container: ${IMAGE_NAME}_container"
        docker rm ${IMAGE_NAME}_container
    else
        echo "Failed to stop container: ${IMAGE_NAME}_container"
        exit 1
    fi
else
    echo "No running container named ${IMAGE_NAME}_container found."
fi

# Run the Docker container with the necessary ports and volume mappings
echo "Running Docker container..."
docker run -d \
  --name ${IMAGE_NAME}_container \
  --env-file .env \
  -p ${HOST_PORT}:${HTTP_PORT} \
  ${IMAGE_NAME}:${CONTAINER_TAG}

echo "Docker container is running on port ${HOST_PORT}."