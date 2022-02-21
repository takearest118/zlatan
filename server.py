# -*- coding: utf-8 -*-

from datetime import datetime
import random

import socketserver
import requests

import threading

import logging

import homography


D_LIST = ('messi', 'ronaldo', 'kangte', 'hwang', 'son')

SLACK_CHANNEL_URL = 'https://hooks.slack.com/services/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'

ENCODING = 'utf-8'

# game plate standard
# x,y flat & z height
ARENA_SIZE_X = 1500
ARENA_SIZE_Y = 2000
ARENA_SIZE_Z = 300

# 'cm' / uwb
SCALE_RATIO = 2000 / 15000

# statics
COORD_X_MIN = 0
COORD_X_MAX = ARENA_SIZE_X
COORD_Y_MIN = 0
COORD_Y_MAX = ARENA_SIZE_Y
COORD_Z_MIN = 0
COORD_Z_MAX = ARENA_SIZE_Z

# position quality factor
PQF_MIN = 0
PQF_MAX = 100


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s\t%(levelname)s:\t%(message)s')
socketserver.TCPServer.allow_reuse_address = True

h_matrix = object

def get_random_device():
    return D_LIST[random.randrange(len(D_LIST))]


class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Singleton(type):
    __instances = {}
    
    def __call__(self, *args, **kwargs):
        if self not in self.__instances:
            self.__instances[self] = super().__call__(*args, **kwargs)
        return self.__instances[self]


class MapService(metaclass=Singleton):

    def __init__(self, *args, **kwargs):
        self.__logger = logging.getLogger('MapService')
        self.__logger.info('init MapService')
        self.__map = dict()
        self.__lock = threading.Lock()

    def set_device_id(self, _id, value):
        with self.__lock:
            self.__map.update({_id: value})

    def get_map(self):
        return self.__map

    def remove_id(self, _id):
        with self.__lock:
            self.__map.pop(_id)


class Session(metaclass=Singleton):

    def __init__(self, *args, **kwargs):
        self.__logger = logging.getLogger('Session  ')
        self.__logger.info('init Session')
        self.__list = list()

    def add(self, session):
        self.__list.append(session)

    def get_session_list(self):
        return self.__list

    def remove(self, session):
        self.__list.remove(session)

    def clear(self):
        self.__list.clear()


class SlackService(metaclass=Singleton):

    def __init__(self, *args, **kwargs):
        self.__logger = logging.getLogger('SlackService')
        self.__logger.info('init SlackService')
        self.__url = SLACK_CHANNEL_URL

    def message(self, msg):
        data = {
            'channel': '#ringo-log',
            'username': 'zlatan',
            'text': msg,
            'icon_emoji': ':racing_car:'
        }
        return requests.post(self.__url, json=data)


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
        if self.request not in Session().get_session_list():
            Session().add(self.request)
            self.__logger.info('connected {}'.format(self.client_address[0]))
        while True:
            # self.request is the TCP socket connected to the client
            self.data = self.request.recv(1024).strip()
            self.__logger.debug("{} {} wrote: {}".format(datetime.utcnow(), self.client_address[0], self.data))
            if str(self.data, ENCODING) == ':/quit':
                Session().remove(self.request)
                self.request.send(bytes('disconnected', ENCODING))
                self.__logger.info('{} was gone'.format(self.client_address[0]))
                break
            elif str(self.data, ENCODING) == ':/map':
                # MapService().set_device_id(get_random_device(), '{},{},{},{}'.format(random.randint(COORD_X_MIN, COORD_X_MAX), random.randint(COORD_Y_MIN, COORD_Y_MAX), random.randint(COORD_Z_MIN, COORD_Z_MAX), random.randint(PQF_MIN, PQF_MAX)))
                self.request.send(bytes(str(MapService().get_map()), ENCODING))
                self.__logger.debug('{} request map'.format(self.client_address[0]))
            elif str(self.data, ENCODING).startswith(':/device'):
                k, v = str(self.data, ENCODING).split('/')[2].split(',', 1)
                split_coord = v.split(',')
                split_coord[0], split_coord[1] = h_matrix([float(split_coord[0]), float(split_coord[1])])
                v = str(int(split_coord[0])) + "," + str(int(split_coord[1])) + "," + split_coord[2] + "," + split_coord[3]
                MapService().set_device_id(k, v)
                self.request.send(bytes(str(MapService().get_map()), ENCODING))
                self.__logger.debug(MapService().get_map())
                self.__logger.debug(Session().get_session_list())
                #SlackService().message(str(MapService().get_map()))
                #SlackService().message(str(Session().get_session_list()))
                # just send back the same data, but upper-cased
                #self.request.sendall(self.data.upper())
            elif str(self.data, ENCODING).startswith(':/object'):
                k, v = str(self.data, ENCODING).split('/')[2].split(',', 1)
                MapService().set_device_id(k, v)
                self.request.send(bytes(str(MapService().get_map()), ENCODING))
                self.__logger.debug(MapService().get_map())
                self.__logger.debug(Session().get_session_list())
            elif str(self.data, ENCODING).startswith(':/remove_object'):
                target = str(self.data, ENCODING).split('/')[2]
                MapService().remove_id(target)
                self.request.send(bytes(str(MapService().get_map()), ENCODING))
            elif str(self.data, ENCODING) == ':/info':
                self.request.send(bytes(
                    "{},{},{},{},{},{},{}".format(
                        COORD_X_MIN,
                        COORD_X_MAX,
                        COORD_Y_MIN,
                        COORD_Y_MAX,
                        COORD_Z_MIN,
                        COORD_Z_MAX,
                        SCALE_RATIO),
                    ENCODING))
            else:
                Session().remove(self.request)
                self.request.send(bytes('error', ENCODING))
                self.__logger.warning('{} wrong command'.format(self.client_address[0]))
                break
                


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == "__main__":
    
    HOST, PORT = "0.0.0.0", 8888

    temporary_mapping_source = [
            Point(-305,-1433),
            Point(12058,-4107),
            Point(15948,13959),
            Point(2854,16254)
    ]

    temporary_mapping_target = [
            Point(0,0),
            Point(1500,0),
            Point(1500,2000),
            Point(0,2000)
    ]

    h_matrix = homography.from_points(temporary_mapping_source, temporary_mapping_target)


    MapService()
    SlackService()

    Session()

    # instantiate the server, and bind to localhost on port 8888
    with ThreadedTCPServer((HOST, PORT), TCPSocketHandler) as server:
        # activate the server
        # this will keep running until Ctrl-C
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
            server.server_close()

