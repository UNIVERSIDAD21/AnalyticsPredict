# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field


EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterRequest(BaseModel):
    email: str = Field(pattern=EMAIL_REGEX, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    accepted_legal: bool = Field(default=False)
    legal_version: str = Field(min_length=3, max_length=32)


class LoginRequest(BaseModel):
    email: str = Field(pattern=EMAIL_REGEX, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str = Field(pattern=EMAIL_REGEX, max_length=254)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
