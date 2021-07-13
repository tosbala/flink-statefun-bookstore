from enum import IntEnum

import statefun
import json


class OrderStatus(IntEnum):
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

# custom class as Types
class Book:
    TYPE: statefun.Type = statefun.simple_type(
        typename="com.bookstore.types/Book",
        serialize_fn=lambda book : json.dumps(book.__dict__).encode(),
        deserialize_fn=lambda serialized : Book(**json.loads(serialized)))

    def __init__(self, isbn, name, author):
        self.isbn = isbn
        self.name = name
        self.author = author

class Order:
    TYPE: statefun.Type = statefun.simple_type(
        typename="com.bookstore.types/Order",
        serialize_fn=lambda order : json.dumps(order.__dict__).encode(),
        deserialize_fn=lambda serialized : Order(**json.loads(serialized)))

    def __init__(self, buyer, isbn, status=OrderStatus.RESERVE, value=0.0):
        self.buyer = buyer
        self.isbn = isbn
        self.status = status
        self.value = value

# list as type
Reservations = []
RESERVATIONS_TYPE: statefun.Type = statefun.simple_type(
    typename="com.bookstore.types/Reservation",
    serialize_fn=lambda reservations : ','.join(reservations).encode(),
    deserialize_fn=lambda serialized : serialized.decode().split(',') if serialized else list())

# JSON as type
Payment: statefun.Type = statefun.make_json_type('com.bookstore.types/Payment') # {'id': isbn, 'user': buyer, 'value': order_value, 'status': PaymentStatus}

class PaymentStatus(IntEnum):
    DEBIT = 0
    DEBITED = 1
    CREDIT = 2
    CREDITED = 3
    REFUND = 4
    REFUNDED = 5