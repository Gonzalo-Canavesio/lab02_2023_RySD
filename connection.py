# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
import os
from constants import *
from base64 import b64encode
import logging


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
        self.s = socket
        self.connected = True
        self.buffer = ""

    def close(self):
        """
        Cierra la conexión.
        """
        print("Closing connection...")
        self.connected = False
        try:
            self.s.close()
        except socket.error as e:
            # Seguramente ya se desconecto del otro lado
            print(f"Error closing socket: {e}")

    def send(self, message: bytes or str, codif="ascii"):
        """
        Envia un mensaje a través del socket de la conexión.

        Args:
            msj: Mensaje a enviar, puede ser una cadena de texto o bytes.
            codif: Codificación a utilizar para enviar el mensaje. Por defecto es "ascii".

        Raises:
            ValueError: Si se especifica una codificación inválida.
        """
        try:
            # Verifica y aplica la codificación a utilizar
            if codif == "ascii":
                message = message.encode("ascii")
            elif codif == "b64encode":
                message = b64encode(message)
            else:
                raise ValueError(f"send: codificación inválida '{codif}'")
            # Envía el mensaje
            while message:
                bytes_sent = self.s.send(message)
                assert bytes_sent > 0
                message = message[bytes_sent:]
            self.s.send(EOL.encode("ascii"))  # Envía el fin de línea

        except BrokenPipeError:
            logging.warning("No se pudo contactar al cliente")

    def header(self, cod: int):
        """
        Envia el encabezado de respuesta al cliente y
        cierra la conexión en los errores fatales.

        Args:
            cod: Código de respuesta a enviar.
        """
        if fatal_status(cod):
            self.send(f"{cod} {error_messages[cod]}")
            self.close()
        else:
            self.send(f"{cod} {error_messages[cod]}")

    def valid_file(self, filename: str):
        """
        Verifica si el nombre de archivo es valido y si el archivo existe

        Args:
            filename (str): El nombre del archivo a verificar.

        Returns:
            CODE_OK si el archivo existe y es valido.
            INVALID_ARGUMENTS si el nombre del archivo no es valido.
            FILE_NOT_FOUND si el archivo no existe.
        """
        # Obtiene los caracteres del nombre del archivo que no pertenecen a VALID_CHARS
        aux = set(filename) - VALID_CHARS
        if os.path.isfile(os.path.join(self.directory, filename)) and len(aux) == 0:
            return CODE_OK
        elif len(aux) != 0:
            return INVALID_ARGUMENTS
        else:
            return FILE_NOT_FOUND

    def get_file_listing(self):
        """
        Obtiene la lista de archivos disponibles en el directorio y la envía al cliente
        """
        rta = ""
        # Itero sobre la lista de archivos disponibles en el directorio
        for fil in os.listdir(self.directory):
            # Agrego los archvios a la cadena de respuesta
            rta += fil + EOL
        self.header(CODE_OK)
        self.send(rta)

    def get_metadata(self, filename: str):
        """
        Obtiene el tamaño de un archivo y lo envía al cliente

        Args:
            filename (str): El nombre del archivo del que se va a obtener el tamaño.
        """
        # Se verifica si es un archivo valido
        if self.valid_file(filename) != CODE_OK:
            # Se envia el mensaje de error correspondiente por no ser un archivo valido
            self.header(self.valid_file(filename))
        else:
            # Se obtiene el tamaño del archivo y se envia al cliente
            file_size = os.path.getsize(os.path.join(self.directory, filename))
            self.header(CODE_OK)
            self.send(str(file_size))

    def get_slice(self, filename: str, offset: int, size: int):
        """
        Obtiene un slice del archivo especificado y
        lo envía al cliente en formato base64.

        Args:
            filename (str): El nombre del archivo del que se va a obtener el slice.
            offset (int): El byte de inicio del slice.
            size (int): El tamaño del slice.
        """
        # Se verifica si es un archivo valido
        if self.valid_file(filename) != CODE_OK:
            # Se envia el mensaje de error correspondiente por no ser un archivo valido
            self.header(self.valid_file(filename))
        else:
            filepath = os.path.join(self.directory, filename)
            file_size = os.path.getsize(filepath)
            if offset < 0 or offset + size > file_size or size < 0:
                self.header(BAD_OFFSET)
            # Abrir el archivo en modo lectura binario "rb"
            # 'r' se abrira el archivo en modo lectura y 'b' se abrira en modo binario
            else:
                with open(filepath, "rb") as f:
                    # Lee el slice del archivo especificado, inicia en offset y lee size bytes
                    f.seek(offset)
                    slice_data = f.read(size)
                    self.header(CODE_OK)
                    self.send(slice_data, codif="b64encode")

    def quit(self):
        """
        Cierra conexión con el cliente y envia el código de respuesta correspondiente.
        """
        self.header(CODE_OK)
        self.close()

    def command_selector(self, line):
        """
        Selecciona el comando a ejecutar según la línea recibida.
        Si la línea no es un comando válido o existe un problema con sus argumentos,
        se envía el código de error correspondiente.

        Args:
            line (str): La línea recibida.
        """
        try:
            print("Request: " + line)
            cmd, *args = line.split(" ")
            if cmd == "get_file_listing":
                if len(args) == 0:
                    self.get_file_listing()
                else:
                    self.header(INVALID_ARGUMENTS)
            elif cmd == "get_metadata":
                if len(args) == 1:
                    self.get_metadata(args[0])
                else:
                    self.header(INVALID_ARGUMENTS)
            elif cmd == "get_slice":
                try:
                    if len(args) == 3:
                        self.get_slice(args[0], int(args[1]), int(args[2]))
                    else:
                        self.header(INVALID_ARGUMENTS)
                except ValueError:
                    self.header(INVALID_ARGUMENTS)
            elif cmd == "quit":
                if len(args) == 0:
                    self.quit()
                else:
                    self.header(INVALID_ARGUMENTS)
            else:
                self.header(INVALID_COMMAND)
        except ConnectionResetError or BrokenPipeError:
            self.close()
        except Exception as e:
            print(f"Error in connection handling: {e}")
            self.header(INTERNAL_ERROR)

    def _recv(self):
        """
        Recibe datos y acumula en el buffer interno.

        Para uso privado del servidor.
        """
        try:
            data = self.s.recv(4096).decode("ascii")
            self.buffer += data

            if len(data) == 0:
                self.close()
            if len(self.buffer) >= MAX_BUFFER_SIZE:
                self.header(BAD_REQUEST)
        except UnicodeError:
            self.header(BAD_REQUEST)
        except ConnectionResetError or BrokenPipeError:
            self.close()

    def read_line(self):
        """
        Espera datos hasta obtener una línea completa delimitada por el
        terminador del protocolo.

        Devuelve la línea sin el terminador ni espacios en blanco al inicio o final.
        """
        while not EOL in self.buffer and self.connected:
            self._recv()
        if EOL in self.buffer:
            response, self.buffer = self.buffer.split(EOL, 1)
            return response.strip()

    def handle(self):
        """
        Atiende eventos de la conexión hasta que termina.
        """
        line = ""
        while self.connected:
            if NEWLINE in line:
                self.header(BAD_EOL)
            elif len(line) > 0:
                self.command_selector(line)
            line = self.read_line()
