#!/usr/bin/python3
# -*- coding: utf-8 -*
import paho.mqtt.client as paho
import json, sys
from threading import Thread, Event
from miio.dreamevacuum import DreameVacuum


broker = "localhost"
vac = DreameVacuum("192.168.0.242", "717257585a4d5033436d4f616c673858")


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
            print(status)
        except Exception as ex:
            print("ERROR", ex)


timer = MyTimerThread()


def on_connect(client, userdata, flags, rc):
    global timer
    if rc==0:
        print("--> connected, rc: ", rc)
        client.subscribe("dreamevacuum/command/#")
        print("subscribed to topics")
        timer.start()
        print("status polling timer started")
    else:
        print("rc: ", rc)


def on_disconnect(client, empty, rc):
    global timer
    print("--> disconnected; rc: ", rc)
    timer.stop()
    print("status polling timer stopped")
    timer = MyTimerThread()


def on_message(client, userdata, message):
    try:
        payload = str(message.payload.decode("utf-8"))
        print("message received: {}".format(str(payload)))
        print("message topic: {}".format(message.topic))
    except:
        print("error:", sys.exc_info()[0])


def main():
    client = paho.Client("client-001")
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


main()

