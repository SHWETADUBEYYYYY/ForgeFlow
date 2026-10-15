from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend import crud, schemas
from backend.dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/add", response_model=schemas.CartItem)
async def add_item_to_cart(
    item: schemas.CartItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_cart_item = crud.get_cart_item_by_user_and_product(db, user_id=current_user["id"], product_id=item.product_id)
    if db_cart_item:
        # If item already in cart, update quantity
        return crud.update_cart_item_quantity(db, cart_item_id=db_cart_item.id, quantity=db_cart_item.quantity + item.quantity)
    else:
        return crud.create_cart_item(db, item, user_id=current_user["id"])

@router.get("/", response_model=List[schemas.CartItem])
async def get_user_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return crud.get_cart_items_by_user(db, user_id=current_user["id"])

@router.put("/{cart_item_id}", response_model=schemas.CartItem)
async def update_cart_item(
    cart_item_id: int,
    item_update: schemas.CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_cart_item = crud.get_cart_item(db, cart_item_id=cart_item_id)
    if not db_cart_item or db_cart_item.user_id != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found or not authorized")
    if item_update.quantity <= 0:
        crud.delete_cart_item(db, cart_item_id=cart_item_id)
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="Item removed from cart") # Indicate removal
    return crud.update_cart_item_quantity(db, cart_item_id=cart_item_id, quantity=item_update.quantity)

@router.delete("/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cart_item(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_cart_item = crud.get_cart_item(db, cart_item_id=cart_item_id)
    if not db_cart_item or db_cart_item.user_id != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found or not authorized")
    crud.delete_cart_item(db, cart_item_id=cart_item_id)
    return {"message": "Item removed from cart"}
