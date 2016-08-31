# check-mqtt

A [Nagios]/[Icinga] plugin for checking connectivity to an [MQTT] broker. Or with --ignoreping monitor an mqtt application. Or for checking the status of MQTT clients maintaining the status on an MQTT broker.

This plugin connects to the specified broker and subscribes to a topic. Upon successful subscription, a message is published to said topic, and the plugin expects to receive that payload within `max_wait` seconds.

## Configuration

Configuration can be done via the following command line arguments:

```
usage: check-mqtt.py [-h] [-H <hostname>] [-P <port>] [-u <username>] [-p <password>] [-m <seconds>] [-a <cafile>]
                     [-c <certfile>] [-k <keyfile>] [-n] [-t <topic>] [-r] [-l <payload>] [-v <value>]
                     [-o <operator>]

optional arguments:
  -h, --help            show this help message and exit
  -H <hostname>, --host <hostname>
                        mqtt host to connect to (defaults to localhost)
  -P <port>, --port <port>
                        network port to connect to (defaults to 1883)
  -u <username>, --username <username>
                        MQTT username (defaults to None)
  -p <password>, --password <password>
                        MQTT password (defaults to None)
  -m <seconds>, --max-wait <seconds>
                        maximum time to wait for the check (defaults to 4 seconds)
  -a <cafile>, --cafile <cafile>
                        cafile (defaults to None)
  -c <certfile>, --certfile <certfile>
                        certfile (defaults to None)
  -k <keyfile>, --keyfile <keyfile>
                        keyfile (defaults to None)
  -n, --insecure        suppress TLS verification of server hostname
  -t <topic>, --topic <topic>
                        topic to use for the check (defaults to nagios/test)
  -r, --readonly        just read the value of the topic
  -l <payload>, --payload <payload>
                        payload which will be PUBLISHed (defaults to 'PiNG'). If it begins with !, output of the
                        command will be used
  -v <value>, --value <value>
                        value to compare against received payload (defaults to 'PiNG'). If it begins with !,
                        output of the command will be used
  -o <operator>, --operator <operator>
                        operator to compare received value with value. Coose from 'equal' (default), 'lessthan',
                        and 'greaterthan'. 'equal' compares Strings, the other two convert the arguments to int
```

`max_wait` is the time we're willing to wait for a SUB to the topic we PUBlish on. If we don't receive the MQTT PUB within this many seconds we exist with _CRITICAL_.

## Example



```
./check-mqtt.py -H localhost -P 1883 -u user -p password -t nagios/test -m 10

OK - message from nagios/test at localhost in 0.00 | response_time=0.10 value=PiNG
```

## Status check example

```
./check-mqtt.py -H localhost -t devices/mydevice/lastevent -v '!expr `date +%s` - 216000' -r -o greaterthan

OK - message from devices/mydevice/lastevent at localhost in 0.05s | response_time=0.05 value=1472626997
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
