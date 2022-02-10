# -*- coding: utf-8 -*-

import random
import socket
import threading
import time
import math
import logging
import sys
import signal


DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8888

NPC_LIST = ('messi', 'ronaldo', 'kangte', 'hwang', 'son')
#NPC_LIST = ('messi',)

ENCODING = 'utf-8'


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s\t%(levelname)s:\t%(message)s')


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

        self.__LOOP_INTERVAL_SEC = 0.1
        self.__MOVE_INTERVAL_SEC = 2
        self.__SLEEP_SEC = 2

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
        self.__speed = random.randint(100, 300)

        self.__rotation_z = random.randint(0, 360)


    def send_message(self, message):
        self.__sock.sendall(bytes(message, ENCODING))
        received = str(self.__sock.recv(1024), ENCODING)
        self.__LOGGER.debug("Received: " + received)
        return received


    def send_position(self):
        message = ":/device/{},{},{},{},{}".format(
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

            time.sleep(self.__LOOP_INTERVAL_SEC)


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




if __name__ == "__main__":
    def shutdown_handler(sig, frame):
        NpcService().stop()

    NpcService()
    NpcService().start()

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    signal.pause()

