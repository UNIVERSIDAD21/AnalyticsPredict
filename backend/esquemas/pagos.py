# -*- coding: utf-8 -*-
"""Esquemas de pagos/suscripción para bloque C1."""

from pydantic import BaseModel, Field


class CheckoutRequest(BaseModel):
    plan_id: str = Field(min_length=2, max_length=64)
    amount_cents: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3, default="COP")
