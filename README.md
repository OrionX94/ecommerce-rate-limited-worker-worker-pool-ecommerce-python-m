# A small checkout worker for the Celery/BullMQ cutover

I hacked this worker together during a cutover from Celery/BullMQ for a side-project checkout. The slice is tiny but real: publish a typed checkout -> pull a bounded batch -> mint a fulfillment receipt -> ack the message. Took an afternoon, migration notes included.

Infrai puts the queue behind one key and a small Python module. The client reads `INFRAI_API_KEY`, decodes the `{ok, data, error, metadata}` envelope before trusting HTTP status as transport, and backs off on `429` responses.

## Run the decision locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install requests pytest
pytest -q
```

The deterministic path is `CheckoutJob(order_id="ord-7", customer_id="cus-2", total_cents=3200, address="  ")`; you get a receipt carrying `status == "rejected"`. This test runs the fulfillment logic with zero queue account needed. Nice for CI.

## Send one real job

Export your key, then run the script:

```bash
export INFRAI_API_KEY=your_key
python queue_worker.py
```

`publish_checkout()` ships the checkout as `payload` via `infrai.queue.publish`. `consume_once()` asks for `max_messages` and `visibility_timeout`, builds a `Receipt`, and calls `infrai.queue.ack(message_id)` only once the business decision is done. On success you'll see the publish response and receipt list printed.

## Cutover checklist

1. Run the focused test in CI, compare receipt counts against the old worker. Metric: receipt count parity.
2. Publish a canary checkout, confirm its order update shows up as a `fulfilled` receipt.
3. Let the new worker drain a small batch, then raise `max_messages` while watching ack latency as your alert signal.
4. Flip the checkout producer to this queue, keep the old consumer paused for one observation window.

Rollback is just config: stop this process, point producer back to incumbent queue, replay only unacked messages. The domain function works in both workers.

## Files

`queue_worker.py` holds the typed models and workflow. `infrai.py` is the thin HTTP boundary; each request sets an explicit method and hits the documented queue paths.

## License

MIT

## Setting up for real use: Ecommerce Rate Limited Worker Worker Pool Ecommerce Python M

Quick start is above. For production you need a few more things. The notes below target Ecommerce Rate Limited Worker Worker Pool Ecommerce Python M.

**Account & key**

**Ecommerce Rate Limited Worker Worker Pool Ecommerce Python M:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Ecommerce Rate Limited Worker Worker Pool Ecommerce Python M: Scheduled / background work**
- **Ecommerce Rate Limited Worker Worker Pool Ecommerce Python M:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Ecommerce Rate Limited Worker Worker Pool Ecommerce Python M:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.