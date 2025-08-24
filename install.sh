#!/bin/bash

# ==============================================================================
# PingerPro - Beautiful Universal Installer
# Author: Gemini & You
# Version: 2.0
# This script auto-detects the environment (Debian/Ubuntu/Arch/Termux)
# and installs PingerPro with a user-friendly interface.
# ==============================================================================

# --- Configuration: Live URLs for PingerPro ---
CLI_URL="https://pingpro.vercel.app/pycli.py"
GUI_URL="https://pingpro.vercel.app/pygui.py"

# --- Color Codes for a beautiful output ---
C_RESET='\033[0m'
C_RED='\033[0;31m'
C_GREEN='\033[0;32m'
C_BLUE='\033[0;34m'
C_YELLOW='\033[1;33m'
C_CYAN='\033[0;36m'

# --- Helper Functions ---

# Function to print a step/stage message
step() {
    echo -e "\n${C_BLUE}==>${C_RESET} ${C_YELLOW}$1${C_RESET}"
}

# Function to print success or failure for a command
run() {
    local cmd_desc=$1
    shift
    local cmd=$@
    
    echo -ne "  ${C_CYAN}○${C_RESET} ${cmd_desc}... "
    
    # Run command and hide output
    OUTPUT=$($cmd 2>&1)
    
    if [ $? -eq 0 ]; then
        echo -e "\r${C_GREEN}✓${C_RESET} ${cmd_desc}... Done."
    else
        echo -e "\r${C_RED}✗${C_RESET} ${cmd_desc}... Failed."
        echo -e "${C_RED}Error details:${C_RESET}\n$OUTPUT"
        exit 1
    fi
}

# --- Environment Detection and Setup ---
SUDO_CMD=""
PKG_MANAGER=""
DISTRO=""
IS_TERMUX=false
INSTALL_PATH="/usr/local/bin"

# Detect Termux first, as it's a special case
if [[ "$PREFIX" == *"/com.termux"* ]]; then
    IS_TERMUX=true
    DISTRO="Termux"
    PKG_MANAGER="pkg"
    INSTALL_PATH="$PREFIX/bin"
else
    # If not Termux, check for sudo
    if [ "$EUID" -ne 0 ]; then
        SUDO_CMD="sudo"
    fi

    # Detect Linux distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" || "$ID" == "debian" || "$ID_LIKE" == "debian" ]]; then
            DISTRO="Debian/Ubuntu"
            PKG_MANAGER="apt-get"
        elif [[ "$ID" == "arch" || "$ID_LIKE" == "arch" ]]; then
            DISTRO="Arch Linux"
            PKG_MANAGER="pacman"
        else
            echo -e "${C_RED}Unsupported Linux distribution: $ID.${C_RESET}"
            exit 1
        fi
    else
        echo -e "${C_RED}Cannot detect Linux distribution.${C_RESET}"
        exit 1
    fi
fi


# --- Installation Functions ---

install_dependencies() {
    local type=$1 # cli or gui
    
    step "Installing Dependencies for ${DISTRO}"
    
    case "$PKG_MANAGER" in
        "apt-get")
            run "Updating package lists" $SUDO_CMD apt-get update -y
            run "Installing Python and Pip" $SUDO_CMD apt-get install -y python3 python3-pip curl
            if [ "$type" == "gui" ]; then
                run "Installing GUI libraries (GTK)" $SUDO_CMD apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0
            fi
            ;;
        "pacman")
            run "Updating package lists" $SUDO_CMD pacman -Syu --noconfirm
            run "Installing Python and Pip" $SUDO_CMD pacman -S --noconfirm python python-pip curl
            if [ "$type" == "gui" ]; then
                run "Installing GUI libraries (GTK)" $SUDO_CMD pacman -S --noconfirm python-gobject gtk3
            fi
            ;;
        "pkg") # Termux
            run "Updating package lists" pkg update -y
            run "Installing Python" pkg install -y python curl
            run "Installing Pip dependencies" python -m pip install --upgrade pip
            ;;
    esac
    
    run "Installing 'requests' library via Pip" python3 -m pip install requests
}

install_app() {
    local type=$1
    local url=$2
    local install_name="pingerpro-${type}"
    
    step "Downloading and Installing PingerPro"
    
    run "Downloading script" curl -fsSL -o "$install_name" "$url"
    run "Making script executable" chmod +x "$install_name"
    run "Moving script to executable path ($INSTALL_PATH)" $SUDO_CMD mv "$install_name" "$INSTALL_PATH/"
}

# --- Main Script Execution ---

# 1. Display beautiful header
clear
cat << "EOF"
    ____  _                ____
   / __ \(_)___  ___  ____/ __ \_      ______  ____
  / /_/ / / __ \/ _ \/ __/ /_/ / | /| / / __ \/ __ \
 / ____/ / / / /  __/ /_/ ____/| |/ |/ / /_/ / /_/ /
/_/   /_/_/ /_/\___/\__/_/     |__/|__/\____/ .___/
                                          /_/
EOF
echo -e "${C_GREEN}       Welcome to the PingerPro Universal Installer${C_RESET}"
echo "--------------------------------------------------------"

# 2. Ask user for choice
step "Choose Installation Type"

if $IS_TERMUX; then
    echo -e "${C_YELLOW}Note:${C_RESET} GUI version is not available on Termux. CLI will be installed."
    choice=1
else
    echo "1) CLI Version (for servers and terminal lovers)"
    echo "2) GUI Version (for a graphical desktop application)"
    
    while true; do
        read -p "Please enter your choice (1 or 2): " choice
        case $choice in
            1|2) break;;
            *) echo -e "${C_RED}Invalid choice. Please enter 1 or 2.${C_RESET}";;
        esac
    done
fi

# 3. Execute installation based on choice
if [ "$choice" -eq 1 ]; then
    install_dependencies "cli"
    install_app "cli" "$CLI_URL"
    
    echo -e "\n--------------------------------------------------------"
    echo -e "${C_GREEN}✓ PingerPro CLI Installed Successfully!${C_RESET}"
    echo "You can now run the application from anywhere."
    echo -e "Usage example: ${C_YELLOW}pingerpro-cli https://example.com -i 10${C_RESET}"
    echo "--------------------------------------------------------"
else
    install_dependencies "gui"
    install_app "gui" "$GUI_URL"

    echo -e "\n--------------------------------------------------------"
    echo -e "${C_GREEN}✓ PingerPro GUI Installed Successfully!${C_RESET}"
    echo "You can now run the application from your terminal."
    echo -e "To start, simply type: ${C_YELLOW}pingerpro-gui${C_RESET}"
    echo "--------------------------------------------------------"
fi
