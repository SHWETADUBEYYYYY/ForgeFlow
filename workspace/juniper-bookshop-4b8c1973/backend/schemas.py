from pydantic import BaseModel
from typing import List, Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    author: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True

class CartItemBase(BaseModel):
    product_id: int
    quantity: int

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int

class CartItem(CartItemBase):
    id: int
    user_id: int
    product: Product # Nested product details

    class Config:
        from_attributes = True

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price_at_purchase: float

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    product: Product # Nested product details

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    total_amount: float
    order_date: str

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    user_id: int
    order_items: List[OrderItem]

    class Config:
        from_attributes = True
