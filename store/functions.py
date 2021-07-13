################################################################################
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
# limitations under the License.
################################################################################
import os
import sys

from statefun import *

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import serve
from models import *


# uses isbn as target id
@serve.functions.bind(typename="com.store.fn/order")
async def order_book(context: Context, message: Message):
    # take the order
    order = message.as_type(Order.TYPE)

    # update the order status
    context.send(
        message_builder(target_typename="com.store.fn/order-updates",
                        target_id=context.address.id,
                        value=order,
                        value_type=Order.TYPE))


# uses isbn as target id
@serve.functions.bind(typename="com.store.fn/order-updates")
async def order_updates(context: Context, message: Message):
    order_update = ''
    payment_request = dict()
    warehouse_request = ''

    if message.is_type(Order.TYPE):
        order = message.as_type(Order.TYPE)

        # print(f"order update '{OrderStatus(order.status).name.upper()}'", flush=True)

        order_update = f'{order.buyer}, sorry we couldnt process your order'
        if order.status == OrderStatus.RESERVE:
            order_update = f'{order.buyer}, Thank You. Your order for book {order.isbn} is being processed'
        elif order.status == OrderStatus.RESERVED:
            order_update = f'{order.buyer}, your order for book {order.isbn} is awaiting payment confirmation'
            # create a payment request
            payment_request = {'id': order.isbn, 'user': order.buyer, 'value': order.value, 'status': PaymentStatus.DEBIT}
        elif order.status == OrderStatus.NORESERVATION:
                order_update = f'{order.buyer}, couldnt process your order for book {order.isbn}. Amount will be refunded'
                # create a refund request
                payment_request = {'id': order.isbn, 'user': order.buyer, 'value': order.value, 'status': PaymentStatus.REFUND}
        elif order.status == OrderStatus.CONFIRMED:
            order_update = f'{order.buyer}, your order for book {order.isbn} is confirmed now'
        elif order.status == OrderStatus.NOSTOCK:
            order_update = f'{order.buyer}, book {order.isbn} you requested is out of stock now, please try again later'
        elif order.status == OrderStatus.DISPATCHED:
            order_update = f'{order.buyer}, book {order.isbn} is dispatched now'
    elif message.is_type(Payment):
        payment = message.as_type(Payment)
        if payment['status'] == PaymentStatus.DEBITED:
            order_update = f"{payment['user']}, payment for book {payment['id']} is confirmed now"
            # make a warehouse request to process the reservation
            order = Order(buyer=payment['user'], isbn=context.address.id, status=OrderStatus.PAID, value=payment['value'])
            warehouse_request = 'com.warehouse.fn/order'
        if payment['status'] == PaymentStatus.REFUNDED:
            order_update = f"{payment['user']}, amound {payment['value']} paid for {payment['id']} is refunded now"

    if payment_request:
        # send out a payment request
        context.send_egress(
            kafka_egress_message(
                typename="com.payments/orders",
                topic="payments",
                key=order.buyer,
                value=payment_request,
                value_type=Payment))

    if warehouse_request:
        # make a warehouse request
        context.send(
            message_builder(
                target_typename=warehouse_request,
                target_id=context.address.id,
                value=order,
                value_type=Order.TYPE))

    if order_update:
        # send out the order status message
        context.send_egress(
            kafka_egress_message(
                typename="com.bookstore/coms",
                topic="status",
                key=context.address.id,
                value=order_update))


if __name__ == '__main__':
    serve.run()
