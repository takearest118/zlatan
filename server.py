# -*- coding: utf-8 -*-

from datetime import datetime
import random

import socketserver



D_LIST = ('messi', 'ronaldo', 'kangte', 'hwang', 'son')


class Singleton(type):
    __instances = {}
    
    def __call__(self, *args, **kwargs):
        if self not in self.__instances:
            self.__instances[self] = super().__call__(*args, **kwargs)
        return self.__instances[self]


class MapService(metaclass=Singleton):

    def __init__(self, *args, **kwargs):
        print('init MapService')
        self.__map = dict()

    def set_device_id(self, _id, value):
        self.__map.update({_id: value})

    def get_map(self):
        return self.__map


class MyTCPSocketHandler(socketserver.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print("{} {} wrote: {}".format(datetime.utcnow(), self.client_address[0], self.data))
        MapService().set_device_id(D_LIST[random.randrange(len(D_LIST))], '{},{},{}'.format(random.randint(0, 255), random.randint(0, 255), 0))
        print(MapService().get_map())
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())


if __name__ == "__main__":
    
    HOST, PORT = "0.0.0.0", 8888

    MapService()

    # instantiate the server, and bind to localhost on port 8888
    with socketserver.TCPServer((HOST, PORT), MyTCPSocketHandler) as server:
        # activate the server
        # this will keep running until Ctrl-C
        server.serve_forever()

