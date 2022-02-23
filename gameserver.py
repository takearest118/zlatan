# -*- coding: utf-8 -*-

import random
import socket
import threading
import time
import math
import logging
import sys
import signal

import socketserver


DEFAULT_HOST = '192.168.41.254'
DEFAULT_PORT = 8888

NPC_LIST = ('messi', 'ronaldo', 'kangte', 'hwang', 'son')
#NPC_LIST = ('messi',)

ENCODING = 'utf-8'


LOOP_INTERVAL_SEC = 0.01


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s\t%(levelname)s:\t%(message)s')
socketserver.TCPServer.allow_reuse_address = True


host = DEFAULT_HOST
port = DEFAULT_PORT
if len(sys.argv) > 1:
    host = sys.argv[1]
if len(sys.argv) > 2:
    port = int(sys.argv[2])


class Singleton(type):
    __instances = {}
    
    def __call__(self, *args, **kwargs):
        if self not in self.__instances:
            self.__instances[self] = super().__call__(*args, **kwargs)
        return self.__instances[self]


class Npc:
    def __init__(self, name):

        self.__name = 'npc_' + name
        self.__LOGGER = logging.getLogger("NPC-" + name)
        self.__LOGGER.setLevel(logging.INFO)

        self.__MOVE_INTERVAL_SEC = 2
        self.__SLEEP_SEC = 2

        # cm
        self.__SPEED_MAX = 300
        self.__SPEED_MIN = 100

        self.__live = True

        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.connect((host, port))

        # prepare arena info
        arena_info_message = self.send_message(":/info")
        self.__LOGGER.debug(arena_info_message)

        split_info_message = arena_info_message.split(',')
        self.__arena_x_min = int(split_info_message[0])
        self.__arena_x_max = int(split_info_message[1])
        self.__arena_y_min = int(split_info_message[2])
        self.__arena_y_max = int(split_info_message[3])
        self.__arena_z_min = int(split_info_message[4])
        self.__arena_z_max = int(split_info_message[5])
        self.__arena_scale = float(split_info_message[6])

        # set initial value
        self.__position_x = random.randint(self.__arena_x_min, self.__arena_x_max)
        self.__position_y = random.randint(self.__arena_y_min, self.__arena_y_max)
        self.__position_z = 0
        self.__speed = random.randint(
                self.__SPEED_MIN * LOOP_INTERVAL_SEC * 10, 
                self.__SPEED_MAX * LOOP_INTERVAL_SEC * 10)

        self.__rotation_z = random.randint(0, 360)

    def send_message(self, message):
        self.__sock.sendall(bytes(message, ENCODING))
        received = str(self.__sock.recv(1024), ENCODING)
        self.__LOGGER.debug("Received: " + received)
        return received


    def send_position(self):
        message = ":/object/{},{},{},{},{}".format(
                self.__name,
                self.__position_x,
                self.__position_y,
                self.__position_z,
                "0")
        self.send_message(message)


    def run(self):
        self.__LOGGER.info("Started " + self.__name)

        while self.__live:
            self.__rotation_z = random.randint(0, 360)

            self.__LOGGER.debug("{}: Location Start: {}, {}".format(self.__name, self.__position_x, self.__position_y))
            self.moving()
            self.__LOGGER.debug("{}: Location End  : {}, {}".format(self.__name, self.__position_x, self.__position_y))

            time.sleep(self.__SLEEP_SEC)
            

    def moving(self):
        radian = math.radians(self.__rotation_z)
        move_start_timestamp = time.time()

        while self.__live:
            delta_x = int(self.__speed * math.cos(radian))
            delta_y = int(self.__speed * math.sin(radian))
            self.__position_x = self.__position_x + delta_x
            self.__position_y = self.__position_y + delta_y

            if self.__position_x < self.__arena_x_min:
                self.__position_x = self.__arena_x_min
                self.__rotation_z = (540 - self.__rotation_z) % 360
                radian = math.radians(self.__rotation_z)
            if self.__position_x > self.__arena_x_max:
                self.__position_x = self.__arena_x_max
                self.__rotation_z = (540 - self.__rotation_z) % 360
                radian = math.radians(self.__rotation_z)
            if self.__position_y < self.__arena_y_min:
                self.__position_y = self.__arena_y_min
                self.__rotation_z = (360 - self.__rotation_z) % 360
                radian = math.radians(self.__rotation_z)
            if self.__position_y > self.__arena_y_max:
                self.__position_y = self.__arena_y_max
                self.__rotation_z = (360 - self.__rotation_z) % 360
                radian = math.radians(self.__rotation_z)

            self.send_position()

            if time.time() > (move_start_timestamp + self.__MOVE_INTERVAL_SEC):
                break;

            time.sleep(LOOP_INTERVAL_SEC)


    def close(self):
        self.__LOGGER.info("Stop " + self.__name)
        self.__live = False
        time.sleep(1)
        self.send_message(":/quit")
        self.__sock.close()


