# -*- coding: utf-8 -*-

import socketserver

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
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())


if __name__ == "__main__":
    
    HOST, PORT = "0.0.0.0", 8888

    # instantiate the server, and bind to localhost on port 8888
    with socketserver.TCPServer((HOST, PORT), MyTCPSocketHandler) as server:
        # activate the server
        # this will keep running until Ctrl-C
        server.serve_forever()
