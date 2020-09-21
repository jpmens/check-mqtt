#!/usr/bin/env python3
# -*- coding: utf-8 -*-
VER = '3.1'

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
try:
    from jsonpath_rw import jsonpath, parse
    module_jsonpath_rw = True
except ImportError:
    module_jsonpath_rw = False
try:
    import json
    module_json = True
except ImportError:
    module_json = False
import ssl
import time
import sys
import os
import argparse
import subprocess
try:
    import math
    module_math = True
except ImportError:
    module_math = False

PROG='{} v{}'.format(os.path.basename(sys.argv[0]),VER)

class Status:
    OK = 0
    WARNING=1
    CRITICAL=2
    UNKNOWN=3
nagios_codes = [ 'OK', 'WARNING', 'CRITICAL', 'UNKNOWN' ]

DEFAULTS = {
    'mqtt_host':        'localhost',
    'mqtt_port':        1883,
    'mqtt_username':    None,
    'mqtt_password':    None,
    'max_wait':         4,
    'keepalive':        60,
    'sleep':            0.1,
    'mqtt_cafile':      None,
    'mqtt_certfile':    None,
    'mqtt_keyfile':     None,
    'mqtt_insecure':    False,
    'check_topic':      'nagios/test',
    'check_subscription':None,
    'mqtt_readonly':    False,
    'mqtt_payload':     'PiNG',
    'mqtt_jsonpath':    None,
    'mqtt_value':       'PiNG',
    'mqtt_operator':    'equal',
    'warning':          None,
    'critical':         None,
    'short_output':     False,
    'debug':            False,
}

operators = ['eq','equal','lt','lessthan','gt','greaterthan','ct','contains','any']

status = Status.OK
message = ''
args = {}


def on_connect(mosq, userdata, flags, rc):
    """
    Upon successfully being connected, we subscribe to the check_topic
    """

    mosq.subscribe(args.check_subscription, 0)
    mosq.loop()

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
        mosq.loop()

def on_message(mosq, userdata, msg):
    """
    This is invoked when we get our own message back. Verify that it
    is actually our message and if so, we've completed a round-trip.
    """


    global message
    global status

    payload = msg.payload.decode("utf-8")

    if module_jsonpath_rw and module_json:
        if args.mqtt_jsonpath is not None:
            try:
                jspayload = json.loads(payload)
                jspath = parse(args.mqtt_jsonpath)
                extractpayload = [match.value for match in jspath.find(jspayload)]
                payload = extractpayload[0]
            except:
                payload = ''
                pass

    
    elapsed = (time.time() - userdata['start_time'])
    userdata['have_response'] = True

    if args.short_output:
        message = "value=%s | response_time=%.2f value=%s" % (str(payload), elapsed, str(payload))
    else:
        message = "message from %s at %s in %.2fs | response_time=%.2f value=%s" % (args.check_subscription, args.mqtt_host, elapsed, elapsed, str(payload))

    if module_math and (args.critical is not None or args.warning is not None):
        status = Status.OK
        if args.critical is not None:
            try:
                if eval(args.critical):
                    status = Status.CRITICAL
            except:
                status = Status.CRITICAL
                message = "critical expression error '{}'".format(args.critical)
                pass
        if status == Status.OK and args.warning is not None:
            try:
                if eval(args.warning):
                    status = Status.WARNING
            except:
                status = Status.CRITICAL
                message = "warning expression error '{}'".format(args.warning)
                pass
    else:
        status = Status.CRITICAL
        try:
            if (args.mqtt_operator == 'lt' or args.mqtt_operator == 'lessthan') and float(payload) < float(args.mqtt_value):
                status = Status.OK
            if (args.mqtt_operator == 'gt' or args.mqtt_operator == 'greaterthan') and float(payload) > float(args.mqtt_value):
                status = Status.OK
            if (args.mqtt_operator == 'eq' or args.mqtt_operator == 'equal') and str(payload) == args.mqtt_value:
                status = Status.OK
            if (args.mqtt_operator == 'ct' or args.mqtt_operator == 'contains') and str(payload).find(args.mqtt_value) != -1:
                status = Status.OK
            if (args.mqtt_operator == 'any') and payload:
                status = Status.OK
        except:
            status = Status.CRITICAL
            pass

def on_log(mosq, userdata, level, buf):
    print(buf, file=sys.stderr)

def on_disconnect(mosq, userdata, rc):

    if rc != 0:
        exitus(1, "Unexpected disconnection. Incorrect credentials?")

def exitus(status=Status.OK, message="all is well"):
    """
    Produce a Nagios-compatible single-line message and exit according
    to status
    """

    print("%s - %s" % (nagios_codes[status], message))
    sys.exit(status)

parser = argparse.ArgumentParser(description='Nagios/Icinga plugin for checking connectivity or status of MQTT clients on an MQTT broker.',
                                 epilog='There are no required arguments, defaults are displayed using --help. If --warning and/or --critical is used then possible given --operator and --value arguments are ignored.')

parser.add_argument('-d', '--debug', default=False, help="enable MQTT logging", action='store_true', dest='debug')

parser.add_argument('-H', '--host', metavar="<hostname>", help="mqtt host to connect to (default: '{}')".format(DEFAULTS['mqtt_host']), dest='mqtt_host', default=DEFAULTS['mqtt_host'])
parser.add_argument('-P', '--port', metavar="<port>", help="network port to connect to (default: {})".format(DEFAULTS['mqtt_port']), dest='mqtt_port', default=DEFAULTS['mqtt_port'], type=int)

