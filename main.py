#!/usr/bin/python3
# -*- coding: utf-8 -*
import paho.mqtt.client as paho
import json, sys, getopt
from threading import Thread, Event
from miio.dreamevacuum import DreameVacuum

vac = None
client = None


class MyTimerThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.stopped = Event()

    def run(self):
        try:
            self.stopped.clear()
            while not self.stopped.wait(10):
                self.poll_status()
        except Exception as ex:
            print("ERROR", ex)

    def stop(self):
        self.stopped.set()

    def poll_status(self):
        try:
            print("polling Dreame status")
            status = vac.status()
            status_dict = status.__dict__
            client.publish("dreamevacuum/status", json.dumps(status_dict))
            for prop, value in status_dict.items():
                client.publish("dreamevacuum/properties/" + prop, value)
        except Exception as ex:
            print("ERROR", ex)


timer = MyTimerThread()


def on_connect(c, userdata, flags, rc):
    global timer
    if rc == 0:
        print("--> connected, rc: ", rc)
        c.subscribe("dreamevacuum/command/#")
        print("subscribed to topics")
        timer.start()
        print("status polling timer started")
    else:
        print("rc: ", rc)


def on_disconnect(c, empty, rc):
    global timer
    print("--> disconnected; rc: ", rc)
    timer.stop()
    timer.join()
    print("status polling timer stopped")
    timer = MyTimerThread()


def on_message(c, userdata, message):
    try:
        payload = str(message.payload.decode("utf-8"))
        print("message received: {}".format(str(payload)))
        print("message topic: {}".format(message.topic))
    except:
        print("error:", sys.exc_info()[0])


def main(argv):
    global vac, client
    broker = "localhost"
    vacuum_ip = "na"
    vacuum_token = "na"
    try:
        opts, args = getopt.getopt(argv, "bh:vip:vt", ["broker_host=", "vacuum_ip=", "vacuum_token="])
    except getopt.GetoptError as ex:
        print("ERROR", ex)
        print('main.py -bh <broker host> -bp <broker port> -vip <vacuum ip> -vt <vacuum token>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-bh", "--broker_host"):
            broker = arg
        elif opt in ("-vip", "--vacuum_ip"):
            vacuum_ip = arg
        elif opt in ("-vt", "--vacuum_token"):
            vacuum_token = arg
    vac = DreameVacuum(vacuum_ip, vacuum_token)

    client = paho.Client("client-dreame-vacuum-001")
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=3, max_delay=30)

    print("connecting to broker: ", broker)
    client.connect(broker)
    try:
        client.loop_forever()
    except:
        pass

    print("stopping...")
    client.disconnect()
    client.loop_stop()


if __name__ == "__main__":
    main(sys.argv[1:])