class NpcService(metaclass=Singleton):
    def __init__(self, *args, **kwargs):
        self.__LOGGER = logging.getLogger('NpcService')
        self.__LOGGER.info('init NpcService')
        self.__npc_list = list()


    def npc_controller(self, name, npc):
        time.sleep(random.randint(0, 2000) / 1000)
        npc.run()


    def start(self):
        for npc_name in NPC_LIST:
            npc = Npc(npc_name)
            self.__npc_list.append(npc)
            thread = threading.Thread(target=self.npc_controller, args=(npc_name, npc))
            thread.start()


    def stop(self):
        self.__LOGGER.info("Shutdown NpcService")
        for npc in self.__npc_list:
            threading.Thread(target=npc.close).start()


class ItemService(metaclass=Singleton):
    def __init__(self, *args, **kwargs):
        self.__LOGGER = logging.getLogger('ItemService')
        self.__LOGGER.info('init ItemService')

        self.__ITEM_MAX = 6
        self.__item_sequence = 0

        self.__item_list = list()

        received = ""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            sock.sendall(bytes(":/info", ENCODING))
            received = str(sock.recv(1024), ENCODING)
            sock.sendall(bytes(":/quit", ENCODING))
            str(sock.recv(1024), ENCODING)

        split_info_message = received.split(',')
        self.__arena_x_min = int(split_info_message[0])
        self.__arena_x_max = int(split_info_message[1])
        self.__arena_y_min = int(split_info_message[2])
        self.__arena_y_max = int(split_info_message[3])
        self.__arena_z_min = int(split_info_message[4])
        self.__arena_z_max = int(split_info_message[5])
        self.__arena_scale = float(split_info_message[6])

        for i in range(0, self.__ITEM_MAX):
            self.add_item()


    def add_item(self):
        item_name = "item_" + str(self.__item_sequence)

        position_x = random.randint(self.__arena_x_min, self.__arena_x_max)
        position_y = random.randint(self.__arena_y_min, self.__arena_y_max)

        message = ":/object/{},{},{},0,0".format(item_name, position_x, position_y)


        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            sock.sendall(bytes(message, ENCODING))
            received = str(sock.recv(1024), ENCODING)
            sock.sendall(bytes(":/quit", ENCODING))
            received = str(sock.recv(1024), ENCODING)

        self.__item_list.append(item_name)
        self.__item_sequence = self.__item_sequence + 1

        self.__LOGGER.info("{} is added".format(item_name))


    def remove_item(self, item_name):

        message = ":/remove_object/{}".format(item_name)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            sock.sendall(bytes(message, ENCODING))
            received = str(sock.recv(1024), ENCODING)
            sock.sendall(bytes(":/quit", ENCODING))
            received = str(sock.recv(1024), ENCODING)

        self.__item_list.remove(item_name)
        self.__LOGGER.info("{} is removed".format(item_name))


    def stop(self):
        while len(self.__item_list) > 0:
            item = self.__item_list[0]
            self.remove_item(item)


class TCPSocketHandler(socketserver.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def __init__(self, *args, **kwargs):
        self.__logger = logging.getLogger('TCPHandler')
        self.__logger.setLevel(logging.INFO)
        socketserver.BaseRequestHandler.__init__(self, *args, **kwargs)


    def handle(self):
        while True:
            self.data = self.request.recv(1024).strip()

            data_string = str(self.data, ENCODING)
            
            if str(self.data, ENCODING) == ':/quit':
                self.request.send(bytes('disconnected', ENCODING))
                self.__logger.info('{} was gone'.format(self.client_address[0]))
                break
            elif data_string.startswith(':/take'):
                try:
                    k, v = data_string.split('/')[2].split(',', 1)
                    self.__logger.info("'{}' tries to take '{}'".format(k, v))
                    ItemService().remove_item(v)
                    self.request.send(bytes('OK', ENCODING))

                    ItemService().add_item()
                except:
                    self.__logger.info("'{}' fails to take '{}'".format(k, v))
                    self.request.send(bytes('ERROR', ENCODING))
            else:
                self.request.send(bytes('error', ENCODING))
                self.__logger.warning('{} wrong command'.format(self.client_address[0]))
                break


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass



if __name__ == "__main__":

    HOST, PORT = "0.0.0.0", 8889

    # instantiate the server, and bind to localhost on port 8888
    with ThreadedTCPServer((HOST, PORT), TCPSocketHandler) as server:
        # activate the server
        # this will keep running until Ctrl-C

        def shutdown_handler(sig, frame):
            NpcService().stop()
            ItemService().stop()
            server.shutdown()
            server.server_close()


        NpcService()
        NpcService().start()
        ItemService()

        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)

        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        signal.pause()