parser.add_argument('-u', '--username', metavar="<username>", help="MQTT username (default: {})".format(DEFAULTS['mqtt_username']), dest='mqtt_username', default=DEFAULTS['mqtt_username'])
parser.add_argument('-p', '--password', metavar="<password>", help="MQTT password (default: {})".format(DEFAULTS['mqtt_password']), dest='mqtt_password', default=DEFAULTS['mqtt_password'])

parser.add_argument('-m', '--max-wait', metavar="<seconds>", help="maximum time to wait for the check (default: {} seconds)".format(DEFAULTS['max_wait']), dest='max_wait', default=DEFAULTS['max_wait'], type=int)
parser.add_argument('-e', '--keepalive', metavar="<seconds>", help="maximum period in seconds allowed between communications with the broker (default: {} seconds)".format(DEFAULTS['keepalive']), dest='keepalive', default=DEFAULTS['keepalive'], type=int)
parser.add_argument(      '--sleep', metavar="<seconds>", help="main loop sleep period in seconds (default: {} seconds)".format(DEFAULTS['sleep']), dest='sleep', default=DEFAULTS['sleep'], type=float)

parser.add_argument('-a', '--cafile', metavar="<cafile>", help="cafile (default: {})".format(DEFAULTS['mqtt_cafile']), dest='mqtt_cafile', default=DEFAULTS['mqtt_cafile'])
parser.add_argument('-C', '--certfile', metavar="<certfile>", help="certfile (default: {})".format(DEFAULTS['mqtt_certfile']), dest='mqtt_certfile', default=DEFAULTS['mqtt_certfile'])
parser.add_argument('-k', '--keyfile', metavar="<keyfile>", help="keyfile (default: {})".format(DEFAULTS['mqtt_keyfile']), dest='mqtt_keyfile', default=DEFAULTS['mqtt_keyfile'])
parser.add_argument('-n', '--insecure', help="suppress TLS verification of server hostname{}".format(" (default)" if DEFAULTS['mqtt_insecure'] else ""), dest='mqtt_insecure', default=DEFAULTS['mqtt_insecure'], action='store_true')

parser.add_argument('-t', '--topic', metavar="<topic>", help="topic to use for the active check (default: '{}')".format(DEFAULTS['check_topic']), dest='check_topic', default=DEFAULTS['check_topic'])
parser.add_argument('-s', '--subscription', metavar="<subscription>", help="topic to use for the passive check (default: '{}')".format(DEFAULTS['check_subscription']), dest='check_subscription', default=DEFAULTS['check_subscription'])
parser.add_argument('-r', '--readonly', help="just read the value of the topic{}".format(" (default)" if DEFAULTS['mqtt_readonly'] else ""), dest='mqtt_readonly', default=DEFAULTS['mqtt_readonly'], action='store_true')
parser.add_argument('-l', '--payload', metavar="<payload>", help="payload which will be PUBLISHed (default: {}). If it starts with an exclamation mark (!) the output of the command will be used".format(DEFAULTS['mqtt_payload']), dest='mqtt_payload', default=DEFAULTS['mqtt_payload'])
if module_jsonpath_rw and module_json:
    parser.add_argument('-j', '--jsonpath', metavar="<jsonpath>", help="if given, payload is interpreted as JSON string and value is extracted using <jsonpath> (default: '{}')".format(DEFAULTS['mqtt_jsonpath']), dest='mqtt_jsonpath', default=DEFAULTS['mqtt_jsonpath'])
parser.add_argument('-v', '--value', metavar="<value>", help="value to compare against received payload (default: '{}'). If it starts with an exclamation mark (!) the output of the command will be used".format(DEFAULTS['mqtt_value']), dest='mqtt_value', default=DEFAULTS['mqtt_value'])
parser.add_argument('-o', '--operator', metavar="<operator>", help="operator to compare received value with value. Choose from {} (default: '{}'). 'eq' compares Strings, the other convert the arguments to float before compare".format(operators, DEFAULTS['mqtt_operator']), dest='mqtt_operator', default=DEFAULTS['mqtt_operator'], choices=operators)
if module_math:
    parser.add_argument('-w', '--warning', metavar="<expr>", help="Exit with WARNING status if <expr> is true (default: '{}'). <expr> can be any Python expression, use <payload> within expression for current payload value.".format(DEFAULTS['warning']), dest='warning', default=DEFAULTS['warning'])
    parser.add_argument('-c', '--critical', metavar="<expr>", help="Exit with CRITICAL status if <expr> is true (default: '{}'). <expr> can be any Python expression, use <payload> within expression for current payload value.".format(DEFAULTS['critical']), dest='critical', default=DEFAULTS['critical'])
parser.add_argument('-S', '--short', help="use a shorter string on output{}".format(" (default)" if DEFAULTS['short_output'] else ""), dest='short_output', default=DEFAULTS['short_output'], action='store_true')
parser.add_argument('-V', '--version',  action='version', version=PROG)

args = parser.parse_args()

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

if args.check_subscription is None:
    args.check_subscription = args.check_topic

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

if args.debug:
    mqttc.on_log = on_log

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
    mqttc.connect(args.mqtt_host, args.mqtt_port, args.keepalive)
except Exception as e:
    status = Status.CRITICAL
    message = "Connection to %s:%d failed: %s" % (args.mqtt_host, args.mqtt_port, str(e))
    exitus(status, message)

rc = 0
while userdata['have_response'] == False and rc == 0:
    rc = mqttc.loop()
    if time.time() - userdata['start_time'] > args.max_wait:
        message = 'timeout waiting for message'
        status = Status.CRITICAL
        break
    time.sleep(args.sleep)

mqttc.disconnect()

exitus(status, message)
