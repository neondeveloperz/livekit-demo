#!/bin/bash

# LiveKit Installer Script
# Supports Dev (Local Docker) and Prod (Config Generation) modes

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}LiveKit Server Installer${NC}"
echo "------------------------"

# 1. Prerequisite Checks
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker and try again."
    exit 1
fi

echo -e "${GREEN}✔ Docker is installed${NC}"

# 2. Mode Selection
echo ""
echo "Select installation mode:"
echo "1) Dev Mode (Run local server instantly)"
echo "2) Prod Mode (Generate production config)"
read -p "Enter choice [1-2]: " mode

if [ "$mode" == "1" ]; then
    # --- DEV MODE ---
    echo ""
    echo -e "${BLUE}Starting LiveKit Server in Development Mode...${NC}"
    
    # Check if container already exists
    if [ "$(docker ps -aq -f name=livekit-dev-server)" ]; then
        echo "Removing existing livekit-dev-server container..."
        docker rm -f livekit-dev-server
    fi

    echo "Running livekit/livekit-server..."
    # Run LiveKit in dev mode
    # -p 7880:7880 (API/Signal)
    # -p 7881:7881 (Internal) -- usually not needed for single node dev, but good to have
    # -p 7882:7882/udp (Unity/WebGL)
    # --network host is best for linux, but purely local dev on mac often needs port mapping.
    # We will use port mapping for broader compatibility in dev.
    
    docker run -d \
        --name livekit-dev-server \
        -p 7880:7880 \
        -p 7881:7881 \
        -p 7882:7882/udp \
        livekit/livekit-server \
        --dev \
        --bind 0.0.0.0

    echo -e "${GREEN}✔ LiveKit Server is running!${NC}"
    echo ""
    echo "Server URL: ws://localhost:7880"
    echo "API Key:    devkey"
    echo "API Secret: secret"
    echo ""
    echo "To view logs: docker logs -f livekit-dev-server"
    echo "To stop:      docker stop livekit-dev-server"

elif [ "$mode" == "2" ]; then
    # --- PROD MODE ---
    echo ""
    echo -e "${BLUE}Preparing Production Configuration...${NC}"
    
    if [ -f "livekit.yaml" ] || [ -f "docker-compose.yaml" ]; then
        echo -e "${RED}Warning: livekit.yaml or docker-compose.yaml already exist in this directory.${NC}"
        read -p "Overwrite? (y/N): " overwrite
        if [[ $overwrite != "y" && $overwrite != "Y" ]]; then
            echo "Aborting."
            exit 0
        fi
    fi

    echo "Launching LiveKit config generator..."
    docker run --rm -it -v $PWD:/output livekit/generate

    echo ""
    echo -e "${GREEN}✔ Configuration generated.${NC}"
    echo "Please review 'livekit.yaml' and 'docker-compose.yaml'."
    echo "To start the server, run:"
    echo -e "${BLUE}docker compose up -d${NC}"

else
    echo "Invalid selection. Exiting."
    exit 1
fi
