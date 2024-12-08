import pika

def callback(ch, method, properties, body):
    print(f"Received: {body.decode()}")

def receive_message():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='car_listings')

    channel.basic_consume(queue='car_listings', on_message_callback=callback, auto_ack=True)

    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    receive_message()
