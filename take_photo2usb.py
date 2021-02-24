#!/usr/bin/env python

import os
import time
import json
import requests
import numpy as np
import cv2
import sys
import subprocess
from farmware_tools import device, app


try:
    points =  app.get_plants()         #Get all plants from webapp
    position_x = int(round(device.get_current_position('x')))      #Actual X-Position
    position_y = int(round(device.get_current_position('y')))      #Actual Y-Position
    all_plants = []
except KeyError:
     log("Loading points/positions failed","error")

def farmware_api_url():

    major_version = int(os.getenv('FARMBOT_OS_VERSION', '0.0.0')[0])
    base_url = os.environ['FARMWARE_URL']
    return base_url + 'api/v1/' if major_version > 5 else base_url

def log(message, message_type):
    'Send a message to the log.'
    try:
        os.environ['FARMWARE_URL']
    except KeyError:
        print(message)
    else:
        log_message = '[take-photo] ' + str(message)
        headers = {
            'Authorization': 'bearer {}'.format(os.environ['FARMWARE_TOKEN']),
            'content-type': "application/json"}
        payload = json.dumps(
            {"kind": "send_message",
             "args": {"message": log_message, "message_type": message_type}})
        requests.post(farmware_api_url() + 'celery_script',
                      data=payload, headers=headers)

        



def image_filename():
    'Prepare filename with timestamp.'
    epoch = str(time.strftime("%Y-%m-%d-%H-%M"))  #Changed the timestamp to "YYYY.MM.DD_H-M"
    filename = '{}_X{}Y{}_{}.jpg'.format(""Plant, position_x, position_y,epoch)     #Add plant_name, x-and y-positions and timestamp
    return filename



def detect_usb_name():
    partitionsFile = open("/proc/partitions")
    lines = partitionsFile.readlines()[2:]#Skips the header lines
    for line in lines:
        words = [x.strip() for x in line.split()]
        minorNumber = int(words[1])
        deviceName = words[3]
 #       if minorNumber % 16 == 0:
 #           path = "/sys/class/block/" + deviceName
 #           if os.path.islink(path):
 #               if os.path.realpath(path).find("/usb") > 0:
 #                   log("/dev/%s" % deviceName,"info")
    return deviceName


def mount_usb_drive():
   if "mmcblk" in sdx_path:
     log("No USB found","error")
     sys.exit(4)
   if not os.path.exists('/tmp/usb/1'):
       os.system("mkdir -p /tmp/usb/1" )
   os.system("mount -t vfat /dev/%s /tmp/usb/1 -o uid=1000,gid=1000,utf8,dmask=027,fmask=137"% sdx_path) 
   time.sleep(1)
   #log("USB mounted","success")

def unmount_usb_drive():
   if os.path.exists('/tmp/usb/1'):
       ret_code_unmount = os.system("sudo unmount /dev/%s"% sdx_path)
       time.sleep(2)
    #   log(ret_code_unmount,"info")
    #   log("USB unmounted","success")

        
def upload_path(filename):
    'Filename with path for uploading an image.'
    try:
        images_dir = '/tmp/usb/1/{}'.format(deviceName)
            #os.environ['IMAGES_DIR']
    except KeyError:
        images_dir = '/tmp/images'
    path = images_dir + os.sep + filename
    return path

def rpi_camera_photo():
    'Take a photo using the Raspberry Pi Camera.'
    from subprocess import call
    try:
        filename_path = upload_path(image_filename())
        retcode = call(
            ["raspistill", "-w", "640", "-h", "480", "-o", filename_path])
        if retcode == 0:
            log("Image saved: {}".format(filename_path),"success")
        else:
            log("Problem getting image.", "error")
    except OSError:
        log("Raspberry Pi Camera not detected.", "error")

if __name__ == '__main__':
    try:
        CAMERA = os.environ['camera']
    except (KeyError, ValueError):
        CAMERA = 'USB'  # default camera

    sdx_path = detect_usb_name()
    mount_usb_drive()
    if 'RPI' in CAMERA:
        rpi_camera_photo()
    unmount_usb_drive()
