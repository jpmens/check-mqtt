# check-mqtt

A [Nagios]/[Icinga] plugin for checking connectivity to an [MQTT] broker. Or with --ignoreip monitor an mqtt application.

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
 -i <pong>, --ignoreping <pong>
                        Ignore our ping respond to monitored client's returned 'pong'                   
```

`max_wait` is the time we're willing to wait for a SUB to the topic we PUBlish on. If we don't receive the MQTT PUB within this many seconds we exist with _CRITICAL_.

## Example



```
./check-mqtt.py -H localhost -P 1883 -u user -p password -t nagios/test -m 10

OK - PUB to nagios/test at localhost responded in 0.00
```


## Ping / Pong Configuration
In the ping/pong configuration check_mqtt ignores it's own ping, responding to a monitored application's pong response from check_mqtt's ping. You must configure your application to respond to the topic and ping you have configured in check_mqtt.

### Example
```
check_mqtt -t mytopic/test/myapplication -i pong 

OK - Publish to mytopic/test/myapplication at localhost responded in 0.05 with msg pong
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
## Partial screenshot of Nagios and check_mqtt
![Nagios mqtt monitoring](assets/NagiosServiceCheck_mqtt.PNG?raw=true "Nagios Network Monitoring")

 [nagios]: http://nagios.org
 [icinga]: http://icinga.org
 [mqtt]: http://mqtt.org
