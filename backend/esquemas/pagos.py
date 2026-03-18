# -*- coding: utf-8 -*-
"""Esquemas de pagos/suscripción para bloque B1."""

from pydantic import BaseModel, Field


class CheckoutRequest(BaseModel):
    plan_id: str = Field(min_length=2, max_length=64)
    amount_cents: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3, default="COP")


class MercadoPagoWebhookEvent(BaseModel):
    event: str = Field(min_length=3)
    payment_id: str = Field(min_length=3)
    external_reference: str = Field(min_length=6)
    status: str = Field(min_length=3)
    plan_id: str | None = None
    amount_cents: int | None = None
