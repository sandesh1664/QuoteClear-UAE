from datetime import date
from decimal import Decimal
from typing import Literal, Self
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)

class Register(Strict):
    name: str=Field(min_length=1,max_length=120)
    email: str=Field(min_length=3,max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password: str=Field(min_length=10,max_length=128)
class Login(Strict):
    email: str=Field(max_length=254)
    password: str=Field(max_length=128)

Category=Literal['AC & maintenance','Car repair','Moving','Cleaning','IT services','Other']
Emirate=Literal['Dubai','Abu Dhabi','Sharjah','Ajman','Ras Al Khaimah','Fujairah','Umm Al Quwain']
class JobIn(Strict):
    title: str=Field(min_length=1,max_length=160)
    category: Category
    emirate: Emirate
    description: str=Field(default='',max_length=3000)
    status: Literal['Comparing','Selected','Completed','Archived']='Comparing'

class ItemIn(Strict):
    label: str=Field(min_length=1,max_length=200)
    kind: Literal['Labour','Parts','Call-out','Transport','Other']='Other'
    pricing: Literal['fixed','included','unknown']='fixed'
    amount: Decimal|None=Field(default=None,ge=0,le=10000000,decimal_places=2)
    quantity: int=Field(default=1,ge=1,le=1000)
    reviewed: bool=False
    source_page: int|None=Field(default=None,ge=1,le=40)
    source_excerpt: str=Field(default='',max_length=1000)
    @model_validator(mode='after')
    def price_consistency(self)->Self:
        if self.pricing=='fixed' and self.amount is None: raise ValueError('Enter an amount for a fixed-price item')
        if self.pricing!='fixed' and self.amount not in (None,Decimal(0)): raise ValueError('Included or unknown items cannot carry a charge')
        if self.pricing=='unknown': self.amount=None
        if self.pricing=='included': self.amount=Decimal(0)
        return self

class QuoteIn(Strict):
    provider: str=Field(min_length=1,max_length=160)
    reference: str=Field(default='',max_length=100)
    document_id: str|None=None
    tax_mode: Literal['included','excluded','unspecified']='unspecified'
    tax_rate: Decimal=Field(default=Decimal(0),ge=0,le=100,decimal_places=2)
    warranty_days: int|None=Field(default=None,ge=0,le=36500)
    completion_days: int|None=Field(default=None,ge=0,le=3650)
    valid_until: date|None=None
    exclusions: str=Field(default='',max_length=3000)
    notes: str=Field(default='',max_length=3000)
    items: list[ItemIn]=Field(min_length=1,max_length=100)

class ExpenseIn(Strict):
    label: str=Field(min_length=1,max_length=180)
    amount: Decimal=Field(gt=0,le=10000000,decimal_places=2)
    paid_on: date
    note: str=Field(default='',max_length=2000)

class Selection(Strict):
    quote_id: str|None=None
