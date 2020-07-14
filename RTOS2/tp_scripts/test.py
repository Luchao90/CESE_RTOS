import serial
import random
import time
import sys
import signal
import crc8

import sys

from serial_init import *
from frame_c2 import *

"""
------------------------------------------------------------------------------
requirements:
this script needs pyserial
refer to https://pyserial.readthedocs.io/en/latest/pyserial.html for installing instructions
------------------------------------------------------------------------------
script instructions:

execute:
python test_random.py
------------------------------------------------------------------------------
"""

# config -------------------------------------------------------------------
DEFAULT_BAURDATE = 115200
start_of_msg = '('
end_of_msg = ')

# Variables globales con valores iniciales ------------------------------------
def signal_handler(sig, frame):
    print('Se pulso Ctrl+C!, saliendo del programa!')
    try:
        ser.close()
    except:
        pass
    else:
        print('Se cerro el puerto OK.')
    sys.exit(0)

# Funciones -------------------------------------------------------------------

def sendData(command, payload , som , eom , valido = False ):

   payload = command + payload
   payload = c2_add_crc(payload, valido)
   payload = c2_add_delimiters(payload, som , eom)

   print ("Enviando: ",  payload)
   ser.write(str(payload).encode())
   time.sleep(0.3)

   try:
      #print ("Leyendo ...")
      readOut = ser.read(ser.in_waiting).decode('ascii')
      #time.sleep(1)
      print ("Recibido: ", readOut)
      return readOut
   except:
      pass

   return


# comando help: Imprime la lista de comandos
def command_list():
   print( "Comandos disponibles -----------------------------------------------" )
   print( "   'h' (help) imprime esta lista de comandos." )
   print( "   'q' (quit) Salir del programa." )
   print( "   '1' Enviar trama corta mayusculizar." )
   print( "   '2' Enviar trama larga minusculizar." )
   print( "   '3' Enviar trama con crc erroneo." )
   print( "   '4' Enviar trama con caracteres erroneos." )
   print( "   '5' Enviar trama con comando invalido" )
   print( "   '6' Enviar trama sin cierre ')'" )
   print( "   '7' Enviar trama con caracteres separados a mas de 50ms " )
   print( "   '8' Enviar trama mas larga que el tamanio del buffer" )
   print( "   'a' Correr todos los tests." )
   print( "--------------------------------------------------------------------\n" )
   return

# comando 1:  Trama corta mayusculizar
def cmd_1():
   data = 'asdFghJ'
   retData = sendData('M',data, '(',')',True )

   data = c2_add_crc(data.upper())
   data = c2_add_delimiters(data,'(',')')

   if retData == data:
      print("PASS")
   else:
      print("FAIL")

   return

# comando 2:  Trama larga minusculizar
def cmd_2():
   data = 'asdFghJasdFghJasdFghJasdFghJ'
   retData = sendData('m', data ,'(',')',True )

   data = c2_add_crc(data.lower())
   data = c2_add_delimiters(data,'(',')')

   if retData == data:
      print("PASS")
   else:
      print("FAIL")

   return

# comando 3: Checksum erroneo
def cmd_3():
   data = 'asdFghJ'

   retData = sendData('m', data, '(',')', False)

   if retData == '':
      print("PASS")
   else:
      print("FAIL")

   return

# comando 4: Enviar trama con caracteres erroneos.
def cmd_4():
   data = 'as!Fg5J'
   retData = sendData('m', data, '(',')',True )

   expected = 'ERROR'
   expected = c2_add_crc(expected)
   expected = c2_add_delimiters(expected, '(', ')')

   if retData == expected:
      print("PASS")
   else:
      print("FAIL")

   return

# comando 5: Enviar trama con comando invalido
def cmd_5():
   data = 'asdFghJ'
   retData = sendData('p', data, '(',')',True )

   expected = 'ERROR'
   expected = c2_add_crc(expected)
   expected = c2_add_delimiters(expected, '(', ')')

   if retData == expected:
      print("PASS")
   else:
      print("FAIL")

   return

