from sqlalchemy.orm import Session
from backend import models, schemas
from backend.auth import hash_password

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hash_password(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_cart_item(db: Session, user_id: int, product_id: int):
    return db.query(models.CartItem).filter(
        models.CartItem.user_id == user_id,
        models.CartItem.product_id == product_id
    ).first()

def get_cart_items_by_user(db: Session, user_id: int):
    return db.query(models.CartItem).filter(models.CartItem.user_id == user_id).all()

def add_item_to_cart(db: Session, user_id: int, product_id: int, quantity: int = 1):
    db_cart_item = get_cart_item(db, user_id, product_id)
    if db_cart_item:
        db_cart_item.quantity += quantity
    else:
        db_cart_item = models.CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.add(db_cart_item)
    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item

def update_cart_item_quantity(db: Session, cart_item_id: int, quantity: int):
    db_cart_item = db.query(models.CartItem).filter(models.CartItem.id == cart_item_id).first()
    if db_cart_item:
        db_cart_item.quantity = quantity
        db.commit()
        db.refresh(db_cart_item)
    return db_cart_item

def remove_item_from_cart(db: Session, cart_item_id: int):
    db_cart_item = db.query(models.CartItem).filter(models.CartItem.id == cart_item_id).first()
    if db_cart_item:
        db.delete(db_cart_item)
        db.commit()
    return db_cart_item

def create_order(db: Session, user_id: int, total_amount: float, order_date: str, cart_items: list[schemas.CartItem]):
    db_order = models.Order(user_id=user_id, total_amount=total_amount, order_date=order_date)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    for item in cart_items:
        db_order_item = models.OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=item.product.price # Assuming product details are loaded
        )
        db.add(db_order_item)
    db.commit()

    # Clear the cart after order creation
    db.query(models.CartItem).filter(models.CartItem.user_id == user_id).delete()
    db.commit()

    db.refresh(db_order)
    return db_order

def get_orders_by_user(db: Session, user_id: int):
    return db.query(models.Order).filter(models.Order.user_id == user_id).all()
