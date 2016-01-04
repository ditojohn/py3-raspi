#!/bin/bash

# Manual pre-installation steps required to be completed:
#
# Setup Git projects and configuration files
# cd ~; mkdir projects; cd projects; mkdir raspi; cd raspi
# git init
# git remote add raspi https://github.com/ditojohn/raspi.git
# git pull raspi master
#
# Localization, Time Zone and Keyboard Configuration
#
# Reboot

echo "Setting up Raspberry Pi 2 ..."
SETUP_TS=$(date +"%Y-%m-%d-%T")
SETUP_DIR=~/projects/raspi/config

echo "WiFi configuration - Setting up ..."
cd ~
sudo apt-get install wpagui

SETUP_CFG_DIR=/etc/network
SETUP_CFG_FIL=interfaces
sudo cp -p ${SETUP_CFG_DIR}/${SETUP_CFG_FIL} ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}.${SETUP_TS}.bak
sudo cat ${SETUP_DIR}/${SETUP_CFG_FIL} > ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}

SETUP_CFG_DIR=/etc/wpa_supplicant
SETUP_CFG_FIL=wpa_supplicant.conf
sudo cp -p ${SETUP_CFG_DIR}/${SETUP_CFG_FIL} ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}.${SETUP_TS}.bak
sudo cat ${SETUP_DIR}/${SETUP_CFG_FIL} > ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}
sudo chmod 600 ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}
sudo adduser pi netdev

echo "WiFi configuration - Manual SSID and Password update"
echo "Use 'sudo vi /etc/network/interfaces' to update WiFi SSID and password manually."
read -p "Press any key when ready ..." -n1 -s; echo ""
echo "WiFi configuration - Setup complete"


echo "VNC configuration - Setting up ..."
cd ~
sudo apt-get install x11vnc
x11vnc -storepasswd
cd ~/.config; mkdir autostart; cd autostart

SETUP_CFG_DIR=~/.config/autostart
SETUP_CFG_FIL=x11vnc.desktop
sudo touch ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}
sudo cat ${SETUP_DIR}/${SETUP_CFG_FIL} > ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}

SETUP_CFG_DIR=/boot
SETUP_CFG_FIL=config.txt
sudo cp -p ${SETUP_CFG_DIR}/${SETUP_CFG_FIL} ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}.${SETUP_TS}.bak
# Uncomment hdmi_force_hotplug=1 in /boot/config.txt
sudo cat ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}.${SETUP_TS}.bak | awk '/hdmi_force_hotplug=1/ {gsub(/^#/, "", $0)} {print $0}' > ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}

echo "VNC configuration - Manual 'Boot to desktop' update"
echo "Use 'sudo raspi-config' to configure 'Boot to desktop' option manually."
read -p "Press any key when ready ..." -n1 -s; echo ""
echo "VNC configuration - Setup complete"


echo "Custom packages - Setting up ..."
sudo apt-get install ksh
echo "Custom packages - Setup complete"


echo "User Profile - Setting up ..."
cd ~

SETUP_CFG_DIR=~
SETUP_CFG_FIL=.profile
sudo cp -p ${SETUP_CFG_DIR}/${SETUP_CFG_FIL} ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}.${SETUP_TS}.bak
echo "" >> ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}
echo '# setup profile customization' >> ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}
echo '. ~/projects/raspi/config/.profile' >> ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}
echo "User Profile - Setup complete"

# Manual post-installation steps required to be completed:
#
# Reboot
#
