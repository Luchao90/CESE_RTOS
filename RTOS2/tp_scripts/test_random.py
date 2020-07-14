import serial
import random
import time
import sys
import signal
import crc8
import random
import string

from serial_init import *
from c2 import *
from c3 import *

"""
------------------------------------------------------------------------------
requirements:
this script needs pyserial
refer to https://pyserial.readthedocs.io/en/latest/pyserial.html for installing instructions
this script must use python3
------------------------------------------------------------------------------
script instructions:

execute:
python test_random.py
------------------------------------------------------------------------------
"""

# config -------------------------------------------------------------------
DEFAULT_BAURDATE = 115200
SOM = '('
EOM = ')'
T_INTER_FRAME = 0.06 #SEGUNDOS
DEFAULT_CMD_NRO = 10
DEFAULT_BYTE_MAX_COUNT = 250
DEFAULT_BYTE_MIN_COUNT = 10

#EN 1 SE AGREGA LA OPERACION EN LA RTA ESPERADA EN 0 NO
RESPONSE_HAS_OPERATION = 0

#SIGNAL TRAP
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

#SENDS A LIST OF COMMANDS
def send_frames( ser, frames , delay_between ):
    lista = []
    lista_timepos = []

    for i in range(0,len(frames)):

        lista_timepos.append(time.clock())

        ser.write( str(frames[i]).encode() )

        time.sleep(delay_between)

        try:
            readOut = ser.read(ser.in_waiting).decode('ascii')
            lista.append(readOut)
        except:
            pass

    return lista

#NOT USED
def sendData(command, payload , som , eom , valido = False ):

   payload = command + payload
   payload = c2_add_crc(payload, valido)
   payload = c2_add_delimiters(payload, som , eom)

   print ("Enviando: ",  payload)
   ser.write(str(payload).encode())
   time.sleep(0.100)

   try:
      #print ("Leyendo ...")
      readOut = ser.read(ser.in_waiting).decode('ascii')
      #time.sleep(1)
      print ("Recibido: ", readOut)
      return readOut
   except:
      pass

   return


def randomword(length):
   letters =  string.ascii_letters
   return ''.join(random.choice(letters) for i in range(length))

def generar_cadenas(N,MAX):
    lista = [  ]
    for i in range(0,N):
        sim_chars = random.randint(1,MAX)
        word = randomword(sim_chars)
        #print(word)
        #print(type(randomword(sim_chars)))
        lista.append(word)

    #print(lista)
    return lista

#genera N operaciones del dictionario, devuelve lista
def generar_operaciones(N,dict):
    lista = []
    #print(len(dict))
    for i in range(0,N):
        index = random.randint(0,len(dict)-1)
        lista.append(dict[index])
    return lista


def validar( cmd_raw , rta , op ):
    #print(type(string.ascii_letters + '(' + ')'))
    #limpio non printable
    #print(bytes(rta,'utf-8'))
    #rta = ''.join(c for c in rta if (c in (string.ascii_letters+ '(' + ')') )
    rta = rta.rstrip('\n')
    rta = rta.rstrip('\r')
    rta = rta.lstrip('\n')
    rta = rta.lstrip('\r')
    rta = rta.strip()

    #proceso
    cmd_raw = c3_process( cmd_raw , op )


    if(RESPONSE_HAS_OPERATION==0):
        op= ""

    cmd = create_pkt( op , cmd_raw , SOM , EOM , True )

    if( cmd != rta ):
        print( "                esperado: " + cmd + " recibido:" + rta)
        return 0
    else:
        return 1

def input_number(msg,default):
    tmp_ = input( msg + " ( default: "+ str(default) + " ):" )
    if(tmp_==''):
        nro = default
    else:
        nro = int(tmp_ )
    return nro

#crea un paquete completo
def create_pkt( operacion , payload , som , eom , valido = False ):
    temp = c3_add_op( payload , operacion )
    pkt =  c2_create_frame( temp , som , eom , valido )
    return pkt

#toma una lista de payloads y le formatea el frame y devuelve lista
def create_pkts( operaciones , payloads , som , eom , valido = False ):
    lista = []
    if(len(operaciones)!=len(payloads) ):
        print("Error")
        return

    for i in range(0,len(operaciones)):
        cmd = create_pkt( operaciones[i] ,  payloads[i] , som , eom , valido )
        lista.append(cmd)
    return lista


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
    #ser.timeout = None                 # block read
    ser.timeout = 1                    # non-block read
    #ser.timeout = 2                    # timeout block read
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

            cantidad_comandos = input_number("Ingrese cantidad de comandos",DEFAULT_CMD_NRO)
            cantidad_bytes = input_number("Ingrese cantidad de bytes maxima por paquete",DEFAULT_BYTE_MAX_COUNT)
            #DEFAULT_BYTE_MIN_COUNT = 10 TODAVIA NO UTILIZADO

            operaciones = generar_operaciones( cantidad_comandos , C3_OPERATIONS )

            respuestas = []
            cadenas = generar_cadenas(cantidad_comandos , cantidad_bytes - c2_overhead() - c3_overhead() )

            #genero los frames de todos los comandos
            frames = create_pkts( operaciones , cadenas , SOM , EOM , True )

            #envio paquetes
            respuestas = send_frames( ser, frames , T_INTER_FRAME )

            #validacion
            error_count = 0
            for i in range(0,len(cadenas)):
                print("cmd: " + frames[i])
                print("rta: " + respuestas[i])
                if( validar( cadenas[i] , respuestas[i] , operaciones[i] )==0 ):
                    error_count+=1
            print("")
            if(error_count>0):
                print("errores:" + str(error_count))
                print("")
            print("Puerto cerrado. Se cierra el programa.")
            ser.close()
            exit()

        except Exception as e1:
            print(e1)
            #print("error de comunicacion." + str(e1))

    else:
       print("No se puede abrir el puerto serie.")
       exit()

#%%
signal.signal(signal.SIGINT, signal_handler)

def main():

   # cmd_1()
   uart_main()


if __name__ == "__main__":
    main()
