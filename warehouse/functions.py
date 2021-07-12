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
from datetime import timedelta

import asyncio

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from inventory import Inventory
from models import *
import serve


@serve.functions.bind(
    typename="com.warehouse.fn/order", 
    specs=[
        ValueSpec(name='reservations', type=RESERVATIONS_TYPE, expire_after_write=timedelta(seconds=5)),
        ValueSpec(name='instock', type=IntType, expire_after_write=timedelta(seconds=60))
        ])
async def process_order(context: Context, message: Message):
    # take the order
    # reserve the book for 5 sec
    # confirm reservation once payment is done
    order = message.as_type(Order.TYPE)

    print(f"Received an order for {context.address.id} in state '{Status(order.status).name}'", flush=True)

    reservations = context.storage.reservations or list()
    
    inventory = Inventory("stock.csv")
    if not context.storage.instock:
        context.storage.instock = inventory.get_stock(order.isbn)

    print(f'in stock {context.storage.instock}', flush=True)

    if order.status == Status.RESERVE:
        order.status = Status.NOSTOCK
        if context.storage.instock > len(reservations):
            if order.buyer not in reservations:
                reservations.append(order.buyer)
            order.status = Status.RESERVED
            order.value = inventory.get_value(order.isbn)
    elif order.status == Status.PAID:
        order.status = Status.NORESERVATION
        if order.buyer in reservations:
            reservations.remove(order.buyer)
            context.storage.instock = inventory.mark_sold(order.isbn)
            order.status = Status.CONFIRMED
    else:
        order.status = Status.FAILED

    context.storage.reservations = reservations
    print(f'current reservations for {context.address.id}: {context.storage.reservations}', flush=True)
    print(f"order for {context.address.id} is moved to state '{Status(order.status).name}'", flush=True)

    # update the order status
    context.send(
        message_builder(target_typename="com.store.fn/order-updates",
                        target_id=context.address.id,
                        value=order,
                        value_type=Order.TYPE))

    # stock up books
    if context.storage.instock < 1:
        context.send(
            message_builder(
                target_typename="com.warehouse.fn/replenish",
                target_id=context.address.id,
                str_value=order.isbn))


@serve.functions.bind(typename="com.warehouse.fn/replenish")
async def stock_up(context: Context, message: Message):
    isbn = message.as_string()
    
    # stock up the book
    inventory = Inventory("stock.csv")
    inventory.add_stock(isbn, 10)
    print(f'{isbn} is stocked up now')


@serve.functions.bind(typename="com.warehouse.fn/dispatch")
async def dispatch_order(context: Context, message: Message):
    order = message.as_type(Order.TYPE)
    order.status = Status.DISPATCHED

    # lets take sometime to dispatch
    await asyncio.sleep(1)

    context.send(
        message_builder(target_typename="com.store.fn/order-updates",
                        target_id=context.address.id,
                        value=order,
                        value_type=Order.TYPE))


if __name__ == '__main__':
    serve.run()
