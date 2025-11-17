from pydantic import BaseModel


class StripeSettings(BaseModel):
    STRIPE_API_KEY: str | None = None


