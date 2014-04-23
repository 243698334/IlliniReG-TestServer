#!/usr/bin/env python

"""
Example JSON data for login process.

-- request from client --
{
    "request_type" : "login",
    "netid" : "xxxxxxxx",
    "password" : "xxxxxxxx"
}

-- response from server --
{
    "request_type" : "login",
    "request_status" : "Accepted" # or "Denied"
}

"""
import socket
import logging
import json

import database

class Login(object):
    
    def __init__(self, conn, address):
        self.conn = conn
        self.address = address
        self.db = database.DatabaseCommunicator()
        self.logger = logging.getLogger('login')
        logging.basicConfig(level=logging.DEBUG)
        
        self.logger.debug("Connected %r at %r" % (conn, address))

    def auth(self):
        try:
            loginRequest = self.conn.recv(1024)
            if loginRequest == '':
                self.logger.debug('Socket closed from client')
                conn.close()
                return False
            self.logger.info('Login request received.')
                
            loginRequestJSON = json.loads(loginRequest)
            requestType = loginRequestJSON['request_type']
            if requestType != 'login':
                return False
            netid = loginRequestJSON['netid']
            password = loginRequestJSON['password']
            self.logger.info('Login request parsed. (netid: %s)' % netid)
            
            if self.db.login(netid, password) == True:
                self.logger.debug('Auth success')
                loginResponse = dict(request_type='login', request_status='Accepted')
                print json.dumps(loginResponse)
                self.conn.sendall(json.dumps(loginResponse) + '\n')
                return True
            else:
                self.logger.debug('Auth failed')
                loginResponse = dict(request_type='login', request_status='Denied')
                self.conn.sendall(json.dumps(loginResponse) + '\n')
                return False
        except:
            self.logger.debug('Unknown error')
            self.logger.debug('Closing current socket')
            self.conn.close()
