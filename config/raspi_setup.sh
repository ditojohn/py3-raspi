#!/bin/bash

# Manual pre-installation steps required to be completed:
#
# Setup Git projects and configuration files
# cd ~; mkdir projects; cd projects; mkdir raspi; cd raspi
# git init
# git config --global user.email "you@example.com"
# git config --global user.name "Your Name"
# git remote add raspi https://github.com/ditojohn/raspi.git
# git pull raspi master
#
# Localization, Time Zone and Keyboard Configuration
#
# Reboot

echo "Setting up Raspberry Pi 2 ..."
SETUP_TS=$(date +"%Y%m%d%H%M%S")
SETUP_DIR=~/projects/raspi/config


echo "---------------------------------------------------------"
echo "WiFi configuration - Setting up ..."
echo "Configure WiFi association from the desktop system tray."

# WiFi configuration is included from NOOBS 1.7.0 upwards.
# For previous versions, use steps provided below.

#cd ~
#sudo apt-get install wpagui#

#SETUP_CFG_DIR=/etc/network
#SETUP_CFG_FIL=interfaces
#sudo cp -p ${SETUP_CFG_DIR}/${SETUP_CFG_FIL} ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}.${SETUP_TS}.bak
#sudo cat ${SETUP_DIR}/${SETUP_CFG_FIL} | sudo tee ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}#

#SETUP_CFG_DIR=/etc/wpa_supplicant
#SETUP_CFG_FIL=wpa_supplicant.conf
#sudo cp -p ${SETUP_CFG_DIR}/${SETUP_CFG_FIL} ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}.${SETUP_TS}.bak
#sudo cat ${SETUP_DIR}/${SETUP_CFG_FIL} | sudo tee ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}
#sudo chmod 600 ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}
#sudo adduser pi netdev#

#echo "WiFi configuration - Manual SSID and Password update"
#echo "Use 'sudo vi /etc/network/interfaces' to update WiFi SSID and password manually."

read -p "Press any key when ready ..." -n1 -s; echo ""
echo "WiFi configuration - Setup complete"
echo "---------------------------------------------------------"

echo "---------------------------------------------------------"
echo "VNC configuration - Setting up ..."
cd ~
sudo apt-get install x11vnc
x11vnc -storepasswd
cd ~/.config; mkdir autostart; cd autostart

echo "VNC configuration - Creating autostart entry"
SETUP_CFG_DIR=~/.config/autostart
SETUP_CFG_FIL=x11vnc.desktop
sudo touch ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}
sudo cat ${SETUP_DIR}/${SETUP_CFG_FIL} | sudo tee ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}

echo "VNC configuration - Boot config update"
SETUP_CFG_DIR=/boot
SETUP_CFG_FIL=config.txt
sudo cp -p ${SETUP_CFG_DIR}/${SETUP_CFG_FIL} ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}.${SETUP_TS}.bak
sudo cat ${SETUP_DIR}/boot_config_addendum.txt | sudo tee -a ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}

echo "VNC configuration - Manual 'Desktop Autologin' update"
echo "Use 'sudo raspi-config' to select '3 Boot Options > B4 Desktop Autologin' option manually."
read -p "Press any key when ready ..." -n1 -s; echo ""
echo "VNC configuration - Setup complete"
echo "---------------------------------------------------------"


echo "---------------------------------------------------------"
echo "Custom packages - Setting up ..."
sudo apt-get install ksh
sudo apt-get install python-bs4
echo "Custom packages - Setup complete"
echo "---------------------------------------------------------"


echo "---------------------------------------------------------"
echo "bashrc - Setting up ..."
cd ~

SETUP_CFG_DIR=~
SETUP_CFG_FIL=.bashrc
cp -p ${SETUP_CFG_DIR}/${SETUP_CFG_FIL} ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}.${SETUP_TS}.bak
cat ${SETUP_DIR}/bashrc_addendum.txt >> ${SETUP_CFG_DIR}/${SETUP_CFG_FIL}
echo "bashrc - Setup complete"
echo "---------------------------------------------------------"

# Manual post-installation steps required to be completed:
#
# Reboot
#
