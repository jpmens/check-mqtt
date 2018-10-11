# check-mqtt

A [Nagios]/[Icinga] plugin for checking connectivity to an [MQTT] broker. Or with --readonly monitor an mqtt application. Or for checking the status of MQTT clients maintaining the status on an MQTT broker.

This plugin connects to the specified broker and subscribes to a topic. Upon successful subscription, a message is published to said topic, and the plugin expects to receive that payload within `max_wait` seconds.

## Prerequisite
This module needs jsonpath-rw. To install, use `$ pip install jsonpath-rw`

## Configuration

Configuration can be done via the following command line arguments:

```
usage: check-mqtt.py [-h] [-H <hostname>] [-P <port>] [-u <username>]
                     [-p <password>] [-m <seconds>] [-e <seconds>]
                     [--sleep <seconds>] [-a <cafile>] [-C <certfile>]
                     [-k <keyfile>] [-n] [-t <topic>] [-s <subscription>] [-r]
                     [-l <payload>] [-j <jsonpath>] [-v <value>]
                     [-o <operator>] [-w <expr>] [-c <expr>] [-S] [-V]

Nagios/Icinga plugin for checking connectivity or status of MQTT clients on an
MQTT broker.

optional arguments:
  -h, --help            show this help message and exit
  -H <hostname>, --host <hostname>
                        mqtt host to connect to (default: 'localhost')
  -P <port>, --port <port>
                        network port to connect to (default: 1883)
  -u <username>, --username <username>
                        MQTT username (default: None)
  -p <password>, --password <password>
                        MQTT password (default: None)
  -m <seconds>, --max-wait <seconds>
                        maximum time to wait for the check (default: 4
                        seconds)
  -e <seconds>, --keepalive <seconds>
                        maximum period in seconds allowed between
                        communications with the broker (default: 60 seconds)
  --sleep <seconds>     main loop sleep period in seconds (default: 0.1
                        seconds)
  -a <cafile>, --cafile <cafile>
                        cafile (default: None)
  -C <certfile>, --certfile <certfile>
                        certfile (default: None)
  -k <keyfile>, --keyfile <keyfile>
                        keyfile (default: None)
  -n, --insecure        suppress TLS verification of server hostname
  -t <topic>, --topic <topic>
                        topic to use for the active check (default:
                        'nagios/test')
  -s <subscription>, --subscription <subscription>
                        topic to use for the passive check (default: 'None')
  -r, --readonly        just read the value of the topic
  -l <payload>, --payload <payload>
                        payload which will be PUBLISHed (default: PiNG). If it
                        starts with an exclamation mark (!) the output of the
                        command will be used
  -j <jsonpath>, --jsonpath <jsonpath>
                        if given, payload is interpreted as JSON string and
                        value is extracted using <jsonpath> (default: 'None')
  -v <value>, --value <value>
                        value to compare against received payload (default:
                        'PiNG'). If it starts with an exclamation mark (!) the
                        output of the command will be used
  -o <operator>, --operator <operator>
                        operator to compare received value with value. Choose
                        from ['eq', 'equal', 'lt', 'lessthan', 'gt',
                        'greaterthan', 'ct', 'contains'] (default: 'equal').
                        'eq' compares Strings, the other convert the arguments
                        to float before compare
  -w <expr>, --warning <expr>
                        Exit with WARNING status if <expr> is true (default:
                        'None'). <expr> can be any Python expression, use
                        <payload> within expression for current payload value.
  -c <expr>, --critical <expr>
                        Exit with CRITICAL status if <expr> is true (default:
                        'None'). <expr> can be any Python expression, use
                        <payload> within expression for current payload value.
  -S, --short           use a shorter string on output
  -V, --version         show program's version number and exit

```

There are no required arguments, defaults are displayed using `--help`. If `--warning` and/or `--critical` is used then possible given `--operator` and `--value` arguments are ignored.

