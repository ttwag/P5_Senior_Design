import os

from awsiot import mqtt_connection_builder
from awscrt import mqtt
from uuid import uuid4
import boto3
import logging
import json
import time
import threading

from botocore.exceptions import ClientError

# Global Start event that synchronizes the threads and indicates the Start and Stop of the Pi.
start_event = threading.Event()


def read_file(file_path):
    """
    Read the file content of the keys
    """
    with open(file_path, 'r') as file:
        file_content = file.read()
    return file_content


def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    """
    Callback function that MQTT calls when a message is received
    """
    global start_event, stop_event
    message = json.loads(payload)['message']
    print("Received message from topic '{}': {}".format(topic, json.loads(payload)['message']))
    if message == 'Start':
        start_event.set()
    else:
        start_event.clear()


def pi_state():
    """
    The Raspberry Pi's current state.
    This function runs on a separate thread and goes into the start state if the Start event is set.
    Otherwise, it waits indefinitely in the Stop state.
    It sends images continuously while it's in the Start state
    """
    count = 0
    while True:
        start_event.wait()  # Wait at the Stop state
        # Configure the s3 bucket client
    #    s3 = boto3.client('s3')
        count = count + 1
        print("I am sending images")
        # with open("test15.jpeg", "rb") as f:
        #     s3.upload_fileobj(f, "eec175test1bucket173409-dev", f"test{count}.jpeg")
        time.sleep(5)


if __name__ == '__main__':
    '''
    The main function that sets up the MQTT connection to subscribe to a topic 
    and creates the separate thread for the pi_state function
    Note: before running this main function, remember to configure the AWS credentials in the command line so the 
    S3 bucket could be used
    '''
    # Create a MQTT connection
    try:
        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=read_file("./certs/endpoint.txt"),
            port=8883,
            cert_filepath='./certs/certificate.pem.crt',
            pri_key_filepath='./certs/private.pem.key',
            ca_filepath='./certs/AmazonRootCA1.pem',
            client_id="test-" + str(uuid4()),
            clean_session=False,
            keep_alive_secs=60)
        connect_future = mqtt_connection.connect()
        connect_future.result()
    except:
        print("Cannot Establish a Connection with MQTT")
    print("Connected!")

    # Subscribing to a topic
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic='topic_1',
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

    # Create a separate thread for the pi_state()
    state_thread = threading.Thread(target=pi_state)
    state_thread.start()
    state_thread.join() # main thread waits for state_thread

