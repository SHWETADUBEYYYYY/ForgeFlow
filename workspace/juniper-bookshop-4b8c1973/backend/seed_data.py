from sqlalchemy.orm import Session
from backend import models, crud
from backend.database import engine, SessionLocal

def seed_products(db: Session):
    """Seeds the database with initial product data if the products table is empty."""
    if db.query(models.Product).count() == 0:
        print("Seeding products...")
        products_data = [
            {
                "name": "The Midnight Library",
                "author": "Matt Haig",
                "price": 14.99,
                "description": "Between life and death there is a library, and within that library, the possibility to try out every life you could have lived.",
                "image_url": "/static/images/midnight_library.jpg"
            },
            {
                "name": "Project Hail Mary",
                "author": "Andy Weir",
                "price": 16.50,
                "description": "Ryland Grace is the sole survivor on a desperate, last-chance mission to save humanity.",
                "image_url": "/static/images/project_hail_mary.jpg"
            },
            {
                "name": "Where the Crawdads Sing",
                "author": "Delia Owens",
                "price": 13.75,
                "description": "A wild young woman living in the marshes of North Carolina becomes a suspect in a murder.",
                "image_url": "/static/images/crawdads_sing.jpg"
            },
            {
                "name": "Atomic Habits",
                "author": "James Clear",
                "price": 12.00,
                "description": "An easy & proven way to build good habits & break bad ones.",
                "image_url": "/static/images/atomic_habits.jpg"
            },
            {
                "name": "Dune",
                "author": "Frank Herbert",
                "price": 15.25,
                "description": "Set in the distant future amidst a feudal interstellar society where various noble houses control planetary fiefs.",
                "image_url": "/static/images/dune.jpg"
            }
        ]

        for product_data in products_data:
            crud.create_product(db, schemas.ProductCreate(**product_data))
        db.commit()
        print(f"Seeded {len(products_data)} products.")
    else:
        print("Products already exist, skipping seeding.")

def create_db_and_seed_data():
    """Creates all database tables and seeds initial data."""
    print("Creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_products(db)
    finally:
        db.close()
    print("Database tables created and seeded.")

if __name__ == "__main__":
    create_db_and_seed_data()
