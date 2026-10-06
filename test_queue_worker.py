from queue_worker import CheckoutJob, fulfill


def test_empty_address_rejects_checkout_before_fulfillment():
    receipt = fulfill(CheckoutJob("ord-7", "cus-2", 3200, "  "))
    assert receipt.status == "rejected"
    assert receipt.order_id == "ord-7"

