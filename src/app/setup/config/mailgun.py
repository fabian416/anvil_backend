from pydantic import BaseModel, Field


class MailgunSettings(BaseModel):
    domain: str = Field(alias="DOMAIN")
    api_key: str = Field(alias="API_KEY")