# comando 6: Enviar trama sin cierre ')'
def cmd_6():
   data = 'asdFghJ'
   retData = sendData('p', data, '(','',True )

   expected = ''

   if retData == expected:
      print("PASS")
   else:
      print("FAIL")

   return

# comando 7: Enviar trama con caracteres separados a mas de 50ms
def cmd_7():
   data1 = 'asdFghJ'
   data2 = 'asdFghJ'

   retData1 = sendData('m', data1, '(','',True )
   time.sleep(0.06)
   retData2 = sendData('', data2, '',')',True )

   expected = ''

   if (retData1 == expected) & (retData2 == expected):
      print("PASS")
   else:
      print("FAIL")

   return

# comando 8:  Enviar trama mas larga que el tamano del buffer
def cmd_8():
    data = 'asdFghJasdFghJasdFghJasdFghJasdFghJasdFghJasdFghJasdFghJasdFghJasdFghJasdFghJasdFghJasdFghJasdFghJasdFghJasdFghJ'

    retData = sendData('m', data ,'(',')',True )

    if retData == '':
        print("PASS")
    else:
        print("FAIL")

    return

# Inicializa y abre el puertos serie ------------------------------------------
def uart_main():

    #platform
    print("Plataforma: " + sys.platform )

    #seleccion de puerto serie
    port = serial_choose()

    #declaro el objeto de puerto serie (sin abrirlo)
    ser = serial.Serial()

    #parametros del puerto serie
    ser.port = port
    ser.baudrate = DEFAULT_BAURDATE
    ser.bytesize = serial.EIGHTBITS    # number of bits per bytes # SEVENBITS
    ser.parity = serial.PARITY_NONE    # set parity check: no parity # PARITY_ODD
    ser.stopbits = serial.STOPBITS_ONE # number of stop bits # STOPBITS_TWO
    #ser.timeout = None                # block read
    ser.timeout = 1                    # non-block read
    #ser.timeout = 2                   # timeout block read
    ser.xonxoff = False                # disable software flow control
    ser.rtscts = False                 # disable hardware (RTS/CTS) flow control
    ser.dsrdtr = False                 # disable hardware (DSR/DTR) flow control
    ser.writeTimeout = 2               # timeout for write

    try:
       ser.open()
    except Exception as e:
       print("Error abriendo puerto serie.\n" + str(e) + '\nFin de programa.')
       exit()

    # Si pudo abrir el puerto -----------------------------------------------------
    if ser.isOpen():

        print(ser.name + ' abierto.\n')

        try:
          ser.flushInput()  # flush input buffer, discarding all its contents
          ser.flushOutput() # flush output buffer, aborting current output
                            # and discard all that is in buffer

          command_list()           # Imprime la lista de comandos

          # Ciclo infinito hasta comando exit (q) ---------------------------------
          while True:
            tests = {
                '1': cmd_1,
                '2': cmd_2,
                '3': cmd_3,
                '4': cmd_4,
                '5': cmd_5,
                '6': cmd_6,
                '7': cmd_7,
                '8': cmd_8,
            }

            command = ""

             # get keyboard input
             # input = raw_input(">> ")  # for Python 2
            command = input(">> ")      # for Python 3

            if command == 'q':
                print("Puerto cerrado. Se cierra el programa.")
                ser.close()
                exit()

            elif command == 'h':
                command_list()

            elif command == 'a':
                for command in tests:
                    tests[command]()

            elif command in tests:
                tests[command]()

            else:
                print("Comando no conocido.")

        except Exception as e1:
            print(e1)
            #print("error de comunicacion." + str(e1))

    else:
       print("No se puede abrir el puerto serie.")
       exit()

#%%
signal.signal(signal.SIGINT, signal_handler)

def main():

   uart_main()


if __name__ == "__main__":
    main()
