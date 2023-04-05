#!/usr/bin/env python
# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Revisión 2014 Carlos Bederián
# Revisión 2011 Nicolás Wolovick
# Copyright 2008-2010 Natalia Bidart y Daniel Moisset
# $Id: server.py 656 2013-03-18 23:49:11Z bc $

import optparse
import socket
import connection
from constants import *
import sys
import os


class Server(object):
    """
    El servidor, que crea y atiende el socket en la dirección y puerto
    especificados donde se reciben nuevas conexiones de clientes.
    """

    def __init__(self, addr=DEFAULT_ADDR, port=DEFAULT_PORT, directory=DEFAULT_DIR):
        """
        Args:
            addr (str): Dirección IP del servidor.
            puerto (int): Puerto en el que el servidor aceptará conexiones entrantes.
            directorio (str): Directorio compartido que se servirá a los clientes.

        Raises:
            OSError: Si no se puede crear el directorio especificado.
        """
        # Revisar que el directorio exista, y si no, crearlo
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError:
                print("No se pudo crear el directorio %s." % directory)
                sys.exit(1)

        print("Serving %s on %s:%s." % (directory, addr, port))

        # Se crea el socket y se lo vincula a la dirección y puerto
        oursocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        oursocket.bind((addr, port))

        # Se guarda el socket y el directorio compartido en el objeto
        self.socket = oursocket
        self.directory = directory

    def serve(self):
        """
        Loop principal del servidor. Se acepta una conexión a la vez
        y se espera a que concluya antes de seguir.
        """
        self.socket.listen()

        while True:
            # Bloquea la ejecución hasta que se recibe una conexión entrante
            (cnSocket, cnAdress) = self.socket.accept()
            # Crea un objeto Connection para manejar la conexión entrante
            cn = connection.Connection(cnSocket, self.directory)
            cn.handle()  # Atiende la conexión entrante


# Esta función main() es el punto de entrada del programa que lanza un servidor que utiliza el protocolo de transferencia de archivos casero HFTP
def main():
    """Parsea los argumentos y lanza el server"""
    # configurar la dirección IP, el número de puerto y el directorio compartido del servidor
    parser = optparse.OptionParser()
    parser.add_option(
        "-p", "--port", help="Número de puerto TCP donde escuchar", default=DEFAULT_PORT
    )
    parser.add_option(
        "-a", "--address", help="Dirección donde escuchar", default=DEFAULT_ADDR
    )
    parser.add_option(
        "-d", "--datadir", help="Directorio compartido", default=DEFAULT_DIR
    )
    # Verifica si hay argumentos adicionales después de las opciones.
    # Si se proporcionan argumentos adicionales, muestra la ayuda del programa y sale del programa.
    options, args = parser.parse_args()
    if len(args) > 0:
        parser.print_help()
        sys.exit(1)
    try:
        # Convierte el valor de puerto proporcionado en un número entero.
        port = int(options.port)
    except ValueError:
        sys.stderr.write("Numero de puerto invalido: %s\n" % repr(options.port))
        parser.print_help()
        sys.exit(1)
    # Crea un objeto servidor utilizando la dirección IP, el número de puerto y el directorio compartido especificados.
    server = Server(options.address, port, options.datadir)
    # Llama al método serve() en el objeto servidor para que comience a escuchar conexiones entrantes.
    server.serve()


if __name__ == "__main__":
    main()
