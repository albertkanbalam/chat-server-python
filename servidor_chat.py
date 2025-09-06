#!/usr/bin/env python

import socket, time, string, datetime
import traceback
import threading


# Esta clase nos permite crear objetos tipo 'cliente' con el socket
# de cada cliente que se conecta a nuestro socket.
# Contiene su direccion_ip, su nickname con el que se registra,
# una referencia a la lista donde estan todos los clientes conectados,
# y un identificador que a su vez es el inice que ocupa en la lista.
class Socket_cliente(threading.Thread):

    def __init__(self, sk, addr, ID, usuarios):
        threading.Thread.__init__(self)

        # Identificador y una referencia a la lista de usuarios
        self.ID = ID
        self.usuarios = usuarios

        # El nickname solo se asigna cuando el cliente se registra
        self.nick = ""

        # Socket cliente e ip
        self.s_c = sk
        self.addr = addr
        self.activo = 1

    # Este metodo es llamado cuando queremos reenviarle algun
    # mensaje a este cliente
    def envia_mensaje(self, mensaje):
        self.s_c.send(mensaje)

    # Con este metodo buscamos, en la lista de clientes, el nick
    # al cual se debe enviar el mensaje y en caso de existir,
    # se envia. En caso contrario, se envia la confirmacion fail
    def busca_y_envia(self, nick, msj):

        # Construimos el mensaje
        mensaje = "from: " + self.nick + '\nto: ' + nick  + "\ntime: " + str(time.localtime()[:6]) + '\nmessage: ' + msj + '\n'

        # Si es para todos, reenviamos a cada cliente de la lista.
        if nick == "all":
            for user in self.usuarios:
                user.envia_mensaje(mensaje)

        # Si no es para todos, buscamos al cliente.
        else:
            esta = 0
            for user in self.usuarios:
                if user.nick == nick:
                    user.envia_mensaje(mensaje)

                    # Y confirmamos que se ha enviado
                    self.s_c.send("message-delivered 201 success")
                    esta = 1
                    break

            if not esta:
                # Confirmamos que no se ha enviado
                self.s_c.send("message-delivered 202 fail")

    # Esta funcion exclusivamente verifica si el nick esta en nuestra lista
    def verificaExistencia(self, nick):
        for user in self.usuarios:
            if user.nick == nick:
                return 1
        return 0

    # Con esta checamos que el nick del cliente no tenga inadecuados
    def verificaNick(self, nick):

        # Si es menor de 3 caracteres o mayor de 50 entonces, esta mal
        # Si no empieza con letras, esta mal
        if (not (3 <= len(nick) <= 25)) or (nick[0] not in string.ascii_letters):
            return 0

        # Si algun caracter no es alphanumerico, esta mal
        for letra in nick:
            if (letra not in string.ascii_letters) and (letra not in string.digits):
                return 0

        # No puede llamarse all
        if nick == "all":
            return 0

        # Si no, entonces esta bien
        return 1

    # Esta es la funcion que correra el thread
    def run(self):

        # Comenzamos recibiendo la info del cliente
        rcv = self.s_c.recv(100)
        rcv = rcv.decode("utf-8")
        print("RECIBIDO::::", rcv[:8])

        # Y nos mantenemos recibiendo peticiones mientras
        # no sean 'exit' o vacias
        while rcv[4:] != "exit" and rcv != "":

            # Cuando recibimos peticion de registro
            # asignamos el nick a la variable nick del objeto
            if str(rcv[:8]) == "register":
                print("YEEEEES")

                # Obtenemos el nick de la peticion
                nick = rcv[9:].split(" ")[0][:-1][:-1]
                print ("nick:"+nick)

                # Si no existe y es valido continuamos, si no avisamos.
                if self.verificaNick(nick) and not self.verificaExistencia(nick):
                    self.nick = nick
                    self.s_c.send(b"registration 101 success")
                else:
                    self.s_c.send(b"registration 102 fail")

            # Cuando se pide mostrar la lista de usuarios
            # mostramos cada nick de la lista.
            if rcv[:3] == "lst":

                # Construimos la cadena que devolveremos
                users = "clients" + str(len(self.usuarios)) + '\n'
                for user in self.usuarios:
                    users += user.nick + '\n'

                # Y lo enviamos
                self.s_c.send(bytes(users, 'ascii'))

            # Cuando recibimos un mensaje para reenviar
            if rcv[:1] == "@":

                # Obtenemos el nick del cliente al que reenviaremos
                nick = rcv[1:].split(" ")[0]

                # Y el resto es el mensaje
                msj = rcv[len(nick)+2:]

                # Si el mensaje contiene a lo mas 100 char
                # entonces lo enviamos
                if len(msj) <= 100:
                    self.busca_y_envia(nick, msj)
                else:
                    self.s_c.send(b"message-delivered 202 fail")

            # Cuando recibimos la peticion de salida
            # cerramos el socket del cliente y lo eliminamos de la lista
            if rcv[:4] == "exit" or rcv == "":

                # Le quitamos el nick
                self.nick = ""

                self.s_c.send(b"Terminamos la sesion")
                print ("Se termina la sesion")

                self.s_c.close()
                self.activo = 0
                # Lo borramos de la lista
                del(self.usuarios[self.ID])

                # Y reacomodamos los ID de la lista
                i = 0
                for user in self.usuarios:
                    user.ID = i
                    i += 1
                break

            # Si no se recibe una peticion conocida
            # continuamos recibiendo.
            else:
                print ("Recibiendo %s de %s"%(rcv, str(self.addr)))
                print ("Usuarios", self.usuarios)
                rcv = self.s_c.recv(100)
                rcv = self.s_c.recv(100).decode("utf-8")


#======================================
#
#    Este es el programa:
#
#======================================

# Creamos un sicket que recibe po cualquier ip disponible
# y escucha por el puerto 5011
s = socket.socket()
s.bind(("", 5018))

# Aceptamos hasta 10 clientes
s.listen(10)

# Inicializamos la lista de usuarios
usuarios = []

# Y comenzamos a recibir conexiones
while 1:

    # Cuando un cliente se conecta
    # Le damos un ID y creamos un objeto con su direccion
    # y con su socket
    sc, addr = s.accept()
    ID = len(usuarios)
    usuario = Socket_cliente(sc, addr, ID, usuarios)

    # Iniciamos el thread del cliente para mantenernos
    # escuchando sus peticiones
    usuario.start()

    # Y lo agregamos a la lista
    usuarios.append(usuario)

# Cerramos nuestro socket
s.close()
