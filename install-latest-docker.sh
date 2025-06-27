#!/usr/bin/env bash
#
# install-latest-docker.sh
# Install the latest Docker Engine on Kali Linux/Debian-based systems
# Author: dr34mhacks
# https://github.com/dr34mhacks/useful-scripts-dump

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}[*] Removing any existing Docker repository configuration...${NC}"
sudo rm -f /etc/apt/sources.list.d/docker.list

echo -e "${GREEN}[*] Creating keyrings directory...${NC}"
sudo mkdir -p /etc/apt/keyrings

echo -e "${GREEN}[*] Downloading Docker GPG key...${NC}"
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo -e "${GREEN}[*] Adding Docker repository (Debian bookworm)...${NC}"
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo -e "${GREEN}[*] Updating package index...${NC}"
sudo apt update -y

echo -e "${GREEN}[*] Installing Docker Engine and related components...${NC}"
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo -e "${GREEN}[*] Enabling and starting Docker service...${NC}"
sudo systemctl enable docker
sudo systemctl start docker

echo -e "${GREEN}[*] Verifying Docker installation with hello-world...${NC}"
if sudo docker run --rm hello-world; then
    echo -e "${GREEN}[+] Docker installed and working correctly!${NC}"
else
    echo -e "${RED}[!] Docker verification failed.${NC}"
    exit 1
fi

# Prompt to remove hello-world image
read -p "Do you want to remove the 'hello-world' image now? (y/n): " RESP
if [[ "$RESP" =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}[*] Removing 'hello-world' image...${NC}"
    sudo docker rmi hello-world || true
fi

# Prompt to add user to docker group
read -p "Do you want to add your user ($USER) to the docker group to avoid using sudo? (y/n): " ADDGROUP
if [[ "$ADDGROUP" =~ ^[Yy]$ ]]; then
    sudo usermod -aG docker "$USER"
    echo -e "${GREEN}[+] Added $USER to the docker group. You must log out and log back in for this to take effect.${NC}"
fi

echo -e "${GREEN}[✓] All done! Docker is ready.${NC}"
