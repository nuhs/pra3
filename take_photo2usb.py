import os
import time
import json
import requests
import numpy as np
import cv2
import sys
import subprocess
from farmware_tools import device, app

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

def folder_name():
    foldername = 'X{}Y{}'.format(position_x,position_y)
    os.system("mkdir -p /tmp/usb/1/{}".format(foldername))
    return foldername

def image_filename():
    'Prepare filename with timestamp.'
    epoch = str(time.strftime("%Y-%m-%d_%H-%M"))  #Changed the timestamp to "YYYY.MM.DD_H-M"
    filename = 'X{}Y{}_{}.jpg'.format(position_x,position_y,epoch)     #Add plant_name, x-and y-positions and timestamp
    return filename
    
def detect_usb_name():
    partitionsFile = open("/proc/partitions")
    lines = partitionsFile.readlines()[2:]#Skips the header lines
    for line in lines:
        words = [x.strip() for x in line.split()]
        minorNumber = int(words[1])
        deviceName = words[3]
    return deviceName

def mount_usb_drive():
   if "mmcblk" in hdd_path:
     log("No USB found","error")
     sys.exit(4)
   if not os.path.exists('/tmp/usb/1'):
       os.system("mkdir -p /tmp/usb/1" )
   os.system("mount -t vfat /dev/%s /tmp/usb/1 -o uid=1000,gid=1000,utf8,dmask=027,fmask=137"% hdd_path) 
   time.sleep(1)
   #log("USB mounted","success")

def unmount_usb_drive():
   if os.path.exists('/tmp/usb/1'):
       ret_code_unmount = os.system("sudo unmount /dev/%s"% hdd_path)
       time.sleep(2)
    #   log(ret_code_unmount,"info")
    #   log("USB unmounted","success")

def upload_path(filename):
    'Filename with path for uploading an image.'
    try:
        images_dir = '/tmp/usb/1/{}/{}'.format(hdd_path,folder_name())
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
            ["raspistill", "-w", "640", "-h", "320", "-o", filename_path])
        if retcode == 0:
            log("Image saved: {}".format(filename_path),"success")
        else:
            log("Problem getting image.", "error")
    except OSError:
        log("Raspberry Pi Camera not detected.", "error")

if __name__ == '__main__':
    position_x = int(round(device.get_current_position('x'))) # Actual X-Position
    position_y = int(round(device.get_current_position('y'))) # Actual Y-Position

    hdd_path = detect_usb_name()
    mount_usb_drive()
    rpi_camera_photo()
    
    unmount_usb_drive()
