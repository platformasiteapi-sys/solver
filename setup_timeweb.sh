#!/bin/bash
# setup_timeweb.sh - Script to quickly deploy TexasSolver API on a new Ubuntu instance

# Exit immediately if a command exits with a non-zero status
set -e

echo "============================================="
echo " starting TexasSolver API Deployment..."
echo "============================================="

# 1. Update system and install required generic tools
echo "[1/4] Updating system packages..."
apt-get update -y
apt-get install -y curl wget git unzip apt-transport-https ca-certificates software-properties-common

# 2. Install Docker (using official convenience script)
echo "[2/4] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker is already installed."
fi

# 3. Setup Project Directory (Assuming we are cloning from a private repo or downloading an archive)
# Replace this block with your actual method of getting the code onto the server
# Example: git clone https://github.com/YourName/TexasSolverAPI.git /opt/texassolver
# For now, we will assume you SCP this folder to the server at /root/solver_project
# --- USER ACTION REQUIRED HERE ---

PROJECT_DIR="/root/solver_project"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: Project directory $PROJECT_DIR not found!"
    echo "Please upload the project files to $PROJECT_DIR before running this script."
    exit 1
fi

cd "$PROJECT_DIR"

# 4. We need the Linux release of TexasSolver to put inside the docker container
echo "[3/4] Downloading TexasSolver Linux Release..."
# Note: We create a linux_bin folder for the Dockerfile to copy from
if [ ! -f "linux_bin/console_solver" ]; then
    mkdir -p linux_bin
    echo "Downloading TexasSolver from GitHub Releases..."
    # The actual URL might change based on the release version on bupticybee/TexasSolver
    wget https://github.com/bupticybee/TexasSolver/releases/download/v0.3.3/TexasSolver-v0.3.3-Linux.zip -O solver.zip
    unzip solver.zip -d extracted_solver
    mv extracted_solver/console_solver linux_bin/
    rm -r extracted_solver solver.zip
    chmod +x linux_bin/console_solver
else
    echo "Linux solver binary already exists locally."
fi

# 5. Build and Run the Docker container
echo "[4/4] Building and starting the Docker container..."
docker build -t texassolver-api .

# Run the container on port 80 (standard HTTP port) mapping to port 8000 internally
# The server will automatically restart if the instance reboots
docker run -d --name solver_api_container -p 80:8000 --restart always texassolver-api

echo "============================================="
echo " Deployment Complete!"
echo " API is running on http://$(curl -s ifconfig.me)/api/solve"
echo " You can test it from your local machine."
echo "============================================="
