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

    def __init__(self, socket: socket.socket, directory):
        """
        Inicializa una nueva conexión.

        Args:
            socket: Objeto socket que representa la conexión.
            directory: Directorio raíz de los archivos que se compartirán con el cliente.
        """
        self.directory = directory
        self.socket = socket
        self.active = True
        self.bof = ""

    def contact(self, msj: bytes or str, codif="ascii"):
        """
        Envia un mensaje a través del socket de la conexión.

        Args:
            msj: Mensaje a enviar, puede ser una cadena de texto o bytes.
            codif: Codificación a utilizar para enviar el mensaje. Por defecto es "ascii".

        Raises:
            ValueError: Si se especifica una codificación inválida.
        """
        # se va enviar el mensaje y se fija en codifi ya que es la codificacion que va a usar
        if codif == "ascii":
            msj = msj.encode("ascii")
        elif codif == "b64encode":
            msj = b64encode(msj)
        else:
            # excepción de tipo ValueError cuando hay un valor invalido en codif
            raise ValueError(f"send: Invalid instance '{codif}'")
        # se encarga de enviar el mensaje a través del socket en trozos hasta que se haya enviado todo el mensaje
        try:
            while len(msj) > 0:
                sent = self.socket.send(msj)
                msj = msj[sent:]
        except BrokenPipeError:
            print("La conexión ya está cerrada.")       


    def quit(self):
        rta = mtext(CODE_OK) + EOL
        self.contact(rta)
        # desactivo la conexion
        self.active = False

    def get_file_listing(self):
        """
        Obtiene la lista de archivos disponibles en el directorio y la envía al cliente.
        """

        rta = EOL
        # obtengo la lista de archivos disponibles en el directorio
        for fil in os.listdir(self.directory):
            # voy agregando los archvios a la cadena de respuesta con \r\n al final
            rta += fil + EOL

        self.contact(mtext(CODE_OK) + rta + EOL)

    def get_metadata(self, filename: str):
        """
        Obtiene el tamaño de un archivo y lo envía al cliente.
        """
        # nos fijamos si no es un arhivo la os.path.join forma una ruta completa con self.directory y el archivo filename y dsp ve si es un archivo que existe
        if not (os.path.isfile(os.path.join(self.directory, filename))):
            self.contact(mtext(FILE_NOT_FOUND) + EOL)

        else:
            # devuelve el tamaño en bytes de un archivo en el camino especificado
            size = os.path.getsize(os.path.join(self.directory, filename))
            self.contact(mtext(CODE_OK) + EOL + str(size) + EOL)

    def get_slice(self, filename: str, offset: int, size: int):
        """
        Obtiene un slice del archivo especificado y lo envía al cliente en formato base64.

        Args:
            filename (str): El nombre del archivo del que se va a obtener el slice.
            offset (int): El byte de inicio del slice.
            size (int): El tamaño del slice.
        """
        filepath = os.path.join(self.directory, filename)
        if not os.path.isfile(filepath):  # existe archivo?
            rta = mtext(FILE_NOT_FOUND) + EOL
            self.contact(rta)
        else:
            file_size = os.path.getsize(filepath)
            if offset < 0 or offset + size > file_size:
                rta = mtext(BAD_OFFSET) + EOL  # error con el offset
                self.contact(rta)
            self.contact(mtext(CODE_OK) + EOL)
            # Abrir el archivo en modo lectura binario "rb", 'r' se abrira el archivo en modo lectura y 'b' se abrira en modo binario
            with open(filepath, "rb") as f:
                # lee el slice del archivo especificado, empezando desde el offset
                f.seek(offset)
                # y leyendo el tamaño especificado
                slice_data = f.read(size)
                # Codifica el slice en base64
                self.contact(slice_data, codif="b64encode")
            self.contact(EOL)

    def _recv(self):
        """
        Recibe datos y acumula en el buffer interno.

        Para uso privado del cliente.
        """

        try:
            data = self.socket.recv(4096).decode("ascii")
            self.bof += data

            if len(data) == 0:
                self.active = False
        except ConnectionResetError:
            self.contact(mtext(INTERNAL_ERROR) + EOL)
            self.active = False
            print(f"closing connection")
            

    def read_line(self):
        """
        Espera datos hasta obtener una línea completa delimitada por el
        terminador del protocolo.

        Devuelve la línea, eliminando el terminaodr y los espacios en blanco
        al principio y al final.
        """
        while EOL not in self.bof and self.active:
            self._recv()
        if EOL in self.bof:
            response, self.bof = self.bof.split(EOL, 1)
            return response.strip()
        else:
            return ""

    def command_selector(self, line):
        """
        Selecciona el comando a ejecutar según la línea recibida.

        Args:
            line (str): La línea recibida.
        """
        try:
            cmd, *args = line.split(" ")
            if cmd == "get_file_listing":
                if len(args) == 0:
                    self.get_file_listing()
                else:
                    self.contact(mtext(INVALID_ARGUMENTS) + EOL)
            elif cmd == "get_metadata":
                if len(args) == 1:
                    self.get_metadata(args[0])
                else:
                    self.contact(mtext(INVALID_ARGUMENTS) + EOL)
            elif cmd == "get_slice":
                try:
                    if len(args) == 3:
                        self.get_slice(args[0], int(args[1]), int(args[2]))
                    else:
                        self.contact(mtext(INVALID_ARGUMENTS) + EOL)
                except ValueError:
                    self.contact(mtext(INVALID_ARGUMENTS) + EOL)
            elif cmd == "quit":
                if len(args) == 0:
                    self.quit()
                else:
                    self.contact(mtext(INVALID_ARGUMENTS) + EOL)
            else:
                self.contact(mtext(INVALID_COMMAND) + EOL)
        except Exception as e:
            print(f"Error in connection handling: {e}")
            self.contact(mtext(BAD_REQUEST) + EOL)
            self.active = False

    def handle(self):
        """
        Atiende eventos de la conexión hasta que termina.
        """
        while self.active:
            line = self.read_line()
            if NEWLINE in line:
                self.contact(mtext(BAD_EOL) + EOL)
                self.active = False
            elif len(line) > 0:
                self.command_selector(line)
            else:
                self.active = False
        
        print(f"Closing connection...")
        self.socket.close()


def mtext(cod: int):
    return f"{cod} {error_messages[cod]}"
