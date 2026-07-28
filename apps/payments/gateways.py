"""
Payment gateway abstraction.

Design
-----
`PaymentGateway` is an abstract interface (ABC) with a single `charge` method.
Concrete gateways (FakeGateway, StripeGateway, ZarinpalGateway) implement it.
The app resolves which gateway to use via `get_gateway()`, driven by a setting
so production can switch to Stripe with one env var and no refactor.

This is the Strategy pattern: the payments service depends on the abstraction,
not a concrete gateway, so adding a new gateway is purely additive.

Why not call the gateway from inside the order service?
-------------------------------------------------------
Separation of concerns: orders own order state; payments own money movement.
The order service creates the order (PENDING); the payment service charges;
on success it calls back into the order service to flip the order to PAID.
"""

from __future__ import annotations

import abc
import secrets
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings


@dataclass
class GatewayResult:
    success: bool
    transaction_id: str
    failure_reason: str = ""


class PaymentGateway(abc.ABC):
    """Abstract gateway interface every concrete gateway implements."""

    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @abc.abstractmethod
    def charge(self, *, amount: Decimal, currency: str, reference: str) -> GatewayResult: ...

    @abc.abstractmethod
    def refund(self, *, transaction_id: str, amount: Decimal) -> GatewayResult: ...


class FakeGateway(PaymentGateway):
    """A deterministic test gateway.

    Succeeds by default. Fails when the amount is non-positive or when the
    reference contains the literal "fail" — useful for testing failure paths
    without hitting a real processor.
    """

    name = "fake"

    def charge(self, *, amount: Decimal, currency: str, reference: str) -> GatewayResult:
        if amount <= 0:
            return GatewayResult(False, "", "Amount must be positive.")
        if "fail" in reference.lower():
            return GatewayResult(False, "", "Simulated failure (reference contains 'fail').")
        tx_id = f"FAKE-{secrets.token_hex(8).upper()}"
        return GatewayResult(True, tx_id)

    def refund(self, *, transaction_id: str, amount: Decimal) -> GatewayResult:
        if not transaction_id.startswith("FAKE-"):
            return GatewayResult(False, "", "Unknown transaction id.")
        return GatewayResult(True, f"{transaction_id}-REFUND")


_GATEWAYS: dict[str, PaymentGateway] = {}


def register_gateway(gateway: PaymentGateway) -> None:
    _GATEWAYS[gateway.name] = gateway


register_gateway(FakeGateway())


def get_gateway(name: str | None = None) -> PaymentGateway:
    """Resolve the gateway. Defaults to settings.PAYMENT_GATEWAY or 'fake'."""
    key = name or getattr(settings, "PAYMENT_GATEWAY", "fake")
    if key not in _GATEWAYS:
        raise ValueError(f"Payment gateway '{key}' is not registered.")
    return _GATEWAYS[key]
