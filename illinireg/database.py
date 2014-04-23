#!/usr/bin/python

import logging
import MySQLdb

"""
NOTICE THAT
Database info are removed
"""

class DatabaseCommunicator(object):
    
    _HOST = '<host_here>'
    _USER = '<user_here>'
    _PASSWORD = '<password_here>'
    _DBNAME = '<dbname_here>'
        
    def __init__(self):
        self.db = MySQLdb.connect(self._HOST, self._USER, self._PASSWORD, self._DBNAME)
        self.cursor = self.db.cursor()
        self.logger = logging.getLogger('DatabaseComm')
        logging.basicConfig(level=logging.DEBUG)
    
    def login(self, netid, password):
        query = """ SELECT user_password
                    FROM `ir_users`
                    WHERE user_netid = '%s' """ % netid
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        for row in results:
            return row[0] == password
    
    def getUserListByCRN(self, crn):
        query = """ SELECT user_netid, user_phone, user_email, user_firstname, monitor_mode, monitor_last_notification, monitor_notification_interval
                    FROM `ir_users` JOIN `ir_monitors` ON user_netid = monitor_netid
                    WHERE monitor_crn = '%s' """ % crn        
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        userList = []
        for row in results:
            user = {
                'netid': row[0],
                'phone': row[1],
                'email': row[2],
                'name' : row[3],
                'mode' : row[4],
                'last_notification' : row[5],
                'notification_interval' : row[6],
            }
            userList.append(user)
        return userList
    
    def getCRNListByNetID(self, netid):
        query = """ SELECT monitor_crn
                    FROM `ir_monitors`
                    WHERE monitor_netid = '%s' """ % netid
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        crnList = []
        for row in results:
            crnList.append(row[0])
        return crnList
    
    def getCourseInfo(self, crn):
        query = """ SELECT course_subject, course_number, course_section
                    FROM `ir_courses` 
                    WHERE course_crn = '%s' """ % crn
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        courseInfo = {}
        for row in results:
            courseInfo['subject'] = row[0]
            courseInfo['number'] = row[1]
            courseInfo['section'] = row[2]
        return courseInfo
    
    def newMonitorRequired(self, crn):
        query = """ SELECT COUNT(1)
                    FROM `ir_monitors`
                    WHERE monitor_crn = '%s' """ % crn
        self.cursor.execute(query)
        if int(self.cursor.fetchone()[0]) > 0:
            return False
        else:
            return True
    
    def addMonitorEntry(self, netid, crn, mode, notificationInterval):
        self.logger.info('Adding new monitor (crn: %s, netid: %s, mode: %s)' % (crn, netid, mode))
        checkExistQuery = """ SELECT COUNT(1)
                              FROM `ir_monitors`
                              WHERE monitor_netid = '%s' AND monitor_crn = '%s' """ % (netid, crn)
        self.cursor.execute(checkExistQuery)
        if int(self.cursor.fetchone()[0]) > 0:
            self.logger.debug('Entry already exists')
            return
        addQuery = """ INSERT INTO `ir_monitors` (
                           monitor_netid, monitor_crn, monitor_mode, monitor_notification_interval)
                       VALUES (
                           '%s', '%s', '%s', '%d') """ % (netid, crn, mode, notificationInterval)
        self.cursor.execute(addQuery)
        self.db.commit()
        self.logger.debug('New entry added. <%s, %s, %s>' % (netid, crn, mode))
    
    def updateMonitorEntry(self, netid, crn, mode, notificationInterval, lastNotification):
        query = """ UPDATE `ir_monitors`
                    SET monitor_mode = '%s', monitor_notification_interval = '%s', monitor_last_notification = '%s'
                    WHERE monitor_netid = '%s' AND monitor_crn = '%s' """ % (mode, notificationInterval, lastNotification, netid, crn)
        self.cursor.execute(query)
        self.db.commit()
        self.logger.debug('Entry updated. <%s, %s, %s>' % (netid, crn, mode))
    
    def deleteMonitorEntry(self, netid, crn):
        query = """ DELETE FROM `ir_monitors`
                    WHERE monitor_netid = '%s' AND monitor_crn = '%s' """ % (netid, crn)
        self.cursor.execute(query)
        self.db.commit()
        self.logger.debug('Entry deleted. <%s, %s>' % (netid, crn))

    def getEnterprisePassword(self, netid):
        query = """ SELECT user_enterprise_password
                    FROM `ir_users`
                    WHERE user_netid = '%s' """ % netid
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]
