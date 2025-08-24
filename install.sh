#!/bin/bash

# --- Configuration: Live URLs for PingerPro ---
CLI_URL="https://pingpro.vercel.app/pycli.py"
GUI_URL="https://pingpro.vercel.app/pygui.py"
# -----------------------------------------------

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print messages
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 1. Check for root privileges
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root. Please use 'sudo'."
    fi
}

# 2. Detect the Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        if [[ "$DISTRO" == "ubuntu" || "$DISTRO" == "debian" || "$ID_LIKE" == "debian" ]]; then
            DISTRO="debian"
        elif [[ "$DISTRO" == "arch" || "$ID_LIKE" == "arch" ]]; then
            DISTRO="arch"
        else
            error "Unsupported distribution: $ID. This script supports Debian, Ubuntu, and Arch Linux."
        fi
    else
        error "Cannot detect Linux distribution."
    fi
    info "Detected distribution: $DISTRO"
}

# 3. Install dependencies based on distro and type (cli/gui)
install_dependencies() {
    local type=$1
    info "Updating package lists..."
    
    case "$DISTRO" in
        "debian")
            apt-get update -y
            info "Installing core dependencies: python3, python3-pip..."
            apt-get install -y python3 python3-pip curl || error "Failed to install core dependencies."
            if [ "$type" == "gui" ]; then
                info "Installing GUI dependencies: GTK..."
                apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 || error "Failed to install GUI dependencies."
            fi
            ;;
        "arch")
            pacman -Syu --noconfirm
            info "Installing core dependencies: python, python-pip..."
            pacman -S --noconfirm python python-pip curl || error "Failed to install core dependencies."
            if [ "$type" == "gui" ];
                info "Installing GUI dependencies: GTK..."
                pacman -S --noconfirm python-gobject gtk3 || error "Failed to install GUI dependencies."
            fi
            ;;
    esac
    
    info "Installing Python libraries: requests..."
    pip install --upgrade pip
    pip install requests || error "Failed to install 'requests' Python library."
}

# 4. Download and install the application script
install_app() {
    local type=$1
    local url=$2
    local install_path="/usr/local/bin/pingerpro-${type}"

    info "Downloading PingerPro ${type} script from your URL..."
    curl -fsSL -o "$install_path" "$url" || error "Failed to download the script from ${url}."
    
    info "Making the script executable..."
    chmod +x "$install_path" || error "Failed to make the script executable."
}

# --- Main function to run the installer ---
main() {
    check_root
    
    echo -e "${GREEN}--- Welcome to the PingerPro Installer ---${NC}"
    
    detect_distro
    
    echo ""
    warn "You can choose to install the Command-Line (CLI) or Graphical (GUI) version."
    echo "1) CLI Version (for servers, Termux, and terminal users)"
    echo "2) GUI Version (for a graphical desktop application)"
    
    local choice
    while true; do
        read -p "Please enter your choice (1 or 2): " choice
        case $choice in
            1|2) break;;
            *) echo -e "${RED}Invalid choice. Please enter 1 or 2.${NC}";;
        esac
    done

    if [ "$choice" -eq 1 ]; then
        info "You have chosen the CLI version."
        install_dependencies "cli"
        install_app "cli" "$CLI_URL"
        echo ""
        info "PingerPro CLI installed successfully!"
        info "To run it, type: ${YELLOW}pingerpro-cli https://your-website.com${NC}"
    else
        info "You have chosen the GUI version."
        install_dependencies "gui"
        install_app "gui" "$GUI_URL"
        echo ""
        info "PingerPro GUI installed successfully!"
        info "To run it, type: ${YELLOW}pingerpro-gui${NC} in your terminal."
    fi
    
    echo -e "${GREEN}Installation complete. Thank you for using PingerPro!${NC}"
}

# Run the main function
main
