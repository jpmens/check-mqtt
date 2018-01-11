#!/usr/bin/env python

# Copyright (c) 2013-2015 Jan-Piet Mens <jpmens()gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of mosquitto nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import paho.mqtt.client as paho
import ssl
import time
import sys
import os
import argparse
import subprocess

status = 0
message = ''
args = {}

nagios_codes = [ 'OK', 'WARNING', 'CRITICAL', 'UNKNOWN' ]

def on_connect(mosq, userdata, flags, rc):
    """
    Upon successfully being connected, we subscribe to the check_topic
    """

    mosq.subscribe(args.check_topic, 0)

def on_publish(mosq, userdata, mid):
    pass

def on_subscribe(mosq, userdata, mid, granted_qos):
    """
    When the subscription is confirmed, we publish our payload
    on the check_topic. Since we're subscribed to this same topic,
    on_message() will fire when we see that same message
    """

    if not args.mqtt_readonly:
        (res, mid) =  mosq.publish(args.check_topic, args.mqtt_payload, qos=2, retain=False)

def on_message(mosq, userdata, msg):
    """
    This is invoked when we get our own message back. Verify that it
    is actually our message and if so, we've completed a round-trip.
    """

    global message
    global status

    elapsed = (time.time() - userdata['start_time'])
    userdata['have_response'] = True
    status = 2
    if args.short_output == True:
        message = "value=%s | response_time=%.2f value=%s" % (str(msg.payload), elapsed, str(msg.payload))
    else:
        message = "message from %s at %s in %.2fs | response_time=%.2f value=%s" % (args.check_topic, args.mqtt_host, elapsed, elapsed, str(msg.payload))

    if args.mqtt_operator == 'lessthan' and float(msg.payload) < float(args.mqtt_value):
        status = 0
    if args.mqtt_operator == 'greaterthan' and float(msg.payload) > float(args.mqtt_value):
        status = 0
    if args.mqtt_operator == 'equal' and str(msg.payload) == args.mqtt_value:
        status = 0
    if args.mqtt_operator == 'contains' and str(msg.payload).find(args.mqtt_value) != -1:
        status = 0

        
def on_disconnect(mosq, userdata, rc):

    if rc != 0:
        exitus(1, "Unexpected disconnection. Incorrect credentials?")

def exitus(status=0, message="all is well"):
    """
    Produce a Nagios-compatible single-line message and exit according
    to status
    """

    print "%s - %s" % (nagios_codes[status], message)
    sys.exit(status)


parser = argparse.ArgumentParser()
parser.add_argument('-H', '--host', metavar="<hostname>", help="mqtt host to connect to (defaults to localhost)", dest='mqtt_host', default="localhost")
parser.add_argument('-P', '--port', metavar="<port>", help="network port to connect to (defaults to 1883)", dest='mqtt_port', default=1883, type=int)

parser.add_argument('-u', '--username', metavar="<username>", help="MQTT username (defaults to None)", dest='mqtt_username', default=None)
parser.add_argument('-p', '--password', metavar="<password>", help="MQTT password (defaults to None)", dest='mqtt_password', default=None)

parser.add_argument('-m', '--max-wait', metavar="<seconds>", help="maximum time to wait for the check (defaults to 4 seconds)", dest='max_wait', default=4, type=int)

parser.add_argument('-a', '--cafile', metavar="<cafile>", help="cafile (defaults to None)", dest='mqtt_cafile', default=None)
parser.add_argument('-c', '--certfile', metavar="<certfile>", help="certfile (defaults to None)", dest='mqtt_certfile', default=None)
parser.add_argument('-k', '--keyfile', metavar="<keyfile>", help="keyfile (defaults to None)", dest='mqtt_keyfile', default=None)
parser.add_argument('-n', '--insecure', help="suppress TLS verification of server hostname", dest='mqtt_insecure', default=False, action='store_true')

parser.add_argument('-t', '--topic', metavar="<topic>", help="topic to use for the check (defaults to nagios/test)", dest='check_topic', default='nagios/test')
parser.add_argument('-r', '--readonly', help="just read the value of the topic", dest='mqtt_readonly', default=False, action='store_true')
parser.add_argument('-l', '--payload', metavar="<payload>", help="payload which will be PUBLISHed (defaults to 'PiNG'). If it begins with !, output of the command will be used", dest='mqtt_payload', default='PiNG')
parser.add_argument('-v', '--value', metavar="<value>", help="value to compare against received payload (defaults to 'PiNG'). If it begins with !, output of the command will be used", dest='mqtt_value', default='PiNG')
parser.add_argument('-o', '--operator', metavar="<operator>", help="operator to compare received value with value. Coose from 'equal' (default), 'lessthan', 'greaterthan' and 'contains'. 'equal' compares Strings, the other two convert the arguments to int", dest='mqtt_operator', default='equal', choices=['equal','lessthan','greaterthan','contains'])
parser.add_argument('-S', '--short', help="use a shorter string on output", dest='short_output', default=False, action='store_true')

args = parser.parse_args()

#print args

if args.mqtt_payload.startswith('!'):
    try:
     args.mqtt_payload = subprocess.check_output(args.mqtt_payload[1:], shell=True) 
    except:
        pass

if args.mqtt_value.startswith('!'):
    try:
        args.mqtt_value = subprocess.check_output(args.mqtt_value[1:], shell=True) 
    except:
        pass

userdata = {
    'have_response' : False,
    'start_time'    : time.time(),
}
mqttc = paho.Client('nagios-%d' % (os.getpid()), clean_session=True, userdata=userdata, protocol=4)
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe

# cafile controls TLS usage
if args.mqtt_cafile is not None:
    if args.mqtt_certfile is not None:
        mqttc.tls_set(args.mqtt_cafile,
        certfile=args.mqtt_certfile,
        keyfile=args.mqtt_keyfile,
        cert_reqs=ssl.CERT_REQUIRED)
    else:
        mqttc.tls_set(args.mqtt_cafile,
        cert_reqs=ssl.CERT_REQUIRED)
    mqttc.tls_insecure_set(args.mqtt_insecure)

# username & password may be None
if args.mqtt_username is not None:
    mqttc.username_pw_set(args.mqtt_username, args.mqtt_password)

# Attempt to connect to broker. If this fails, issue CRITICAL

try:
    mqttc.connect(args.mqtt_host, args.mqtt_port, 60)
except Exception, e:
    status = 2
    message = "Connection to %s:%d failed: %s" % (args.mqtt_host, args.mqtt_port, str(e))
    exitus(status, message)

rc = 0
while userdata['have_response'] == False and rc == 0:
    rc = mqttc.loop()
    if time.time() - userdata['start_time'] > args.max_wait:
        message = 'timeout waiting for message'
        status = 2
        break

mqttc.disconnect()

exitus(status, message)

