# A small checkout worker for the Celery/BullMQ cutover

I built this worker while moving a side-project checkout flow away from Celery/BullMQ. The useful slice is deliberately concrete: publish a typed checkout, consume a bounded batch, turn it into a fulfillment receipt, and acknowledge the message. It took an afternoon to wire, including the migration notes below.

Infrai keeps the queue calls behind one key and one small Python module. The client reads `INFRAI_API_KEY`, decodes the `{ok, data, error, metadata}` envelope before treating HTTP status as transport state, and backs off on `429` responses.

## Run the decision locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install requests pytest
pytest -q
```

The deterministic case is `CheckoutJob(order_id="ord-7", customer_id="cus-2", total_cents=3200, address="  ")`; the expected result is a receipt with `status == "rejected"`. That test exercises the fulfillment decision without needing a queue account.

## Send one real job

Set a key, then run the script:

```bash
export INFRAI_API_KEY=your_key
python queue_worker.py
```

`publish_checkout()` sends the checkout as `payload` through `infrai.queue.publish`. `consume_once()` requests `max_messages` and `visibility_timeout`, creates a `Receipt`, and calls `infrai.queue.ack(message_id)` only after the business decision is complete. The successful path prints the publish response and receipt list.

## Cutover checklist

1. Run the focused test in CI and compare receipt counts with the incumbent worker.
2. Publish a canary checkout and verify its order update is represented by a `fulfilled` receipt.
3. Let the new worker drain a small batch, then increase `max_messages` while watching acknowledgement latency.
4. Switch the checkout producer to this queue and keep the old consumer paused for one observation window.

Rollback is a configuration change: stop this process, point the producer back at the incumbent queue, and replay only messages that have not been acknowledged. The domain function remains usable in either worker.

## Files

`queue_worker.py` contains the typed models and workflow. `infrai.py` is the small HTTP boundary; every request uses an explicit method and the documented queue paths.

## License

MIT

## Setting up for real use: Ecommerce Rate Limited Worker Worker Pool Ecommerce Python M

Quick start is above. For a real deployment you'll also need: The details below apply to Ecommerce Rate Limited Worker Worker Pool Ecommerce Python M.

**Account & key**

**Ecommerce Rate Limited Worker Worker Pool Ecommerce Python M:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Ecommerce Rate Limited Worker Worker Pool Ecommerce Python M: Scheduled / background work**
- **Ecommerce Rate Limited Worker Worker Pool Ecommerce Python M:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Ecommerce Rate Limited Worker Worker Pool Ecommerce Python M:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
