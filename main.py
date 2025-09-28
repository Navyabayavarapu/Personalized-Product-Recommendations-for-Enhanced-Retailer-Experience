from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import SessionLocal, engine
from backend.models import Base, Retailer, Product, Interaction
from pydantic import BaseModel
from datetime import datetime
from backend.ml_model import get_ml_recommendations
import redis
import json
import logging

# Initialize app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Redis client
r = redis.Redis(host='localhost', port=6379, db=0)

# Logging
logging.basicConfig(level=logging.INFO)

# DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------
# Retailer Endpoint
# -------------------------------
class RetailerCreate(BaseModel):
    name: str
    location: str
    last_login: datetime

@app.post("/retailers/")
async def create_retailer(retailer: RetailerCreate, db: Session = Depends(get_db)):
    new_retailer = Retailer(**retailer.dict())
    db.add(new_retailer)
    db.commit()
    db.refresh(new_retailer)
    return new_retailer

# -------------------------------
# Product Endpoint
# -------------------------------
class ProductCreate(BaseModel):
    name: str
    category: str
    brand: str
    price: float
    product_metadata: dict

@app.post("/products/")
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

# -------------------------------
# Interaction Endpoint
# -------------------------------
class InteractionCreate(BaseModel):
    retailer_id: int
    product_id: int
    action_type: str
    timestamp: datetime

@app.post("/interactions/")
async def create_interaction(interaction: InteractionCreate, db: Session = Depends(get_db)):
    new_interaction = Interaction(**interaction.dict())
    db.add(new_interaction)
    db.commit()
    db.refresh(new_interaction)
    return new_interaction

# -------------------------------
# Rule-Based Recommendations
# -------------------------------
@app.get("/recommendations/{retailer_id}")
async def get_recommendations(
    retailer_id: int,
    limit: int = 5,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    cache_key = f"recommendations:{retailer_id}:{limit}:{offset}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    results = (
        db.query(
            Product.product_id,
            Product.name,
            Product.brand,
            Product.category,
            func.count(Interaction.interaction_id).label("view_count")
        )
        .join(Interaction, Product.product_id == Interaction.product_id)
        .filter(Interaction.retailer_id == retailer_id)
        .filter(Interaction.action_type == "view")
        .group_by(Product.product_id, Product.name, Product.brand, Product.category)
        .order_by(func.count(Interaction.interaction_id).desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    recommendations = [
        {
            "product_id": r.product_id,
            "name": r.name,
            "brand": r.brand,
            "category": r.category,
            "view_count": r.view_count
        }
        for r in results
    ]

    response = {"retailer_id": retailer_id, "recommendations": recommendations}
    r.setex(cache_key, 300, json.dumps(response))
    return response

# -------------------------------
# ML-Based Recommendations
# -------------------------------
@app.get("/ml_recommendations/{retailer_id}")
async def ml_recommendations(retailer_id: int, db: Session = Depends(get_db)):
    logging.info(f"Fetching ML recommendations for retailer {retailer_id}")

    cache_key = f"ml_recommendations:{retailer_id}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    data = db.query(Interaction.retailer_id, Interaction.product_id).filter(Interaction.action_type == "view").all()
    interaction_data = [{"retailer_id": r.retailer_id, "product_id": r.product_id} for r in data]

    recommended_product_ids = get_ml_recommendations(retailer_id, interaction_data)

    if not recommended_product_ids:
        return {
            "retailer_id": retailer_id,
            "ml_recommendations": [],
            "message": "No recommendations available yet. Try interacting with more products!"
        }

    products = db.query(Product).filter(Product.product_id.in_(recommended_product_ids)).all()

    detailed_recommendations = [
        {
            "product_id": p.product_id,
            "name": p.name,
            "brand": p.brand,
            "category": p.category,
            "price": float(p.price),
            "metadata": p.product_metadata
        }
        for p in products
    ]

    response = {
        "retailer_id": retailer_id,
        "ml_recommendations": detailed_recommendations
    }

    r.setex(cache_key, 300, json.dumps(response))
    return response

# -------------------------------
# Export Interactions
# -------------------------------
@app.get("/interactions/export")
async def export_interactions(db: Session = Depends(get_db)):
    data = db.query(Interaction.retailer_id, Interaction.product_id).filter(Interaction.action_type == "view").all()
    return [{"retailer_id": r.retailer_id, "product_id": r.product_id} for r in data]

# -------------------------------
# Root Endpoint
# -------------------------------
@app.get("/")
def read_root():
    return {"message": "Welcome to QwipoBuddy!"}
