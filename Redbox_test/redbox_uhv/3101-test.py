from Redbox_driver import *
import time
import sys
#import fcntl
import os
import math

def toContinue():
  answer = input('Continue [yY]? ')
  if (answer == 'y' or answer == 'Y'):
    return True
  else:
    return False

def main():
  # initalize the class
  try:
    usb3100 = usb_3101()
  except Exception as e:
    print(e)

    print('No USB-31XX device found')
    return

  print("Manufacturer: %s" % usb3100.h.get_manufacturer_string())
  print("Product: %s" % usb3100.h.get_product_string())
  print("Serial No: %s" % usb3100.h.get_serial_number_string())

  # config mask 0x01 means all inputs
  usb3100.DConfigPort(usb3100.DIO_DIR_OUT)
  usb3100.DOut(0)

  # Configure all analog channels for 0-10V output
  for i in range(8):
    usb3100.AOutConfig(i, usb3100.UP_10_00V)
    print('channel = ', i, 'slope = ', format(usb3100.CalTable[i].slope,'.4f'), 'intercept = ',format(usb3100.CalTable[i].intercept,'.4f'))
    
  channel = 0
  gain = 0
  voltage = 0.0
  value = usb3100.volts(gain, voltage)
  usb3100.AOutConfig(channel, gain)
  usb3100.AOut(channel, value, 0)

  while True:
    print("\nUSB 31XX Testing")
    print("----------------")
    print("Hit 'a' for analog output of different levels.")
    print("Hit 'o' for analog output.")
    print("Hit 'b' to blink")
    print("Hit 'c' to test counter")
    print("Hit 'd' to test digital output")
    print("Hit 'i' to test digital input")
    print("Hit 'I' for information")
    print("Hit 'e' to exit")
    print("Hit 'g' to get serial number")
    print("Hit 'r' to reset")
    print("Hit 's' to get status")
    print("Hit 'R' to read memory")
    print("Hit 'x' for Jonas AES energy Test")

    ch = input('\n')
    if ch == 'b':
      count = int(input('Enter number of times to blink: '))
      usb3100.Blink(count)
    elif ch == 'a':
      print('Testing the analog output ...')
      chan = int(input('Enter channel [0-15]: '))
      for value in range(0,0xfff0,0xf):
        usb3100.AOut(chan, value, 0)
      usb3100.AOut(chan, 0x0, 0)
    elif ch == 'o':
      print('Testing the analog output for a single channel.')
      channel = int(input('Enter channel [0-15]: '))
      gain = int(input('Enter a range: 0 = 0-10V, 1 = +/- 10V, 2 = 0-20mA'))
      voltage = float(input('Enter a voltage: '))
      value = usb3100.volts(gain, voltage)
      usb3100.AOutConfig(channel, gain)
      usb3100.AOut(channel, value, 0)
    elif ch == 'c':
      print('Connect CTR and DIO0')
      print('Hit s <CR> to stop.')
      usb3100.CInit()
      usb3100.DConfigPort(usb3100.DIO_DIR_OUT)
      time.sleep(1.)
      flag = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
      fcntl.fcntl(sys.stdin, fcntl.F_SETFL, flag|os.O_NONBLOCK)
      while True:
        usb3100.DOut(0x1)
        time.sleep(0.2)
        usb3100.DOut(0x0)
        time.sleep(0.2)
        print('Counter = ', usb3100.CIn())
        c = sys.stdin.readlines()
        if (len(c) != 0):
          fcntl.fcntl(sys.stdin, fcntl.F_SETFL, flag)
          break
    elif ch == 'd':
      print('Testing Digital I/O ...')
      value = int(input('Enter a byte value [0-0xff]: '),16)
      usb3100.DConfigPort(usb3100.DIO_DIR_OUT)
      usb3100.DOut(value & 0xff)
    elif ch == 'i':
      print('Testing Digital Input ...')
      usb3100.DConfigPort(usb3100.DIO_DIR_IN)
      value = usb3100.DIn()
      print('Digital Input =', hex(value))
    elif ch == 'e':
      usb3100.exit()
      exit(0)
    elif ch == 'I':
      print("Manufacturer: %s" % usb3100.h.get_manufacturer_string())
      print("Product: %s" % usb3100.h.get_product_string())
      print("Serial No: %s" % usb3100.h.get_serial_number_string())
    elif ch == 'g':
      print("Serial No: %s" % usb3100.h.get_serial_number_string())
    elif ch == 'r':
      usb3100.Reset()
      return 0
    elif ch == 'R':
      print('reading from EEPROM: ')
      for i in range(0x0, 0xff, 32):
        memory = usb3100.MemRead(i, 32)
        for j in range(0, 32, 2):
          try:
            print('address =', hex(j+i), '\tvalue = ', hex(memory[j]),'\t\taddress =', hex(j+i+1), '\tvalue = ', hex(memory[j+1]))
            print(memory)
          except IndexError:
            pass
      print(' ')
      print('reading from FLASH: ')
      for i in range(0x0100,0x02ff,32):
        memory = usb3100.MemRead(i, 32)
        for j in range(0, 32, 2):
          try:
            print('address =', hex(j+i), '\tvalue = ', hex(memory[j]),'\t\taddress =', hex(j+i+1), '\tvalue = ', hex(memory[j+1]))
          except IndexError:
            pass
    elif ch == 's':
      print('Status = ',hex(usb3100.Status()))
    elif ch == 'x':
      channel = 2
      gain = int(0)
      voltage = 0.004 * 350 - 0.01873
      value = usb3100.volts(gain, voltage)
      usb3100.AOutConfig(channel, gain)
      usb3100.AOut(channel, value, 0)

      for eV in range(0, 10, 1):
        voltage = 0.004 * eV - 0.0187 
        value = usb3100.volts(gain, voltage)
        value = value + 0.9878 + 335.3961
        value = 20000 + eV * 1000
        usb3100.AOutConfig(channel, gain)
        usb3100.AOut(channel, value, 0)
        time.sleep(5)

      voltage = 0
      #value = usb3100.volts(gain, voltage)
      #usb3100.AOutConfig(channel, gain)
      #usb3100.AOut(channel, value, 0)



'''
Product: USB-3101
Serial No: 00071787
channel =  0 slope =  0.9878 intercept =  335.3961
channel =  1 slope =  0.9877 intercept =  310.7381
channel =  2 slope =  0.9878 intercept =  247.1620
channel =  3 slope =  0.9879 intercept =  261.4377
channel =  4 slope =  nan intercept =  nan
channel =  5 slope =  nan intercept =  nan
channel =  6 slope =  nan intercept =  nan
channel =  7 slope =  nan intercept =  nan'''
      
if __name__ == "__main__":
  main()
