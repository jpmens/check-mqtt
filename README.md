# check-mqtt

A [Nagios]/[Icinga] plugin for checking connectivity to an [MQTT] broker.

This plugin connects to the specified broker and subscribes to a topic. Upon successful subscription, a message is published to said topic, and the plugin expects to receive that payload within `max_wait` seconds.

## Configuration

Configuration can be done via the following command line arguments:

```
 -H <hostname>, --host <hostname>
                        mqtt host to connect to (defaults to localhost)
 -P <port>, --port <port>
                        network port to connect to (defaults to 1883)
 -u <username>, --username <username>
                        username
 -p <password>, --password <password>
                        password
 -t <topic>, --topic <topic>
                        topic to use for the check (defaults to nagios/test)
 -m <seconds>, --max-wait <seconds>
                        maximum time to wait for the check (defaults to 4
                        seconds)
```

`max_wait` is the time we're willing to wait for a SUB to the topic we PUBlish on. If we don't receive the MQTT PUB within this many seconds we exist with _CRITICAL_.

## Example



```
./check-mqtt.py -H localhost -P 1883 -u user -p password -t nagios/test -m 10

OK - PUB to nagios/test at localhost responded in 0.00
```

## Nagios Configuration

### command definition
```
define command{
        command_name    check-mqtt
        command_line    $USER1$/check-mqtt
        }
```
### service definition
```
define service{
        use                             local-service
        host_name                       localhost
        service_description             mqtt broker
        check_command                   check-mqtt
        notifications_enabled           0
        }
```

 [nagios]: http://nagios.org
 [icinga]: http://icinga.org
 [mqtt]: http://mqtt.org
