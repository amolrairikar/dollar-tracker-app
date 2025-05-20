import datetime
from pydantic import BaseModel, field_serializer
from decimal import Decimal


class Transaction(BaseModel):
    """Data model for a transaction record."""
    Date: datetime.date
    Merchant: str
    Amount: Decimal
    Group: str
    Category: str
    Subcategory: str
    Account: str

    @field_serializer('Amount')
    def format_amount(self, amount: Decimal, _info):
        return f'{amount:.2f}'


class NetWorthDetail(BaseModel):
    """Data model for a net worth detail entry."""
    Date: datetime.date
    Account: str
    Category: str
    Subcategory: str
    Balance: Decimal


    @field_serializer('Balance')
    def format_amount(self, amount: Decimal, _info):
        return f'{amount:.2f}'


class NetWorthAggregate(BaseModel):
    """Data model for a net worth aggregate entry."""
    Date: datetime.date
    Category: str
    Balance: Decimal


    @field_serializer('Balance')
    def format_amount(self, amount: Decimal, _info):
        return f'{amount:.2f}'
