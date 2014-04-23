#!/usr/bin/env python

"""
PLEASE NOTICE THAT
Passwords and API Keys are removed.
""" 

import sys
sys.path.append('../mechanize-0.2.5')
sys.path.append('../libpynexmo')

import time
import logging
from HTMLParser import HTMLParser
from nexmomessage import NexmoMessage
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

import mechanize
import database

class RegisterMachine(object):
    
    _LOGIN_URL = 'https://eas.admin.uillinois.edu/eas/servlet/EasLogin?redirect=https://webprod.admin.uillinois.edu/ssa/servlet/SelfServiceLogin?appName=edu.uillinois.aits.SelfServiceLogin&dad=BANPROD1'
    _ADD_CLASS_URL = 'https://ui2web1.apps.uillinois.edu/BANPROD1/bwskfreg.P_AltPin'
    _NEXMO_API_KEY = '<nexmo_api_key_here>'
    _NEXMO_API_SECRET = '<nexmo_api_secret_here>'
    _NEXMO_SMS_FROM = '17029568734'
    _GMAIL_FROM = 'illinireg@gmail.com'
    _GMAIL_SMTP = 'smtp.gmail.com:587'
    _GMAIL_PASSWORD = '<gmail_password_here>'
    
    def __init__(self, netid, crn):
        self.netid = netid
        self.crn = crn
        self.db = database.DatabaseCommunicator()
        self.password = self.db.getEnterprisePassword(self.netid)
        self.logger = logging.getLogger('RegisterMachine (netid: %s, crn: %s)' % (netid, crn))
        logging.basicConfig(level=logging.DEBUG)
        self.browser = mechanize.Browser()
        self._initializeBrowser()
    
    def _initializeBrowser(self):
        self.browser.set_handle_equiv(True)
        self.browser.set_handle_gzip(True)
        self.browser.set_handle_redirect(True)
        self.browser.set_handle_referer(True)
        self.browser.set_handle_robots(False)
        self.browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
        self.browser.addheaders = [('User-agent', 'Chrome')]    
        self._login()

    def _initializeCourse(self):
        courseInfo = self.db.getCourseInfo(self.crn)
        self.subject = courseInfo['subject']
        self.number = courseInfo['number']
        self.section = courseInfo['section']
    
    def _login(self):
        self.logger.debug('Attempt login')
        self.browser.open(self._LOGIN_URL)
        self.browser.select_form(nr=0)
        self.browser.form['inputEnterpriseId'] = self.netid
        self.browser.form['password'] = self.password
        self.browser.submit()
        response = self.browser.response()
        self.logger.debug('Login complete')
    
    def _sendSMS(self, message, phone):
        msg = {
            'reqtype': 'json',
            'api_key': self._NEXMO_API_KEY,
            'api_secret': self._NEXMO_API_SECRET,
            'from': self._NEXMO_SMS_FROM,
            'to': phone,
            'text': message
        }
        sms = NexmoMessage(msg)
        sms.set_text_info(msg['text'])
        sms.send_request()
    
    def _sendEmail(self, message, email):
        server = smtplib.SMTP(self._GMAIL_SMTP)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(self._GMAIL_FROM, self._GMAIL_PASSWORD)
        msg = MIMEMultipart()
        msg['From'] = 'IlliniReG Notification'
        msg['To'] = email
        msg['Subject'] = 'Registration Status for %s %s %s' % (self.subject, self.number, self.section)
        msg.attach(MIMEText(message, 'plain'))
        server.sendmail(self._GMAIL_FROM, email, msg.as_string())
        server.quit()
    
    def _notifyOnSuccess(self):
        message = 'Yay! %s %s %s is registered successfully!' % (self.subject, self.number, self.section)
        message += '*From IlliniReG*'
        # _sendSMS(message, )
        # _sendEmail(message, )
    
    def _notifyOnFail(self):
        message = 'Urr! %s %s %s can not be registered at this moment.' % (self.subject, self.number, self.section)
        message += '*From IlliniReG*'
        # _sendSMS(message, )
        # _sendEmail(message, )
    
    def start(self):
        self.browser.open(self._ADD_CLASS_URL)
        self.browser.select_form(nr=1)
        self.browser.submit()
        response = self.browser.response()
        self.browser.select_form(nr=1)
        self.browser.find_control(id='crn_id1').value = self.crn
        self.browser.submit()
        response = self.browser.response()
        content = response.read()
        if 'Registration Add Errors' in content:
            self.logger.debug('Failed to add class')
            self._notifyOnFail()
        else:
            self.logger.debug('Class added successfully')
            self._notifyOnSuccess()
