#!/usr/bin/env python

import multiprocessing
import socket

from dispatch import Dispatch
from login import Login

class Server(object):
    
    def __init__(self, hostname, port):
        import logging
        self.logger = logging.getLogger("server")
        self.hostname = hostname
        self.port = port
 
    def _dispatchLauncher(self, conn, address):
        Login(conn, address).auth()
        Dispatch(conn, address).listen()
    
    def start(self):
        self.logger.debug("listening")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(1)
        self.logger.debug("listen() called")


        while True:
            self.logger.debug("in loop")
            conn, address = self.socket.accept()
            self.logger.debug("Got connection")
            process = multiprocessing.Process(target=self._dispatchLauncher, args=(conn, address))
            process.daemon = True
            process.start()
            self.logger.debug("Started process %r", process)
 
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    server = Server("localhost", 9000)
    try:
        logging.info("Listening")
        server.start()
    except:
        logging.exception("Unexpected exception")
    finally:
        logging.info("Shutting down")
        for process in multiprocessing.active_children():
            logging.info("Shutting down process %r", process)
            process.terminate()
            process.join()
    logging.info("All done")