<dl>
  <dt>hostname, port, username, password</dt>
  used to connect to a MQTT broker
  
  <dt>cafile certfile keyfile insecure</dt>
  optional used for a encryptet TLS connection, for details see <a href="https://mosquitto.org/man/mosquitto-conf-5.html" target="_blank">mosquitto.conf</a> - Certificate based SSL/TLS Support.
  
  <dt>max_wait</dt>
  <dd>is the time (integer) we're willing to wait for a SUB to the topic we PUBlish on. If we don't receive the MQTT PUB within this many seconds we exist with _CRITICAL_</dd>
  
  <dt>keepalive</dt>
  <dd>maximum period in seconds (integer) allowed between communications with the broker. If no other messages are being exchanged, this controls the rate at which the client will send ping messages to the broker</dd>

  <dt>sleep</dt>
  <dd>period in seconds (float) to sleep in main loop - may reduce cpu load if a lot of processes (&gt;100) are running.</dd>

  <dt>topic</dt>
  <dd>topic where the <code>payload</code> will be published when we have received the subscribed message.</dd>

  <dt>payload</dt>
  <dd><code>payload</code> to publish on <code>topic</code>.</dd>

  <dt>subscription</dt>
  <dd>topic to use for the passive check - read only. If <code>subscription</code> is not given it will be set to <code>topic</code></dd>

  <dt>readonly</dt>
  <dd>just read on <code>subscription</code>, do not publish any <code>payload</code> on <code>topic</code></dd>

  <dt>jsonpath</dt>
  <dd>a JSONPath expression refering to a JSON structure (for JSONPath syntax see <a href="https://goessner.net/articles/JsonPath/" target="_blank">JSONPath expressions</a>)</dd>

  <dt>value, operator</dt>
  <dd><code>value</code> to compare against received payload. The comparison is done using one of the listed (see help above) operators. The returned status is <i>OK</i> if the comparison is true, otherwise it will return <i>CRITICAL</i>. If -w (--warning) or -c (--critical) argument is used, <code>value</code> and <code>operator</code> will be ignored.</dd>

  <dt>warning, critical</dt>
  <dd>a warning and/or critical expression. Use the word <code>payload</code> within your formular to refer to the read payload value.<br/>If both are given (warning and critical) the critical expression overrule the warning. <code>&lt;exp&gt;</code> can be any valid pyhton expression inclusive build-in and standard library functions e. g. conversion like <code>str()</code>, <code>float()</code>...<br/>Using one of them a possible <code>--value</code> and/or <code>--operator</code> argument will be ignored. </dd>

  <dt>short</dt>
  <dd>if set it will use a short string layout for returned message</dd>
</dl>


## Example

```
./check-mqtt.py -H localhost -P 1883 -u user -p password -t nagios/test -m 10

OK - message from nagios/test at localhost in 0.00 | response_time=0.10 value=PiNG
```

## Status check

```
./check-mqtt.py -H localhost -t devices/mydevice/lastevent -v '!expr `date +%s` - 216000' -r -o greaterthan

OK - message from devices/mydevice/lastevent at localhost in 0.05s | response_time=0.05 value=1472626997
```

## Ping Pong check

```
./check-mqtt.py -H localhost -t nagios/ListenForPing -s nagios/PublishPongTo -l ping -v pong

OK - message from nagios/PublishPongTo at localhost in 0.05s | response_time=0.05 value=pong
```

## Jsonpath check

```
./check-mqtt.py -H localhost -t devices/mydevice/sensor -v '950' -j '$.BME280.Pressure' -r -o greaterthan

OK - message from devices/mydevice/sensor at localhost in 0.06s | response_time=0.06 value=1005.0
```

## Jsonpath check using range (warning if lower than 4° or higher than 28°, critical if minus or higher than 35°)

```
./check-mqtt.py -H localhost -t devices/mydevice/sensor -v '950' -j '$.BME280.Temperature' -r --warning 'payload < 4 or payload >28' --critical 'payload < 0 or payload >35'

OK - message from devices/mydevice/sensor at localhost in 0.06s | response_time=0.06 value=20.1
```


