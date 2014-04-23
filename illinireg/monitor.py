#!/usr/bin/env python

"""
PLEASE NOTICE THAT
Passwords and API Keys are removed.
""" 

import sys
sys.path.append('../mechanize-0.2.5')
sys.path.append('../libpynexmo')

import time
import smtplib
import logging
import multiprocessing
from HTMLParser import HTMLParser
from nexmomessage import NexmoMessage
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

import mechanize
import database
import register

class Monitor(object):
    
    _REFRESH_RATE = 3
    _TERM_CODE = '120148'
    _YEAR = '2014'
    _SEMESTER = 'fall'
    _LOGIN_URL = 'https://eas.admin.uillinois.edu/eas/servlet/EasLogin?redirect=https://webprod.admin.uillinois.edu/ssa/servlet/SelfServiceLogin?appName=edu.uillinois.aits.SelfServiceLogin&dad=BANPROD1'
    _LOOKUP_URL = 'https://ui2web1.apps.uillinois.edu/BANPROD1/bwckschd.p_disp_detail_sched?term_in=%s&crn_in=' % _TERM_CODE
    _STATUS_LOOKUP_URL = 'http://courses.illinois.edu/cisapp/explorer/schedule'
    _NEXMO_API_KEY = '<nexmo_api_key_here>'
    _NEXMO_API_SECRET = '<nexmo_api_secret_here>'
    _NEXMO_SMS_FROM = '17029568734'
    _GMAIL_FROM = 'illinireg@gmail.com'
    _GMAIL_SMTP = 'smtp.gmail.com:587'
    _GMAIL_PASSWORD = '<gmail_password_here>'
    
    _MONITOR_NETID = '<netid_here>'
    _MONITOR_PASSWORD = '<password_here>'
    
    def __init__(self, crn):
        self.logger = logging.getLogger('Monitor (crn: %s)' % crn)
        logging.basicConfig(level = logging.DEBUG)
        self.logger.info('Monitor started')
        self.browser = mechanize.Browser()
        self._initializeBrowser()
        self.crn = crn
        self._initializeCourse()
        self.db = database.DatabaseCommunicator()
    
    def _login(self):
        self.logger.debug('Attempt login')
        self.browser.open(self._LOGIN_URL)
        self.browser.select_form(nr=0)
        self.browser.form['inputEnterpriseId'] = self._MONITOR_NETID
        self.browser.form['password'] = self._MONITOR_PASSWORD
        self.browser.submit()
        response = self.browser.response()
        self.logger.debug('Login complete')
    
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
        response = self.browser.open(self._LOOKUP_URL + self.crn)
        source = response.read()
        parser = self._CourseInfoParser(self)
        parser.feed(source)
        self.logger.debug('Current Course: <%s, %s, %s>' % (self.subject, self.number, self.section))
    
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
        msg['Subject'] = 'Available Seat Found!'
        msg.attach(MIMEText(message, 'plain'))
        server.sendmail(self._GMAIL_FROM, email, msg.as_string())
        server.quit()
    
    def _register(self, netid, crn):
        RegisterMachine(netid, crn).start()

    def _notify(self):
        userList = self.db.getUserListByCRN(self.crn)
        for user in userList:
            netid = user['netid']
            phone = user['phone']
            email = user['email']
            name = user['name']
            mode = user['mode']
            last_notification = user['last_notification']
            notification_interval = user['notification_interval']
            
            if time.time() - last_notification < notification_interval:
                self.logger.debug('Cancel current notification for user <%s>' % netid)
                continue
            else:
                self.db.updateMonitorEntry(netid, self.crn, mode, time.time())
            
            message = 'Hi, ' + name + '! '
            message += 'A seat in <%s, %s, %s> has been found for you.\n' % (self.subject, self.number, self.section)
            if mode == '0':
                message += 'Please register ASAP with CRN: ' + self.crn + '.\n'
            if mode == '1':
                message += 'Register is already in progress. Please pay attention to the next message.\n'
            message += '*From IlliniReG*'
            
            self._sendSMS(message, phone)
            self._sendEmail(message, email)
            if mode == '1':
                self.logger.debug('launching register process for user <%s>' % netid)
                process = multiprocessing.Process(target=self._register, args=(netid, self.crn))
        pass
    
    def _shouldTerminate(self):
        userList = self.db.getUserListByCRN(self.crn)
        return (not userList)
    
    def start(self):
        while True:
            if _shouldTerminate():
                self.logger.debug('No users left. Exit.')
                sys.exit()
            
            response = self.browser.open(self._LOOKUP_URL + self.crn)
            htmlSource = response.read()
            availabilityParser = self._CourseAvailabilityParser(self)
            availabilityParser.feed(htmlSource)
            if self.remaining > 0:
                print 'seat available'
                self._notify()
            else:
                #print 'No seat at ' + time.strftime('%m/%d %X')
                time.sleep(self._REFRESH_RATE)
                continue
        pass
    
    
    class _CourseInfoParser(HTMLParser):
        _found = False
        _shouldStop = False
        
        def __init__(self, monitor):
            HTMLParser.__init__(self)
            self.monitor = monitor
        
        def handle_starttag(self, tag, attrs):
            if self._found == False and self._shouldStop == False and tag == 'th' and attrs == [('class', 'ddlabel'), ('scope', 'row')]:
                self._found = True
    
        def handle_data(self, data):
            if self._found == True and self._shouldStop == False:
                crnIndex = data.find(self.monitor.crn)
                subjectIndex = crnIndex + 8
                numberInddex = data.find(' ', subjectIndex) + 1
                sectionIndex = data.find('-', numberInddex) + 2
                self.monitor.subject = data[subjectIndex:(numberInddex - 1)]
                self.monitor.number = data[numberInddex:(sectionIndex - 3)]
                self.monitor.section = data[sectionIndex:]
                self._shouldStop = True
    
    class _CourseAvailabilityParser(HTMLParser):
        _tagCount = 0
        _capacityLoaded = False
        _actualLoaded = False
        _remainingLoaded = False
        
        def __init__(self, monitor):
            HTMLParser.__init__(self)
            self.monitor = monitor
        
        def handle_starttag(self, tag, attrs):
            if tag == 'td' and attrs == [('class', 'dddefault')]:
                self._tagCount += 1
        
        def handle_data(self, data):
            if self._tagCount == 8 and (not self._capacityLoaded):
                # cross list capacity
                self.monitor.capacity = int(float(data.strip()))
                self._capacityLoaded = True
            if self._tagCount == 9 and (not self._actualLoaded):
                # cross list actual
                self.monitor.actual = int(float(data.strip(' \t\n\r')))
                self._actualLoaded = True
            if self._tagCount == 10 and (not self._remainingLoaded):
                # cross list remaining
                self.monitor.remaining = int(float(data.strip(' \t\n\r')))
                self._remainingLoaded = True
                self._tagCount = 0
    
    class _CourseStatusParser(HTMLParser):
        _found = False
        
        def __init__(self, monitor):
            HTMLParser.__init__(self)
            self.moniotr = monitor
        
        def handle_starttag(self, tag, attrs):
            if tag == 'enrollmentstatus':
                self._found = True
        
        def handle_data(self, data):
            if self._found:
                self.moniotr.status = data
                print data
            self._found = False
