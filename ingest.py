import json
from sseclient import SSEClient
from google.cloud import pubsub_v1
from config import topic

WIKI_SSE_URL = 'https://stream.wikimedia.org/v2/stream/recentchange'
publisher = pubsub_v1.PublisherClient()

def callback(future):
    '''Callback for when publishing completes'''
    if future.exception():
        print(f"Publishing message threw an exception {future.exception()}.")
    else:
        print("Published message to topic.")

def publish_to_pubsub(message):
    '''Publishes a message to a pub/sub topic'''
    data = json.dumps(message).encode("utf-8")
    future = publisher.publish(topic, data=data)
    future.add_done_callback(callback)

def main():
    try:
        response = SSEClient(WIKI_SSE_URL)
        for event in response:
            if event.event == "message":
                try:
                    message = json.loads(event.data)
                    publish_to_pubsub(message)
                except json.JSONDecodeError:
                    continue
                except ValueError:
                    pass
                else:   #discard canary events
                    if message['meta']['domain'] == 'canary': continue
    except KeyboardInterrupt:
        print("\nStopping ingestion...")

if __name__ == "__main__":
    main()
