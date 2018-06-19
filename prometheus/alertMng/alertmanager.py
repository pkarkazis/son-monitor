'''
## ALL RIGHTS RESERVED.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
## Neither the name of the SONATA-NFV, 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).
##
## This work has been performed in the framework of the 5GTANGO project,
## funded by the European Commission under Grant number 761493 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the 5GTANGO
## partner consortium (www.5gtango.eu).
# encoding: utf-8
'''

from influxDB import influx
from msg_pools import msgs
import json, os, base64
import time, threading, urllib2
from threading import  Thread 
from rabbitMQ import amqp
from emailNotifier import emailNotifier  


__author__="panos"

def checkServPlatform(time_window):
    global count
    cl = influx('influx',8086,'','','prometheus')
    if not cl.checkDB('prometheus'):
        print 'Influx prometeheus DB not found'
        return
    
    resp = cl.query('select * from ALERTS where alertstate=\'firing\' and value=1 and time > now() - '+ time_window)
    if 'series' in resp:
        for serie in resp['series']:
            for rec in serie['values']:
                obj = pool.list2obj(rec,serie['columns'])
                if 'serviceID' in obj:
                    if ns_exists(obj['serviceID']):
                        pool.addQueueMsg(obj)
                else:
                    pool.addQueueMsg(obj)
        
    
    resp = cl.query('select * from ALERTS where alertstate=\'pending\' and value=0 and time > now() - '+ time_window)
    if 'series' in resp:
        if debug == 1:
            print 'Event Started'
        for serie in resp['series']:
            for rec in serie['values']:
                obj = pool.list2obj(rec,serie['columns'])
                if 'serviceID' in obj:
                    if ns_exists(obj['serviceID']):
                        pool.addEmailMsg(obj)
                        pool.addSmsMsg(obj)
                else:
                    pool.addEmailMsg(obj)
                    pool.addSmsMsg(obj)
    
    resp = cl.query('select * from ALERTS where alertstate=\'firing\' and value=0 and time > now() - '+ time_window)
    if 'series' in resp:
        if debug == 1:
            print 'Event Stoped'
        for serie in resp['series']:
            for rec in serie['values']:
                obj = pool.list2obj(rec,serie['columns'])
                if 'serviceID' in obj:
                    if ns_exists(obj['serviceID']):
                        pool.addEmailMsg(obj)
                        pool.addSmsMsg(obj)
                else:
                    pool.addEmailMsg(obj)
                    pool.addSmsMsg(obj)
        
def checkAlerts():
    if debug == 1:
        print(time.ctime())
    checkServPlatform('15s')
    threading.Timer(10, checkAlerts).start()


def emailConsumer(pool_):
    while 1:
        if len(pool_) > 0:
            
            mailNotf = emailNotifier()
            msgs = pool_
            if debug == 1:
                print 'send mails : ' + json.dumps(msgs) +' number of mails: '+ "".join(str(len(msgs)))
            mailNotf.msgs2send(msgs)
            del pool_[:]
            #msg = pool_[0]
            #del pool_[0]
        time.sleep(4)
        
def smsConsumer(pool_):
    vm_dt = ''
    while 1:
        if len(pool_) > 0:
            msg = pool_[0]
            del pool_[0]
            if debug == 1:
                print 'send sms : ' + json.dumps(msg) +' remain: '+ "".join(str(len(pool_)))
        time.sleep(0.2)

def ns_exists(serv_id):
        mails=[]
        try:
            url = 'http://manager:8000/api/v1/service/'+serv_id+'/'
            req = urllib2.Request(url)
            req.add_header('Content-Type','application/json')        
            response=urllib2.urlopen(req, timeout = 3)
            code = response.code
            data = json.loads(response.read())
            if data['count'] > 0:    
                return True
            else:
                return False

        except urllib2.HTTPError, e:
            return {'error':str(e)}
        except urllib2.URLError, e:
            return {'error':str(e)}
        except ValueError, e:
            return {'error':str(e)}
        
def rabbitConsumer(pool_):
    try:
        rabbit = getRabbitUrl()
        if rabbit == '':
            raise ValueError('Rabbimq url unset') 
        host = rabbit.split(':')[0]
        port = int(rabbit.split(':')[1])
    except ValueError as err:
        print(err.args)
        return

    while 1:
        if len(pool_) > 0:
            if rabbit == '':
                return
            msg = pool_[0]
            type = 'undefined tp'
            topic = 'son.monitoring'
            if 'tp' in msg:
                if msg['tp'] == 'DEV':
                    type='dev'
                    topic = 'son.monitoring'
                else:
                    type=msg['tp']
                    topic = 'son.monitoring.'+msg['tp']
            rmq = amqp(host, port, topic, 'guest', 'guest')
            rmq.send(json.dumps(msg))
            del pool_[0]
            if debug == 1:
                print 'send rabbitmq : ' + msg['alertname'] + ' '+ msg['exported_instance'] +' '+ type +' remain: '+ "".join(str(len(pool_)))
        

def getRabbitUrl():
    if os.environ.has_key('RABBIT_URL'):
        return str(os.environ['RABBIT_URL']).strip()
    else:
        return ''

def getEmailPass():
    if os.environ.has_key('EMAIL_PASS'):
        key = str(os.environ['EMAIL_PASS']).strip()
        return key.decode('base64')
    else:
        return ''


if __name__ == "__main__":
    global pool
    global debug
    debug = 0
    count = 0
    if os.environ.has_key('DEBUG'):
        debug = int(os.environ['DEBUG'])
    pool = msgs()
    t1 = Thread(target = emailConsumer, args=(pool.getEmailMsgs(),))
    t2 = Thread(target = smsConsumer, args=(pool.getSmsMsgs(),))
    t3 = Thread(target = rabbitConsumer, args=(pool.getQueueMsgs(),))
    t1.daemon = True
    t2.daemon = True
    t3.daemon = True
    t1.start()
    t2.start()
    t3.start()
    
    print(time.ctime())
    print(getEmailPass())
    print(getRabbitUrl())
    checkServPlatform('15s')    
    threading.Timer(7, checkAlerts).start()
