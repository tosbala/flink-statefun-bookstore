from time import sleep
import csv
import random
import json

from kafka import KafkaProducer

from models import Order


def get_book_list():
    available_books = dict()

    with open('stock.csv', "r") as in_file:
        reader = csv.reader(in_file)
        for row in reader:
            if row[0] != 'isbn':
                available_books[row[0]] = row[1]
    
    return available_books


def place_orders(book_list, no_of_orders):
    sleep(5)
    producer = KafkaProducer(bootstrap_servers=['kafka:9092'])

    for i in range(no_of_orders):
        selection = random.choice(list(book_list.keys()))
        order = Order(buyer=random.choice(['aviz', 'ishbi', 'santi']), isbn=selection)
        value = json.dumps(order.__dict__).encode()
        producer.send(topic='orders', key=selection.encode(), value=json.dumps(order.__dict__).encode())
        
        print(f"placed the order for book '{book_list[selection]}'", flush=True)

        sleep(10)


if __name__ == '__main__':
    book_list = get_book_list()
    place_orders(book_list=book_list, no_of_orders=25)