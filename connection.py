# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
import os
from constants import *
from base64 import b64encode

class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    def __init__(self, socket: socket.socket , directory):
        self.directory = directory
        self.socket = socket
        self.active = True
        self.bof = ''
    
    def contact(self, msj: bytes or str, codif='ascii'):
        #se va enviar el mensaje y se fija en codifi ya que es la codificacion que va a usar
        if codif == 'ascii':
            msj = msj.encode("ascii")
        elif codif == 'b64encode':
            msj = b64encode(msj)
        else:
            raise ValueError(f"send: Invalid instance '{codif}'") # excepción de tipo ValueError cuando hay un valor invalido en codif
        
        while len(msj) > 0: #se encarga de enviar el mensaje a través del socket en trozos hasta que se haya enviado todo el mensaje
            sent = self.socket.send(msj) 
            msj = msj[sent]
        #sent tiene la cantidad almacena la cantidad de bytes que se han enviado y se asegura que se haya enviado al menos un byte antes de seguir
    
    def quit(self):
        rta = mtext(CODE_OK) + EOL
        self.contact(rta)
        self.active = False #desactivo la conexion 
        f"Closing connection..."
    
    def valid_file(self, filename: str):
        aux = set(filename) - VALID_CHARS #obtener los caracteres en filename que no pertenecen al conjunto VALID_CHARS
        return (len(aux) == 0) #si obtengo != 0 significa que tengo argumentos invalidos y si tengo 0 esta todo bien
    
    
    def get_file_listing(self):
        rta = mtext(CODE_OK) + EOL #Cadena de texto que indica que la operacion fue exitosa
        
        for fil in os.listdir(self.directory): #obtengo la lista de archivos disponibles en el directorio 
            rta += fil + EOL # voy agregando los archvios a la cadena de respuesta con \r\n al final 
        rta += EOL # fin de la cadena
        self.contact(rta)
    
    def get_metadata(self, filename: str):
        rta = mtext(CODE_OK) + EOL
        
        if not(os.path.isfile(os.path.join(self.directory, filename))): #nos fijamos si no es un arhivo la os.path.join forma una ruta completa con self.directory y el archivo filename y dsp ve si es un archivo que existe
            rta += mtext(FILE_NOT_FOUND) + EOL
            self.contact(rta)
        elif not self.valid_file(filename):
            rta += mtext(INVALID_ARGUMENTS) + EOL
            self.contact(rta)
        else:
            size = os.path.getsize(os.path.join(self.directory, filename)) # devuelve el tamaño en bytes de un archivo en el camino especificado
            rta = f"{str(size)} {EOL}"
            self.contact(rta)               

    def get_slice(self, filename: str, offset: int, size: int):
        filepath = os.path.join(self.directory, filename)
        if not os.path.isfile(filepath): # existe archivo?
            rta = mtext(FILE_NOT_FOUND) + EOL
            self.contact(rta)
        elif not self.valid_file(filename): # argumentos validos?
            rta = mtext(INVALID_ARGUMENTS) + EOL
            self.contact(rta)
        else:
            file_size = os.path.getsize(filepath)
            if offset < 0 or offset >= file_size or size < 0 or offset + size > file_size:
                rta = mtext(BAD_OFFSET) + EOL  # error con el offset
                self.contact(rta)
            rta = mtext(CODE_OK) + EOL
            self.contact(rta)
            with open(filepath, "rb") as f: #Abrir el archivo en modo lectura binario "rb", 'r' se abrira el archivo en modo lectura y 'b' se abrira en modo binario
                f.seek(offset) #lee el slice del archivo especificado, empezando desde el offset
                slice_data = f.read(size) #y leyendo el tamaño especificado
                self.contact(slice_data, codif='b64encode') #Codifica el slice en base64
            rta = EOL
            self.contact(rta)
    
    def _recv(self):
        try:
            while True:
                data = self.socket.recv(4096).decode('ascii')
                self.bof += data
                
                if len(data) == 0:
                    self.active = False
                    break
        except UnicodeError:
            rta = mtext(BAD_REQUEST) + EOL
            self.send(rta)
            self.active = False
            f"Closing connection..."    
    
    def handle(self):
        """
        Atiende eventos de la conexión hasta que termina.
        """

def mtext(cod: int):
    return f"{cod} {error_messages[cod]}"