"""Checkout-to-fulfillment worker used during the Celery/BullMQ migration."""
from dataclasses import asdict, dataclass
from typing import Any

import infrai


QUEUE_NAME = "checkout-fulfillment"


@dataclass(frozen=True)
class CheckoutJob:
    order_id: str
    customer_id: str
    total_cents: int
    address: str


@dataclass(frozen=True)
class Receipt:
    order_id: str
    customer_id: str
    status: str
    total_cents: int


def fulfill(job: CheckoutJob) -> Receipt:
    """The domain decision: paid checkouts become fulfilled receipts."""
    status = "fulfilled" if job.total_cents > 0 and job.address.strip() else "rejected"
    return Receipt(job.order_id, job.customer_id, status, job.total_cents)


def publish_checkout(job: CheckoutJob) -> dict:
    return infrai.queue.publish(QUEUE_NAME, asdict(job))


def consume_once(max_messages: int = 5, visibility_timeout: int = 60) -> list[Receipt]:
    batch = infrai.queue.consume(QUEUE_NAME, max_messages, visibility_timeout)
    messages = batch.get("messages") or []
    receipts: list[Receipt] = []
    for message in messages:
        payload: Any = message.get("payload") or {}
        job = CheckoutJob(**payload)
        receipt = fulfill(job)
        receipts.append(receipt)
        infrai.queue.ack(QUEUE_NAME, message["message_id"])
    return receipts


if __name__ == "__main__":
    import json
    sample = CheckoutJob("ord_demo", "cus_demo", 2499, "21 Market Street")
    print("published:", json.dumps(publish_checkout(sample)))
    print("receipts:", consume_once())
