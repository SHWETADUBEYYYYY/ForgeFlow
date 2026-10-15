from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend import crud, schemas
from backend.dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/checkout", response_model=schemas.Order)
async def checkout_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cart_items = crud.get_cart_items_by_user(db, user_id=current_user["id"])
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")
    
    order = crud.create_order_from_cart(db, user_id=current_user["id"], cart_items=cart_items)
    crud.clear_user_cart(db, user_id=current_user["id"])
    return order

@router.get("/", response_model=List[schemas.Order])
async def get_user_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return crud.get_orders_by_user(db, user_id=current_user["id"])

@router.get("/{order_id}", response_model=schemas.Order)
async def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = crud.get_order_by_id(db, order_id=order_id)
    if not order or order.user_id != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or not authorized")
    return order
