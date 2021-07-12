from enum import IntEnum

from statefun import *
import json


class Status(IntEnum):
    RESERVE = 1
    RESERVED = 2
    PAID = 3
    CONFIRMED = 4
    DISPATCHED = 5
    NOSTOCK = 6
    NORESERVATION = 7
    CANCELLED = 8
    FAILED = 9
    REFUNDED = 10

class Book:
    TYPE: type = simple_type(
        typename="com.bookstore.types/book",
        serialize_fn=lambda book : json.dumps(book.__dict__).encode(),
        deserialize_fn=lambda serialized : Book(**json.loads(serialized)))

    def __init__(self, isbn, name, author):
        self.isbn = isbn
        self.name = name
        self.author = author

class Order:
    TYPE: type = simple_type(
        typename="com.bookstore.types/order",
        serialize_fn=lambda order : json.dumps(order.__dict__).encode(),
        deserialize_fn=lambda serialized : Order(**json.loads(serialized)))

    def __init__(self, buyer, isbn, status=Status.RESERVE, value=0.0):
        self.buyer = buyer
        self.isbn = isbn
        self.status = status
        self.value = value


Reservations = []
RESERVATIONS_TYPE = simple_type(
    typename="com.bookstore.types/reservations",
    serialize_fn=lambda reservations : ','.join(reservations).encode(),
    deserialize_fn=lambda serialized : serialized.decode().split(',') if serialized else list())