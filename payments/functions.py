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
import json
import asyncio

from statefun import *

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from models import Payment, PaymentStatus
import serve


# Uses buyer as target id
@serve.functions.bind(typename="com.payments.fn/process", specs=[ValueSpec(name='last_transaction', type=FloatType)])
async def process_payment(context: Context, message: Message):
    payment_request = message.as_type(Payment)

    last_transacted_amount = context.storage.last_transaction or 0.0

    if payment_request['status'] == PaymentStatus.DEBIT:
        context.storage.last_transaction = payment_request['value']
        print(f"amount {payment_request['value']} debited from user {context.address.id}'s account", flush=True)
        # lets take random amount of time to process the payment
        # cases like 5, 6 etc., are intentionally there to simulate timeouts
        await asyncio.sleep(random.choice([0.5, 0.75, 1, 2, 5, 6]))
        payment_request['status'] = PaymentStatus.DEBITED
    elif payment_request['status'] == PaymentStatus.REFUND:
        print(f"amount {last_transacted_amount} refunded to user {context.address.id}'s account", flush=True)
        del context.storage.last_transaction
        payment_request['status'] = PaymentStatus.REFUNDED
    elif payment_request['status'] == PaymentStatus.CREDIT:
        print(f"amount {payment_request['value']} credited to user {context.address.id}'s account", flush=True)
        payment_request['status'] = PaymentStatus.CREDITED

    # send out the update
    context.send_egress(
        kafka_egress_message(
            typename="com.bookstore.ingress/orders",
            topic="payment-updates",
            key=payment_request['id'],
            value=json.dumps(payment_request).encode()))


if __name__ == '__main__':
    serve.run()
