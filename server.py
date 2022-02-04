# -*- coding: utf-8 -*-

from datetime import datetime
import random

import socketserver
import requests


D_LIST = ('messi', 'ronaldo', 'kangte', 'hwang', 'son')

SLACK_CHANNEL_URL = 'https://hooks.slack.com/services/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'

ENCODING = 'utf-8'


def get_random_device():
    return D_LIST[random.randrange(len(D_LIST))]


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


class Session(metaclass=Singleton):

    def __init__(self, *args, **kwargs):
        print('init Session')
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
        print('init SlackService')
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

    def handle(self):
        if self.request not in Session().get_session_list():
            Session().add(self.request)
            print('connected {}'.format(self.client_address[0]))
        while True:
            # self.request is the TCP socket connected to the client
            self.data = self.request.recv(1024).strip()
            print("{} {} wrote: {}".format(datetime.utcnow(), self.client_address[0], self.data))
            if str(self.data, ENCODING) == ':/quit':
                Session().remove(self.request)
                self.request.send(bytes('disconnected', ENCODING))
                print('{} was gone'.format(self.client_address[0]))
                break
            elif str(self.data, ENCODING) == ':/map':
                MapService().set_device_id(get_random_device(), '{},{},{},{}'.format(random.randint(0, 5000), random.randint(0, 5000), 0, random.randint(0, 100)))
                self.request.send(bytes(str(MapService().get_map()), ENCODING))
                print('{} request map'.format(self.client_address[0]))
            elif str(self.data, ENCODING).startswith(':/device'):
                k, v = str(self.data, ENCODING).split('/')[2].split(',', 1)
                MapService().set_device_id(k, v)
                MapService().set_device_id(get_random_device(), '{},{},{},{}'.format(random.randint(0, 5000), random.randint(0, 5000), 0, random.randint(0, 100)))
                print(MapService().get_map())
                print(Session().get_session_list())
                #SlackService().message(str(MapService().get_map()))
                #SlackService().message(str(Session().get_session_list()))
                # just send back the same data, but upper-cased
                self.request.sendall(self.data.upper())
            else:
                Session().remove(self.request)
                self.request.send(bytes('error', ENCODING))
                print('{} wrong command'.format(self.client_address[0]))
                break
                


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == "__main__":
    
    HOST, PORT = "0.0.0.0", 8888

    MapService()
    SlackService()

    Session()

    # instantiate the server, and bind to localhost on port 8888
    with ThreadedTCPServer((HOST, PORT), TCPSocketHandler) as server:
        # activate the server
        # this will keep running until Ctrl-C
        server.serve_forever()
        server.shutdown()
        server.server_close()

