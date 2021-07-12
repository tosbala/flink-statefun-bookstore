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
import random

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import asyncio

import serve
from models import *


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


@serve.functions.bind(typename="com.store.fn/order-updates")
async def order_updates(context: Context, message: Message):
    order = message.as_type(Order.TYPE)

    print(f"order update '{Status(order.status).name}'", flush=True)

    order_update = f'{order.buyer}, sorry we couldnt process your order'
    if order.status == Status.RESERVE:
        order_update = f'{order.buyer}, Thank You. Your order for book {order.isbn} is being processed'
    elif order.status in [Status.RESERVED, Status.NORESERVATION]:
        order_update = f'{order.buyer}, your order for book {order.isbn} is awaiting payment confirmation'
        if order.status == Status.NORESERVATION:
            order_update = f'{order.buyer}, couldnt process your order for book {order.isbn}. Amount will be refunded'

        context.send(
        message_builder(target_typename="com.store.fn/reserved",
                        target_id=order.buyer,
                        value=order,
                        value_type=Order.TYPE))
    elif order.status == Status.CONFIRMED:
        order_update = f'{order.buyer}, your order for book {order.isbn} is confirmed now'
        context.send(
            message_builder(
                target_typename="com.warehouse.fn/dispatch",
                target_id=context.address.id,
                value=order,
                value_type=Order.TYPE))
    elif order.status == Status.NOSTOCK:
        order_update = f'{order.buyer}, book {order.isbn} you requested is out of stock now, please try again later'
    elif order.status == Status.DISPATCHED:
        order_update = f'{order.buyer}, book {order.isbn} is dispatched now'
    elif order.status == Status.REFUNDED:
        order_update = f'{order.buyer}, amound paid for {order.isbn} is refunded now'

    # send out the order status message
    context.send_egress(
        kafka_egress_message(
            typename="com.bookstore/coms",
            topic="status",
            key=order.isbn,
            value=order_update))


@serve.functions.bind(typename="com.store.fn/reserved", specs=[ValueSpec(name='last_transaction', type=FloatType)])
async def process_payment(context: Context, message: Message):
    order = message.as_type(Order.TYPE)

    last_transacted_amount = context.storage.last_transaction or 0.0

    if order.status == Status.RESERVED:
        order.status = Status.PAID

        context.storage.last_transaction = order.value

        # lets take random amount of time to process the payment
        # cases like 5, 6 etc., are intentionally there to simulate timeouts
        await asyncio.sleep(random.choice([0.5, 0.75, 1, 2, 5, 6]))

        context.send(
                message_builder(target_typename="com.warehouse.fn/order",
                                target_id=order.isbn,
                                value=order,
                                value_type=Order.TYPE))
    elif order.status == Status.NORESERVATION and last_transacted_amount > 0.0:
        print(f"amount {order.value} deducted for {order.isbn} is refunded now", flush=True)
        del context.storage.last_transaction

        order.status = Status.REFUNDED

        context.send(
        message_builder(target_typename="com.store.fn/order-updates",
                        target_id=order.isbn,
                        value=order,
                        value_type=Order.TYPE))


if __name__ == '__main__':
    serve.run()
