#!/bin/bash

set -e

# 1. Create and activate Python virtual environment
python3 -m venv mifire
source mifire/bin/activate

# 2. Update and upgrade system packages
sudo apt update && sudo apt upgrade -y

# 3. Check OS release and platform architecture
. /etc/os-release
ARCH=$(uname -m)
echo "Detected OS: $ID $VERSION_CODENAME ($VERSION_ID), Architecture: $ARCH"

# 4. Download and unzip driver package
DRIVER_URL="https://www.acs.com.hk/download-driver-unified/14214/acsccid-linux-bin-1.1.11-20240328.zip"
DRIVER_ZIP="acsccid-linux-bin-1.1.11-20240328.zip"
DRIVER_DIR="acsccid-linux-bin-1.1.11-20240328"

if [ ! -f "$DRIVER_ZIP" ]; then
    wget "$DRIVER_URL"
fi

if [ ! -d "$DRIVER_DIR" ]; then
    unzip "$DRIVER_ZIP"
fi

cd "$DRIVER_DIR"

# 5. Decision tree for driver installation
install_deb() {
    sudo dpkg -i "$1"
    sudo apt-get install -f -y
}

install_rpm() {
    sudo rpm -ivh --replacepkgs "$1"
}

case "$ID" in
    ubuntu)
        case "$VERSION_CODENAME" in
            jammy) PKG="ubuntu/jammy/libacsccid1_1.1.11-1~bpo22.04.1_amd64.deb" ;;
            focal) PKG="ubuntu/focal/libacsccid1_1.1.11-1~bpo20.04.1_amd64.deb" ;;
            bionic) PKG="ubuntu/bionic/libacsccid1_1.1.11-1~bpo18.04.1_amd64.deb" ;;
            xenial) PKG="ubuntu/xenial/libacsccid1_1.1.11-1~bpo16.04.1_amd64.deb" ;;
            trusty) PKG="ubuntu/trusty/libacsccid1_1.1.11-1~bpo14.04.1_amd64.deb" ;;
            mantic) PKG="ubuntu/mantic/libacsccid1_1.1.11-1~bpo23.10.1_amd64.deb" ;;
            *)
                echo "Unsupported Ubuntu version: $VERSION_CODENAME"
                exit 1
                ;;
        esac
        install_deb "$PKG"
        ;;
    debian)
        case "$VERSION_CODENAME" in
            bookworm) PKG="debian/bookworm/libacsccid1_1.1.11-1~bpo12+1_amd64.deb" ;;
            bullseye) PKG="debian/bullseye/libacsccid1_1.1.11-1~bpo11+1_amd64.deb" ;;
            buster) PKG="debian/buster/libacsccid1_1.1.11-1~bpo10+1_amd64.deb" ;;
            *)
                echo "Unsupported Debian version: $VERSION_CODENAME"
                exit 1
                ;;
        esac
        install_deb "$PKG"
        ;;
    raspbian)
        case "$VERSION_CODENAME" in
            bookworm) PKG="raspbian/bookworm/libacsccid1_1.1.11-1~bpo12+1_armhf.deb" ;;
            bullseye) PKG="raspbian/bullseye/libacsccid1_1.1.11-1~bpo11+1_armhf.deb" ;;
            buster) PKG="raspbian/buster/libacsccid1_1.1.11-1~bpo10+1_armhf.deb" ;;
            *)
                echo "Unsupported Raspbian version: $VERSION_CODENAME"
                exit 1
                ;;
        esac
        install_deb "$PKG"
        ;;
    fedora)
        case "$VERSION_ID" in
            38) PKG="fedora/38/pcsc-lite-acsccid-1.1.11-1.fc38.x86_64.rpm" ;;
            39) PKG="fedora/39/pcsc-lite-acsccid-1.1.11-1.fc39.x86_64.rpm" ;;
            40) PKG="fedora/40/pcsc-lite-acsccid-1.1.11-1.fc40.x86_64.rpm" ;;
            *)
                echo "Unsupported Fedora version: $VERSION_ID"
                exit 1
                ;;
        esac
        install_rpm "$PKG"
        ;;
    opensuse*)
        case "$VERSION_ID" in
            15.5) PKG="opensuse/15.5/pcsc-acsccid-1.1.11-lp155.100.1.x86_64.rpm" ;;
            15.6) PKG="opensuse/15.6/pcsc-acsccid-1.1.11-lp156.100.1.x86_64.rpm" ;;
            *)
                echo "Unsupported openSUSE version: $VERSION_ID"
                exit 1
                ;;
        esac
        install_rpm "$PKG"
        ;;
    centos|rhel)
        case "$VERSION_ID" in
            6) PKG="epel/6/pcsc-lite-acsccid-1.1.11-1.el6_10.x86_64.rpm" ;;
            7) PKG="epel/7/pcsc-lite-acsccid-1.1.11-1.el7.x86_64.rpm" ;;
            8) PKG="epel/8/pcsc-lite-acsccid-1.1.11-1.el8.x86_64.rpm" ;;
            9) PKG="epel/9/pcsc-lite-acsccid-1.1.11-1.el9.x86_64.rpm" ;;
            *)
                echo "Unsupported CentOS/RHEL version: $VERSION_ID"
                exit 1
                ;;
        esac
        install_rpm "$PKG"
        ;;
    sles|sle)
        case "$VERSION_ID" in
            11) PKG="sle/11sp4/pcsc-acsccid-1.1.11-100.1.x86_64.rpm" ;;
            12) PKG="sle/12/pcsc-acsccid-1.1.11-100.1.x86_64.rpm" ;;
            15) PKG="sle/15/pcsc-acsccid-1.1.11-100.1.x86_64.rpm" ;;
            *)
                echo "Unsupported SLE version: $VERSION_ID"
                exit 1
                ;;
        esac
        install_rpm "$PKG"
        ;;
    *)
        echo "Unsupported OS: $ID"
        exit 1
        ;;
esac

cd ..

# 6. Install Python dependencies
pip install -r requirements.txt

# 7. Run the application
python app.py