from sqlalchemy import Column, Integer, String, TIMESTAMP, DECIMAL, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from backend.database import engine

Base = declarative_base()

# Retailer Table
class Retailer(Base):
    __tablename__ = "retailers"

    retailer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    location = Column(String(100))
    last_login = Column(TIMESTAMP)

# Product Table
class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    category = Column(String(50))
    brand = Column(String(50))
    price = Column(DECIMAL)
    product_metadata = Column(JSON)  # ← renamed from 'metadata'


# Interaction Table
class Interaction(Base):
    __tablename__ = "interactions"

    interaction_id = Column(Integer, primary_key=True, index=True)
    retailer_id = Column(Integer, ForeignKey("retailers.retailer_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    action_type = Column(String(50))  # e.g., 'view', 'search', 'add_to_cart'
    timestamp = Column(TIMESTAMP)

# Create tables in the database
Base.metadata.create_all(bind=engine)
