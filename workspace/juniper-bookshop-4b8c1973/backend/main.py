from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.seed_data import create_db_and_seed_data
from backend.auth import init_session_serializer, generate_secret_key
from backend.routers import auth, products, cart, orders
from backend.dependencies import get_current_user

app = FastAPI(title="Juniper Books")

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="frontend")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])

@app.on_event("startup")
def on_startup():
    create_db_and_seed_data()
    # Initialize session serializer with a random secret key
    session_secret_key = generate_secret_key()
    init_session_serializer(session_secret_key)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # For API requests, return JSON error. For frontend, redirect or render error page.
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    else:
        # For frontend, we might want to redirect to a generic error page or login
        # For now, let's redirect to login if it's a 401, otherwise to root with a message
        if exc.status_code == 401:
            return RedirectResponse(url="/login", status_code=302)
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": exc.detail, "status_code": exc.status_code},
            status_code=exc.status_code
        )

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "user": current_user})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/products/{product_id}", response_class=HTMLResponse)
async def product_detail_page(request: Request, product_id: int):
    return templates.TemplateResponse("product.html", {"request": request, "product_id": product_id})

@app.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request, current_user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("cart.html", {"request": request, "user": current_user})

@app.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request, current_user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("checkout.html", {"request": request, "user": current_user})

@app.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request, current_user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("orders.html", {"request": request, "user": current_user})

@app.get("/error", response_class=HTMLResponse)
async def error_page(request: Request, message: str = "An unexpected error occurred.", status_code: int = 500):
    return templates.TemplateResponse("error.html", {"request": request, "message": message, "status_code": status_code})