## Nagios Configuration
### command definition
```
define command{
        command_name    check_mqtt
        command_line    $USER1$/check_mqtt
        }
        
define command{
        command_name    check_myapplication
        command_line    $USER1$/check_mqtt -i pong -t mytopic/test/myapplication
        }
```

### icinga2 command definition
```

object CheckCommand "check-mqtt" {
  import "plugin-check-command"

  command = [ PluginDir + "/check-mqtt.py" ] //constants.conf -> const PluginDir

  arguments = {
    "-H" = "$mqtt_host$"
    "-u" = "$mqtt_user$"
    "-p" = "$mqtt_password$"
    "-P" = "$mqtt_port$"
    "-a" = "$mqtt_cafile$"
    "-c" = "$mqtt_certfile$"
    "-k" = "$mqtt_keyfile$"
    "-t" = "$mqtt_topic$"
    "-m" = {
      set_if = "$mqtt_max$"
      value = "$mqtt_max$"
    }

    "-l" = "$mqtt_payload$"
    "-v" = "$mqtt_value$"
    "-o" = "$mqtt_operator$"

    "-r" = {
      set_if = "$mqtt_readonly$"
      description = "Don't write."
    }
    "-n" = {
      set_if = "$mqtt_insecure$"
      description = "suppress TLS hostname check"
    }
  }
}


```
### service definition
```
define service{
        use                             local-service
        host_name                       localhost
        service_description             mqtt broker
        check_command                   check_mqtt
        notifications_enabled           0
        }
        
define service{
        use                             local-service
        host_name                       localhost
        service_description             check if myapplication is running
        check_command                   check_myapplication
        notifications_enabled           0
        }
        
```

### icinga2 host definition
```
object Host "wemos1" {
  import "generic-host"
  check_command = "check-mqtt"

  vars.homie = true
  vars.lastevent = true

  vars.mqtt_host = "localhost"
#  vars.mqtt_port = 1883
#  vars.mqtt_user = "user"
#  vars.mqtt_password = "password"
#  vars.mqtt_cafile = "cafile"
#  vars.mqtt_certfile = "certfile"
#  vars.mqtt_keyfile = "keyfile"
  vars.mqtt_prefix = "devices/mydevice"

  vars.mqtt_topic = vars.mqtt_prefix + "/$$online"
  vars.mqtt_payload = "true"
  vars.mqtt_value = "true"
  vars.mqtt_operator = "equal"
  vars.mqtt_readonly = true

  vars.os = "Homie"
  vars.sla = "24x7"
}
```

### icinga2 service definition

```
apply Service "mqtt-health" {
  import "generic-service"

  check_command = "check-mqtt"

  assign where host.vars.mqtt == true
  ignore where host.vars.no_health_check == true
}

apply Service "homie-health" {
  import "generic-service"

  check_command = "check-mqtt"
  vars.mqtt_topic = host.vars.mqtt_prefix + "/$$online"
  vars.mqtt_payload = "true"
  vars.mqtt_value = "true"
  vars.mqtt_operator = "equal"
  vars.mqtt_readonly = true

  assign where host.vars.homie == true
  ignore where host.vars.no_health_check == true
}


apply Service "lastevent-health" {
  import "generic-service"

  check_command = "check-mqtt"

   vars.mqtt_topic = host.vars.mqtt_prefix + "/lastevent"
   vars.mqtt_payload = "true"
   vars.mqtt_value = "!expr `date +%s` - 21600"
   vars.mqtt_operator = "greaterthan"
   vars.mqtt_readonly = true

  assign where host.vars.lastevent == true
  ignore where host.vars.no_health_check == true
}
```

## Partial screenshot of Nagios and check_mqtt
![Nagios mqtt monitoring](assets/NagiosServiceCheck_mqtt.PNG?raw=true "Nagios Network Monitoring")

 [nagios]: http://nagios.org
 [icinga]: http://icinga.org
 [mqtt]: http://mqtt.org
