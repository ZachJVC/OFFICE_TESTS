#! /bin/bash
STM32_Programmer_CLI -l usb -c port=usb1 -w images/mcuapp_v1_5_3_48/mbrSwift.bin 0x8000000 -v
STM32_Programmer_CLI -l usb -c port=usb1 -w ./images/mcuapp_v1_5_3_48/swift-ab.bin 0x8006800 -g
