from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import hashlib
import secrets
import asyncio
import os


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Get allowed origins from environment
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "supersecretkey")
JWT_ALGORITHM = "HS256"
JWT_EXP_HOURS = 24

security = HTTPBearer()
def create_jwt_token(data: dict):
    expire = datetime.utcnow() + timedelta(hours=JWT_EXP_HOURS)
    payload = data.copy()
    payload.update({"exp": expire})
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
JWT_EXPIRATION_HOURS = 24
    
# Enhanced Models
class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    original_price: Optional[float] = None
    category: str
    subcategory: str
    brand: str
    image_url: str
    gallery_images: List[str] = []
    rating: float
    review_count: int
    in_stock: bool
    stock_quantity: int
    specifications: dict
    features: List[str]
    tags: List[str]
    is_restricted: bool = False
    weight: Optional[str] = None
    dimensions: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    original_price: Optional[float] = None
    category: str
    subcategory: str
    brand: str
    image_url: str
    gallery_images: List[str] = []
    rating: float = 4.5
    review_count: int = 0
    in_stock: bool = True
    stock_quantity: int = 100
    specifications: dict = {}
    features: List[str] = []
    tags: List[str] = []
    is_restricted: bool = False
    weight: Optional[str] = None
    dimensions: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    in_stock: Optional[bool] = None
    stock_quantity: Optional[int] = None
    specifications: Optional[dict] = None
    features: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_restricted: Optional[bool] = None
    weight: Optional[str] = None
    dimensions: Optional[str] = None

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    description: str
    image_url: str
    product_count: int = 0

class CategoryWithCount(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    image_url: str
    product_count: int

class Brand(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    logo_url: str
    description: str
    website: Optional[str] = None

class BrandWithCount(BaseModel):
    id: str
    name: str
    logo_url: str
    description: str
    website: Optional[str] = None
    product_count: int

# User Authentication Models (separate from dealers)
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = "United States"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = "United States"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None

# Dealer Authentication Models (existing)
class Dealer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    company_name: str
    contact_name: str
    phone: str
    address: str
    license_number: str
    is_approved: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DealerCreate(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    contact_name: str
    phone: str
    address: str
    license_number: str

class DealerLogin(BaseModel):
    email: EmailStr
    password: str

class DealerResponse(BaseModel):
    id: str
    email: EmailStr
    company_name: str
    contact_name: str
    phone: str
    address: str
    license_number: str
    is_approved: bool
    is_active: bool

# Quote System Models
class QuoteItem(BaseModel):
    product_id: str
    quantity: int
    price: float
    notes: Optional[str] = None

class Quote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[QuoteItem]
    total_amount: float
    
    # Additional quote information
    project_name: str
    intended_use: str
    delivery_date: Optional[datetime] = None
    delivery_address: str
    billing_address: str
    company_size: Optional[str] = None
    budget_range: Optional[str] = None
    additional_requirements: Optional[str] = None
    
    status: str = "pending"  # pending, reviewed, approved, declined
    admin_notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QuoteCreate(BaseModel):
    user_id: str
    items: List[QuoteItem]
    project_name: str
    intended_use: str
    delivery_date: Optional[datetime] = None
    delivery_address: str
    billing_address: str
    company_size: Optional[str] = None
    budget_range: Optional[str] = None
    additional_requirements: Optional[str] = None

class QuoteResponse(BaseModel):
    id: str
    user_name: str
    user_email: str
    company_name: Optional[str]
    items: List[QuoteItem]
    total_amount: float = 0.0
    project_name: str
    intended_use: str
    delivery_date: Optional[datetime]
    delivery_address: str
    billing_address: str
    company_size: Optional[str]
    budget_range: Optional[str]
    additional_requirements: Optional[str]
    status: str
    admin_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

# Admin Authentication Models
class Admin(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    is_super_admin: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    is_super_admin: bool

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Admin:
    token_data = verify_jwt_token(credentials.credentials)
    if not token_data or token_data["user_type"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin token"
        )
    
    admin = await db.admins.find_one({"id": token_data["user_id"], "is_active": True})
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found or inactive"
        )
    
    return Admin(**admin)
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    sender_type: str  # "user" or "admin"
    sender_name: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessageCreate(BaseModel):
    user_id: str
    sender_type: str
    sender_name: str
    message: str

# Shopping Cart Models (enhanced for users)
class CartItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class Cart(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[CartItem] = []
    total: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AddToCartRequest(BaseModel):
    product_id: str
    quantity: int = 1

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_jwt_token(user_id: str, user_type: str = "user") -> str:
    payload = {
        "user_id": user_id,
        "user_type": user_type,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "user_id": payload.get("user_id"),
            "user_type": payload.get("user_type", "user")
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token_data = verify_jwt_token(credentials.credentials)
    if not token_data or token_data["user_type"] != "user":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user = await db.users.find_one({"id": token_data["user_id"], "is_active": True})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return User(**user)

async def get_current_dealer(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dealer:
    token_data = verify_jwt_token(credentials.credentials)
    if not token_data or token_data["user_type"] != "dealer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    dealer = await db.dealers.find_one({"id": token_data["user_id"], "is_active": True})
    if not dealer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Dealer not found or inactive"
        )
    
    return Dealer(**dealer)

# Initialize sample data
@api_router.post("/initialize-data")
async def initialize_sample_data():
    # Clear existing data
    await db.products.delete_many({})
    await db.categories.delete_many({})
    await db.brands.delete_many({})
    
    # Sample categories
    categories = [
        {
            "name": "Body Armor & Protection",
            "slug": "body-armor",
            "description": "Professional body armor, plates, and protective gear",
            "image_url": "https://images.unsplash.com/photo-1704278483976-9cca15325bc0?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwzfHx0YWN0aWNhbCUyMGdlYXJ8ZW58MHx8fHwxNzU3Mzc1OTk5fDA&ixlib=rb-4.1.0&q=85"
        },
        {
            "name": "Tactical Apparel",
            "slug": "tactical-apparel", 
            "description": "Uniforms, boots, gloves, and tactical clothing",
            "image_url": "https://images.unsplash.com/photo-1705564667318-923901fb916a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwyfHx0YWN0aWNhbCUyMGdlYXJ8ZW58MHx8fHwxNzU3Mzc1OTk5fDA&ixlib=rb-4.1.0&q=85"
        },
        {
            "name": "Tactical Gear & Equipment",
            "slug": "tactical-gear",
            "description": "Backpacks, pouches, holsters, and tactical accessories",
            "image_url": "https://images.unsplash.com/photo-1714384716870-6d6322bf5a7f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwxfHx0YWN0aWNhbCUyMGdlYXJ8ZW58MHx8fHwxNzU3Mzc1OTk5fDA&ixlib=rb-4.1.0&q=85"
        },
        {
            "name": "Optics & Scopes",
            "slug": "optics",
            "description": "Red dots, scopes, night vision, and optical equipment",
            "image_url": "https://images.unsplash.com/photo-1704278483831-c3939b1b041b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHw0fHx0YWN0aWNhbCUyMGdlYXJ8ZW58MHx8fHwxNzU3Mzc1OTk5fDA&ixlib=rb-4.1.0&q=85"
        },
        {
            "name": "Weapons & Accessories",
            "slug": "weapons",
            "description": "Firearms, magazines, and weapon accessories",
            "image_url": "https://images.pexels.com/photos/78783/submachine-gun-rifle-automatic-weapon-weapon-78783.jpeg"
        },
        {
            "name": "Training & Simulation",
            "slug": "training",
            "description": "Training equipment and simulation gear",
            "image_url": "https://images.unsplash.com/photo-1637252166739-b47f8875f304?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwxfHxtaWxpdGFyeSUyMGVxdWlwbWVudHxlbnwwfHx8fDE3NTczNzYwMDd8MA&ixlib=rb-4.1.0&q=85"
        }
    ]
    
    for cat in categories:
        category = Category(**cat)
        await db.categories.insert_one(category.dict())
    
    # Sample brands with tactical logo placeholders
    brands = [
        {"name": "5.11 Tactical", "logo_url": "https://images.unsplash.com/photo-1753723883109-a575c639c0a3?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwyfHx0YWN0aWNhbCUyMGdlYXIlMjBsb2dvc3xlbnwwfHx8fDE3NTgwMDMyNTF8MA&ixlib=rb-4.1.0&q=85", "description": "Professional tactical gear and apparel"},
        {"name": "Blackhawk", "logo_url": "https://images.unsplash.com/photo-1636136370671-7ec07f284a2f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwxfHx0YWN0aWNhbHxlbnwwfHx8fDE3NTgwMDMyNzR8MA&ixlib=rb-4.1.0&q=85", "description": "Military and law enforcement equipment"},
        {"name": "Crye Precision", "logo_url": "https://images.unsplash.com/photo-1655706443789-7682c46bcb8b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1NzZ8MHwxfHNlYXJjaHwzfHxtaWxpdGFyeSUyMGxvZ29zfGVufDB8fHx8MTc1ODAwMzI3MHww&ixlib=rb-4.1.0&q=85", "description": "Advanced combat systems and gear"},
        {"name": "Oakley SI", "logo_url": "https://images.unsplash.com/photo-1711097658585-73d97ef42bf6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1NzZ8MHwxfHNlYXJjaHwxfHxtaWxpdGFyeSUyMGxvZ29zfGVufDB8fHx8MTc1ODAwMzI3MHww&ixlib=rb-4.1.0&q=85", "description": "Standard Issue tactical eyewear and gear"},
        {"name": "Condor Outdoor", "logo_url": "https://via.placeholder.com/200x80/2d2d2d/ffffff?text=CONDOR+TACTICAL", "description": "Tactical gear and outdoor equipment"},
        {"name": "Ops-Core", "logo_url": "https://via.placeholder.com/200x80/1a1a1a/ffffff?text=OPS-CORE", "description": "Advanced helmet and protection systems"},
        {"name": "Safariland", "logo_url": "https://via.placeholder.com/200x80/333333/ffffff?text=SAFARILAND", "description": "Law enforcement holsters and duty gear"},
        {"name": "Mechanix Wear", "logo_url": "https://via.placeholder.com/200x80/dc2626/ffffff?text=MECHANIX", "description": "Professional work and tactical gloves"}
    ]
    
    for brand in brands:
        brand_obj = Brand(**brand)
        await db.brands.insert_one(brand_obj.dict())
    
    # Sample products with varied stock status
    products = [
        {
            "name": "Tactical Plate Carrier Vest",
            "description": "Professional-grade plate carrier with MOLLE webbing system. Designed for military and law enforcement use.",
            "price": 299.99,
            "original_price": 399.99,
            "category": "Body Armor & Protection",
            "subcategory": "Plate Carriers",
            "brand": "5.11 Tactical",
            "image_url": "https://images.unsplash.com/photo-1704278483976-9cca15325bc0?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwzfHx0YWN0aWNhbCUyMGdlYXJ8ZW58MHx8fHwxNzU3Mzc1OTk5fDA&ixlib=rb-4.1.0&q=85",
            "rating": 4.8,
            "review_count": 156,
            "in_stock": True,
            "stock_quantity": 25,
            "features": ["MOLLE Compatible", "Adjustable Shoulder Straps", "Quick Release System", "Drag Handle"],
            "tags": ["tactical", "military", "law-enforcement", "protection"],
            "specifications": {"Material": "1000D Cordura", "Weight": "2.1 lbs", "Size": "One Size Fits Most"},
            "weight": "2.1 lbs"
        },
        {
            "name": "Combat Tactical Boots",
            "description": "Durable tactical boots designed for extreme conditions. Waterproof and slip-resistant.",
            "price": 189.99,
            "category": "Tactical Apparel",
            "subcategory": "Boots",
            "brand": "5.11 Tactical",
            "image_url": "https://images.unsplash.com/photo-1705564667318-923901fb916a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwyfHx0YWN0aWNhbCUyMGdlYXJ8ZW58MHx8fHwxNzU3Mzc1OTk5fDA&ixlib=rb-4.1.0&q=85",
            "rating": 4.6,
            "review_count": 89,
            "in_stock": True,
            "stock_quantity": 50,
            "features": ["Waterproof", "Slip-Resistant Sole", "Breathable Lining", "Reinforced Toe"],
            "tags": ["boots", "tactical", "waterproof", "military"],
            "specifications": {"Material": "Full-grain leather", "Height": "8 inches", "Weight": "2.5 lbs per pair"}
        },
        {
            "name": "Tactical Assault Backpack",
            "description": "3-day assault pack with multiple compartments and MOLLE attachment points.",
            "price": 129.99,
            "original_price": 169.99,
            "category": "Tactical Gear & Equipment",
            "subcategory": "Backpacks",
            "brand": "Blackhawk",
            "image_url": "https://images.unsplash.com/photo-1714384716870-6d6322bf5a7f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwxfHx0YWN0aWNhbCUyMGdlYXJ8ZW58MHx8fHwxNzU3Mzc1OTk5fDA&ixlib=rb-4.1.0&q=85",
            "rating": 4.7,
            "review_count": 234,
            "in_stock": True,
            "stock_quantity": 15,
            "features": ["40L Capacity", "MOLLE Compatible", "Hydration Ready", "Reinforced Bottom"],
            "tags": ["backpack", "tactical", "molle", "assault-pack"],
            "specifications": {"Capacity": "40L", "Material": "600D Polyester", "Dimensions": "19x13x8 inches"}
        },
        {
            "name": "Red Dot Sight Optic",
            "description": "Professional red dot sight with unlimited eye relief and parallax-free performance.",
            "price": 449.99,
            "category": "Optics & Scopes",
            "subcategory": "Red Dot Sights",
            "brand": "Ops-Core",
            "image_url": "https://images.unsplash.com/photo-1704278483831-c3939b1b041b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHw0fHx0YWN0aWNhbCUyMGdlYXJ8ZW58MHx8fHwxNzU3Mzc1OTk5fDA&ixlib=rb-4.1.0&q=85",
            "rating": 4.9,
            "review_count": 67,
            "in_stock": True,
            "stock_quantity": 8,
            "features": ["Parallax Free", "Unlimited Eye Relief", "Shockproof", "Waterproof"],
            "tags": ["optics", "red-dot", "tactical", "precision"],
            "is_restricted": True,
            "specifications": {"Battery Life": "50,000 hours", "Weight": "0.8 lbs", "Mount": "Picatinny Rail"}
        },
        {
            "name": "Tactical Combat Uniform Set",
            "description": "Complete ACU uniform set with reinforced knees and elbows. Flame resistant fabric.",
            "price": 89.99,
            "category": "Tactical Apparel",
            "subcategory": "Uniforms",
            "brand": "Crye Precision",
            "image_url": "https://images.pexels.com/photos/33812346/pexels-photo-33812346.jpeg",
            "rating": 4.5,
            "review_count": 178,
            "in_stock": True,
            "stock_quantity": 35,
            "features": ["Flame Resistant", "Reinforced Knees", "Multiple Pockets", "Adjustable Cuffs"],
            "tags": ["uniform", "tactical", "flame-resistant", "combat"],
            "specifications": {"Material": "50/50 NYCO", "Colors": "Multicam, OCP", "Sizes": "XS-3XL"}
        },
        {
            "name": "Ballistic Helmet System",
            "description": "Advanced combat helmet with NVG mount and accessory rails. NIJ Level IIIA protection.",
            "price": 899.99,
            "category": "Body Armor & Protection",
            "subcategory": "Helmets",
            "brand": "Ops-Core",
            "image_url": "https://images.pexels.com/photos/33819675/pexels-photo-33819675.jpeg",
            "rating": 4.9,
            "review_count": 45,
            "in_stock": False,  # Out of stock
            "stock_quantity": 0,
            "features": ["NIJ Level IIIA", "NVG Mount", "Accessory Rails", "Comfort Padding"],
            "tags": ["helmet", "ballistic", "protection", "tactical"],
            "is_restricted": True,
            "specifications": {"Protection Level": "NIJ Level IIIA", "Weight": "3.2 lbs", "Shell": "Carbon Fiber"}
        },
        {
            "name": "Tactical Knee Pads",
            "description": "Professional knee protection for tactical operations. Comfortable and durable.",
            "price": 39.99,
            "category": "Body Armor & Protection",
            "subcategory": "Protective Gear",
            "brand": "Blackhawk",
            "image_url": "https://images.pexels.com/photos/33759979/pexels-photo-33759979.jpeg",
            "rating": 4.4,
            "review_count": 312,
            "in_stock": True,
            "stock_quantity": 100,
            "features": ["Adjustable Straps", "Non-slip Design", "Durable Padding", "Lightweight"],
            "tags": ["knee-pads", "protection", "tactical", "gear"],
            "specifications": {"Material": "Neoprene & Nylon", "Weight": "0.8 lbs", "Size": "Adjustable"}
        },
        {
            "name": "Night Vision Monocular",
            "description": "Gen 3 night vision monocular for tactical operations. High-resolution imaging.",
            "price": 2499.99,
            "category": "Optics & Scopes",
            "subcategory": "Night Vision",
            "brand": "Ops-Core",
            "image_url": "https://images.unsplash.com/photo-1549563793-ae7c90155169?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHw0fHxtaWxpdGFyeSUyMGVxdWlwbWVudHxlbnwwfHx8fDE3NTczNjAwMDd8MA&ixlib=rb-4.1.0&q=85",
            "rating": 4.8,
            "review_count": 23,
            "in_stock": False,  # Out of stock
            "stock_quantity": 0,
            "features": ["Gen 3 Tube", "Auto-Gated", "High Resolution", "Durable Housing"],
            "tags": ["night-vision", "optics", "tactical", "surveillance"],
            "is_restricted": True,
            "specifications": {"Generation": "Gen 3", "Resolution": "64 lp/mm", "Weight": "1.2 lbs"}
        },
        # Additional products for better filtering testing
        {
            "name": "Tactical Gloves Pro",
            "description": "Professional tactical gloves with reinforced palm and fingertips.",
            "price": 45.99,
            "category": "Tactical Apparel",
            "subcategory": "Gloves",
            "brand": "Condor Outdoor",
            "image_url": "https://images.unsplash.com/photo-1705564667318-923901fb916a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwyfHx0YWN0aWNhbCUyMGdlYXJ8ZW58MHx8fHwxNzU3Mzc1OTk5fDA&ixlib=rb-4.1.0&q=85",
            "rating": 4.3,
            "review_count": 156,
            "in_stock": True,
            "stock_quantity": 75,
            "features": ["Reinforced Palm", "Touchscreen Compatible", "Breathable", "Durable"],
            "tags": ["gloves", "tactical", "protection"],
            "specifications": {"Material": "Synthetic Leather", "Sizes": "S-XL"}
        },
        {
            "name": "Weapon Cleaning Kit",
            "description": "Comprehensive cleaning kit for tactical weapons maintenance.",
            "price": 59.99,
            "category": "Weapons & Accessories",
            "subcategory": "Maintenance",
            "brand": "Oakley SI",
            "image_url": "https://images.pexels.com/photos/78783/submachine-gun-rifle-automatic-weapon-weapon-78783.jpeg",
            "rating": 4.6,
            "review_count": 89,
            "in_stock": True,
            "stock_quantity": 30,
            "features": ["Multi-Caliber", "Portable Case", "Quality Tools", "Instructions"],
            "tags": ["cleaning", "maintenance", "weapons"],
            "specifications": {"Compatible": "Multiple Calibers", "Weight": "1.5 lbs"}
        }
    ]
    
    for product in products:
        product_obj = Product(**product)
        await db.products.insert_one(product_obj.dict())
    
    return {"message": "Sample data initialized successfully"}

# Sample Users Creation Endpoint
@api_router.post("/create-sample-users")
async def create_sample_users():
    # Clear existing users and dealers
    await db.users.delete_many({})
    await db.dealers.delete_many({})
    
    # Create sample users
    sample_users = [
        {
            "email": "john.doe@company.com",
            "password": hash_password("password123"),
            "first_name": "John",
            "last_name": "Doe",
            "company_name": "Tactical Solutions LLC",
            "phone": "555-123-4567",
            "address": "123 Business Street",
            "city": "Security City",
            "state": "CA",
            "zip_code": "90210",
            "country": "United States",
            "is_active": True
        },
        {
            "email": "sarah.wilson@defense.gov",
            "password": hash_password("password123"),
            "first_name": "Sarah",
            "last_name": "Wilson",
            "company_name": "Defense Department",
            "phone": "555-987-6543",
            "address": "456 Government Ave",
            "city": "Washington",
            "state": "DC",
            "zip_code": "20001",
            "country": "United States",
            "is_active": True
        },
        {
            "email": "mike.johnson@police.org",
            "password": hash_password("password123"),
            "first_name": "Mike",
            "last_name": "Johnson",
            "company_name": "Metro Police Department",
            "phone": "555-456-7890",
            "address": "789 Safety Blvd",
            "city": "Metro City",
            "state": "TX",
            "zip_code": "75001",
            "country": "United States",
            "is_active": True
        }
    ]
    
    for user_data in sample_users:
        user_dict = {k: v for k, v in user_data.items() if k != "password"}
        user = User(**user_dict)
        user_with_password = user.dict()
        user_with_password["password"] = user_data["password"]
        await db.users.insert_one(user_with_password)
    
    # Create sample dealers
    sample_dealers = [
        {
            "email": "dealer@tactical-wholesale.com",
            "password": hash_password("dealer123"),
            "company_name": "Tactical Wholesale Partners",
            "contact_name": "Robert Smith",
            "phone": "555-111-2222",
            "address": "999 Wholesale District",
            "license_number": "TWP-123456789",
            "is_approved": True,
            "is_active": True
        },
        {
            "email": "admin@tactical-supply.com", 
            "password": hash_password("dealer123"),
            "company_name": "Tactical Supply Co",
            "contact_name": "Lisa Anderson",
            "phone": "555-333-4444",
            "address": "888 Supply Chain Ave",
            "license_number": "TSC-987654321",
            "is_approved": True,
            "is_active": True
        }
    ]
    
    for dealer_data in sample_dealers:
        dealer_dict = {k: v for k, v in dealer_data.items() if k != "password"}
        dealer = Dealer(**dealer_dict)
        dealer_with_password = dealer.dict()
        dealer_with_password["password"] = dealer_data["password"]
        await db.dealers.insert_one(dealer_with_password)
    
    # Create some sample quotes for demo
    users = await db.users.find().to_list(length=None)
    if users:
        sample_quotes = [
            {
                "user_id": users[0]["id"],
                "items": [
                    {"product_id": "sample-1", "quantity": 2, "price": 299.99, "notes": "Tactical Plate Carrier Vest - 5.11 Tactical"},
                    {"product_id": "sample-2", "quantity": 1, "price": 189.99, "notes": "Combat Tactical Boots - 5.11 Tactical"}
                ],
                "total_amount": 789.97,
                "project_name": "Security Team Upgrade Q1",
                "intended_use": "security_services",
                "delivery_date": datetime.now(timezone.utc) + timedelta(days=30),
                "delivery_address": "123 Business Street, Security City, CA 90210",
                "billing_address": "123 Business Street, Security City, CA 90210",
                "company_size": "51-200",
                "budget_range": "$5000-$15000",
                "additional_requirements": "Need training materials and bulk pricing for team of 12",
                "status": "pending"
            },
            {
                "user_id": users[1]["id"] if len(users) > 1 else users[0]["id"],
                "items": [
                    {"product_id": "sample-3", "quantity": 5, "price": 449.99, "notes": "Red Dot Sight Optic - Ops-Core"}
                ],
                "total_amount": 2249.95,
                "project_name": "Precision Equipment Procurement",
                "intended_use": "military",
                "delivery_date": datetime.now(timezone.utc) + timedelta(days=14),
                "delivery_address": "456 Government Ave, Washington, DC 20001",
                "billing_address": "456 Government Ave, Washington, DC 20001",
                "company_size": "1000+",
                "budget_range": "$15000-$50000",
                "additional_requirements": "Requires security clearance verification",
                "status": "approved",
                "admin_notes": "Approved for immediate processing. Contact procurement officer for delivery coordination."
            }
        ]
        
        for quote_data in sample_quotes:
            quote = Quote(**quote_data)
            await db.quotes.insert_one(quote.dict())
    
    # Create sample chat messages
    if users:
        sample_messages = [
            {
                "user_id": users[0]["id"],
                "sender_type": "user",
                "sender_name": "John Doe",
                "message": "Hello, I have a question about bulk pricing for tactical vests."
            },
            {
                "user_id": users[0]["id"],
                "sender_type": "admin",
                "sender_name": "Support Team",
                "message": "Hi John! I'd be happy to help with bulk pricing. How many units are you looking at?"
            },
            {
                "user_id": users[0]["id"],
                "sender_type": "user", 
                "sender_name": "John Doe",
                "message": "We need approximately 15-20 plate carriers for our security team."
            },
            {
                "user_id": users[0]["id"],
                "sender_type": "admin",
                "sender_name": "Support Team",
                "message": "Perfect! For orders of 15+ units, we offer a 12% discount. I'll prepare a detailed quote for you."
            }
        ]
        
        for msg_data in sample_messages:
            message = ChatMessage(**msg_data)
            await db.chat_messages.insert_one(message.dict())
    
    # Create sample admin accounts
    sample_admins = [
        {
            "email": "admin@oehtraders.com",
            "password": hash_password("admin123"),
            "username": "admin",
            "is_super_admin": True,
            "is_active": True
        },
        {
            "email": "support@oehtraders.com", 
            "password": hash_password("support123"),
            "username": "support",
            "is_super_admin": False,
            "is_active": True
        }
    ]
    
    for admin_data in sample_admins:
        admin_dict = {k: v for k, v in admin_data.items() if k != "password"}
        admin = Admin(**admin_dict)
        admin_with_password = admin.dict()
        admin_with_password["password"] = admin_data["password"]
        await db.admins.insert_one(admin_with_password)

    return {
        "message": "Sample users, dealers, quotes, chat messages, and admin accounts created successfully",
        "users_created": len(sample_users),
        "dealers_created": len(sample_dealers),
        "admins_created": len(sample_admins),
        "quotes_created": 2,
        "chat_messages_created": 4
    }

# User Authentication Endpoints
@api_router.post("/users/register")
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    user_dict = user_data.dict()
    hashed_password = hash_password(user_data.password)
    user = User(**{k: v for k, v in user_dict.items() if k != "password"})
    
    # Store with password
    user_with_password = user.dict()
    user_with_password["password"] = hashed_password
    
    await db.users.insert_one(user_with_password)
    
    return {"message": "User registration successful"}

@api_router.post("/users/login")
async def login_user(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    token = create_jwt_token(user["id"], "user")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(**user)
    }

@api_router.get("/users/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict())

# Dealer Authentication Endpoints (existing)
@api_router.post("/dealers/register")
async def register_dealer(dealer_data: DealerCreate):
    # Check if dealer already exists
    existing_dealer = await db.dealers.find_one({"email": dealer_data.email})
    if existing_dealer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dealer with this email already exists"
        )
    
    # Create new dealer
    dealer_dict = dealer_data.dict()
    hashed_password = hash_password(dealer_data.password)
    dealer = Dealer(**{k: v for k, v in dealer_dict.items() if k != "password"})
    
    # Store with password
    dealer_with_password = dealer.dict()
    dealer_with_password["password"] = hashed_password
    
    await db.dealers.insert_one(dealer_with_password)
    
    return {"message": "Dealer registration successful. Awaiting approval."}

@api_router.post("/dealers/login")
async def login_dealer(login_data: DealerLogin):
    dealer = await db.dealers.find_one({"email": login_data.email})
    if not dealer or not verify_password(login_data.password, dealer["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not dealer["is_approved"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dealer account pending approval"
        )
    
    if not dealer["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dealer account is inactive"
        )
    
    token = create_jwt_token(dealer["id"], "dealer")
    return {
        "access_token": token,
        "token_type": "bearer",
        "dealer": DealerResponse(**dealer)
    }

@api_router.get("/dealers/profile", response_model=DealerResponse)
async def get_dealer_profile(current_dealer: Dealer = Depends(get_current_dealer)):
    return DealerResponse(**current_dealer.dict())

# Admin Authentication Endpoints
@api_router.post("/admin/login")
async def login_admin(login_data: AdminLogin):
    admin = await db.admins.find_one({"username": login_data.username})
    if not admin or not verify_password(login_data.password, admin["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not admin["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive"
        )
    
    token = create_jwt_token(admin["id"], "admin")
    return {
        "access_token": token,
        "token_type": "bearer",
        "admin": AdminResponse(**admin)
    }

@api_router.get("/admin/profile", response_model=AdminResponse)
async def get_admin_profile(current_admin: Admin = Depends(get_current_admin)):
    return AdminResponse(**current_admin.dict())

# Enhanced Admin Endpoints for Dealer Management
@api_router.get("/admin/dealers/pending")
async def get_pending_dealers(current_admin: Admin = Depends(get_current_admin)):
    """Get all dealers pending approval"""
    dealers = await db.dealers.find({"is_approved": False, "is_active": True}).to_list(length=None)
    return [DealerResponse(**{k: v for k, v in dealer.items() if k != "_id" and k != "password"}) for dealer in dealers]

@api_router.get("/admin/dealers")
async def get_all_dealers(current_admin: Admin = Depends(get_current_admin)):
    """Get all dealers with their status"""
    dealers = await db.dealers.find().to_list(length=None)
    return [DealerResponse(**{k: v for k, v in dealer.items() if k != "_id" and k != "password"}) for dealer in dealers]

@api_router.put("/admin/dealers/{dealer_id}/approve")
async def approve_dealer(dealer_id: str, current_admin: Admin = Depends(get_current_admin)):
    """Approve a dealer registration"""
    result = await db.dealers.update_one(
        {"id": dealer_id},
        {"$set": {"is_approved": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Dealer not found")
    
    return {"message": "Dealer approved successfully"}

@api_router.put("/admin/dealers/{dealer_id}/reject")
async def reject_dealer(dealer_id: str, current_admin: Admin = Depends(get_current_admin)):
    """Reject a dealer registration"""
    result = await db.dealers.update_one(
        {"id": dealer_id},
        {"$set": {"is_active": False}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Dealer not found")
    
    return {"message": "Dealer rejected successfully"}

# Enhanced Admin Endpoints for User Management
@api_router.get("/admin/users")
async def get_all_users(current_admin: Admin = Depends(get_current_admin)):
    """Get all users"""
    users = await db.users.find().to_list(length=None)
    return [UserResponse(**{k: v for k, v in user.items() if k != "_id" and k != "password"}) for user in users]

@api_router.get("/admin/stats")
async def get_admin_stats(current_admin: Admin = Depends(get_current_admin)):
    """Get admin dashboard statistics"""
    stats = {
        "total_users": await db.users.count_documents({}),
        "total_dealers": await db.dealers.count_documents({}),
        "pending_dealers": await db.dealers.count_documents({"is_approved": False, "is_active": True}),
        "approved_dealers": await db.dealers.count_documents({"is_approved": True, "is_active": True}),
        "total_quotes": await db.quotes.count_documents({}),
        "pending_quotes": await db.quotes.count_documents({"status": "pending"}),
        "approved_quotes": await db.quotes.count_documents({"status": "approved"}),
        "total_products": await db.products.count_documents({}),
        "chat_messages": await db.chat_messages.count_documents({})
    }
    return stats

# ADMIN PRODUCT MANAGEMENT ENDPOINTS
@api_router.post("/admin/products", response_model=Product)
async def create_product(product_data: ProductCreate, current_admin: Admin = Depends(get_current_admin)):
    """Create a new product (Admin only)"""
    try:
        # Generate product ID and timestamps
        product_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        # Create product object
        product = Product(
            id=product_id,
            **product_data.dict(),
            created_at=now,
            updated_at=now
        )
        
        # Insert into database
        await db.products.insert_one(product.dict())
        
        return product
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}"
        )

@api_router.put("/admin/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_data: ProductUpdate, current_admin: Admin = Depends(get_current_admin)):
    """Update an existing product (Admin only)"""
    try:
        # Check if product exists
        existing_product = await db.products.find_one({"id": product_id})
        if not existing_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Prepare update data
        update_data = product_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update product in database
        await db.products.update_one(
            {"id": product_id},
            {"$set": update_data}
        )
        
        # Return updated product
        updated_product = await db.products.find_one({"id": product_id})
        return Product(**updated_product)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}"
        )

@api_router.delete("/admin/products/{product_id}")
async def delete_product(product_id: str, current_admin: Admin = Depends(get_current_admin)):
    """Delete a product (Admin only)"""
    try:
        # Check if product exists
        existing_product = await db.products.find_one({"id": product_id})
        if not existing_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Delete product from database
        result = await db.products.delete_one({"id": product_id})
        
        if result.deleted_count == 1:
            return {"message": "Product deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete product"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete product: {str(e)}"
        )

@api_router.get("/admin/products")
async def get_all_products_admin(
    current_admin: Admin = Depends(get_current_admin),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=100)
):
    """Get all products with pagination (Admin only)"""
    try:
        products = await db.products.find().skip(skip).limit(limit).to_list(length=None)
        total_count = await db.products.count_documents({})
        
        return {
            "products": [Product(**product) for product in products],
            "total_count": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch products: {str(e)}"
        )

@api_router.get("/admin/products/{product_id}", response_model=Product)
async def get_product_admin(product_id: str, current_admin: Admin = Depends(get_current_admin)):
    """Get product details (Admin only)"""
    try:
        product = await db.products.find_one({"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return Product(**product)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch product: {str(e)}"
        )

@api_router.post("/cart/add")
async def add_to_cart(request: AddToCartRequest, current_user: User = Depends(get_current_user)):
    # Check if product exists and is in stock
    product = await db.products.find_one({"id": request.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not product["in_stock"] or product["stock_quantity"] < request.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    # Find or create cart for user
    cart = await db.carts.find_one({"user_id": current_user.id})
    
    if not cart:
        cart = Cart(user_id=current_user.id, items=[])
        cart_dict = cart.dict()
    else:
        # Remove MongoDB _id field
        cart_dict = {k: v for k, v in cart.items() if k != "_id"}
    
    # Check if item already in cart
    item_found = False
    for item in cart_dict["items"]:
        if item["product_id"] == request.product_id:
            item["quantity"] += request.quantity
            item_found = True
            break
    
    if not item_found:
        cart_dict["items"].append({
            "product_id": request.product_id,
            "quantity": request.quantity,
            "price": product["price"]
        })
    
    # Calculate total
    cart_dict["total"] = sum(item["quantity"] * item["price"] for item in cart_dict["items"])
    cart_dict["updated_at"] = datetime.now(timezone.utc)
    
    # Save cart
    await db.carts.replace_one(
        {"user_id": current_user.id},
        cart_dict,
        upsert=True
    )
    
    return {"message": "Item added to cart", "cart": cart_dict}

@api_router.get("/cart")
async def get_cart(current_user: User = Depends(get_current_user)):
    cart = await db.carts.find_one({"user_id": current_user.id})
    if not cart:
        return {"items": [], "total": 0.0}
    
    # Get product details for each item
    enriched_items = []
    for item in cart["items"]:
        product = await db.products.find_one({"id": item["product_id"]})
        if product:
            # Remove MongoDB _id field to avoid serialization issues
            product_dict = {k: v for k, v in product.items() if k != "_id"}
            enriched_items.append({
                **item,
                "product": Product(**product_dict)
            })
    
    # Remove MongoDB _id field from cart
    cart_dict = {k: v for k, v in cart.items() if k != "_id"}
    cart_dict["items"] = enriched_items
    return cart_dict

@api_router.delete("/cart/item/{product_id}")
async def remove_from_cart(product_id: str, current_user: User = Depends(get_current_user)):
    cart = await db.carts.find_one({"user_id": current_user.id})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Remove MongoDB _id field
    cart_dict = {k: v for k, v in cart.items() if k != "_id"}
    cart_dict["items"] = [item for item in cart_dict["items"] if item["product_id"] != product_id]
    cart_dict["total"] = sum(item["quantity"] * item["price"] for item in cart_dict["items"])
    cart_dict["updated_at"] = datetime.now(timezone.utc)
    
    await db.carts.replace_one({"user_id": current_user.id}, cart_dict)
    return {"message": "Item removed from cart"}

# Quote System Endpoints
@api_router.post("/quotes")
async def create_quote(quote_data: QuoteCreate, current_user: User = Depends(get_current_user)):
    total_amount = 0
    # Assign actual product price to each item
    for item in quote_data.items:
        product = await db.products.find_one({"id": item.product_id})
        if product and "price" in product:
            item.price = product["price"]  # <-- assign actual price
            total_amount += product["price"] * item.quantity
        else:
            item.price = 0  # fallback if product not found
    
    # Create quote with updated items
    quote = Quote(
        user_id=current_user.id,
        items=quote_data.items,  # now contains correct prices
        total_amount=total_amount,  # use total calculated above
        project_name=quote_data.project_name,
        intended_use=quote_data.intended_use,
        delivery_date=quote_data.delivery_date,
        delivery_address=quote_data.delivery_address,
        billing_address=quote_data.billing_address,
        company_size=quote_data.company_size,
        budget_range=quote_data.budget_range,
        additional_requirements=quote_data.additional_requirements
    )
    
    await db.quotes.insert_one(quote.dict())
    
    # Clear user's cart after quote submission
    await db.carts.delete_one({"user_id": current_user.id})
    
    return {"message": "Quote submitted successfully", "quote_id": quote.id}

@api_router.get("/quotes", response_model=List[QuoteResponse])
async def get_user_quotes(current_user: User = Depends(get_current_user)):
    quotes = await db.quotes.find({"user_id": current_user.id}).sort("created_at", -1).to_list(length=None)
    
    quote_responses = []
    for quote in quotes:
        quote_dict = {k: v for k, v in quote.items() if k != "_id"}
        
        # Hide total if not approved
        if quote_dict.get("status") != "approved":
            quote_dict["total_amount"] = 0  # or None

        quote_responses.append(QuoteResponse(
            **quote_dict,
            user_name=f"{current_user.first_name} {current_user.last_name}",
            user_email=current_user.email,
            company_name=current_user.company_name
        ))
    
    return quote_responses

# Admin Endpoints for Quote Management
@api_router.get("/admin/quotes", response_model=List[QuoteResponse])
async def get_all_quotes():
    quotes = await db.quotes.find().sort("created_at", -1).to_list(length=None)
    quote_responses = []
    for quote in quotes:
        user = await db.users.find_one({"id": quote["user_id"]})
        quote_dict = {k: v for k, v in quote.items() if k != "_id"}  # ✅ keeps total_amount too
        if user:
            quote_responses.append(QuoteResponse(
                **quote_dict,
                user_name=f"{user['first_name']} {user['last_name']}",
                user_email=user["email"],
                company_name=user.get("company_name")
            ))
    return quote_responses

@api_router.put("/admin/quotes/{quote_id}/status")
async def update_quote_status(quote_id: str, status: str, admin_notes: str = ""):
    quote = await db.quotes.find_one({"id": quote_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    update_data = {
        "status": status,
        "admin_notes": admin_notes
    }

    await db.quotes.update_one({"id": quote_id}, {"$set": update_data})
    return {"message": "Quote status updated successfully"}

# Chat System Endpoints
@api_router.post("/chat/send")
async def send_message(message_data: ChatMessageCreate, current_user: User = Depends(get_current_user)):
    # For user messages, override sender info
    message = ChatMessage(
        user_id=current_user.id,
        sender_type="user",
        sender_name=f"{current_user.first_name} {current_user.last_name}",
        message=message_data.message
    )
    
    await db.chat_messages.insert_one(message.dict())
    return {"message": "Message sent successfully"}

@api_router.get("/chat/{user_id}")
async def get_chat_messages(user_id: str, current_user: User = Depends(get_current_user)):
    # Users can only access their own chat
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    messages = await db.chat_messages.find({"user_id": user_id}).sort("created_at", 1).to_list(length=None)
    return [ChatMessage(**{k: v for k, v in msg.items() if k != "_id"}) for msg in messages]

@api_router.post("/admin/chat/send")
async def admin_send_message(message_data: ChatMessageCreate, current_admin: Admin = Depends(get_current_admin)):
    # Admin sends message with proper authentication
    message = ChatMessage(
        user_id=message_data.user_id,
        sender_type="admin",
        sender_name=f"Admin ({current_admin.username})",
        message=message_data.message
    )
    await db.chat_messages.insert_one(message.dict())
    return {"message": "Admin message sent successfully"}

@api_router.get("/admin/chat/conversations")
async def get_all_conversations(current_admin: Admin = Depends(get_current_admin)):
    """Get all chat conversations with users"""
    # Get unique user IDs who have sent messages
    pipeline = [
        {"$group": {"_id": "$user_id", "last_message": {"$last": "$$ROOT"}, "message_count": {"$sum": 1}}},
        {"$sort": {"last_message.created_at": -1}}
    ]
    
    conversations = await db.chat_messages.aggregate(pipeline).to_list(length=None)
    
    # Enrich with user data
    enriched_conversations = []
    for conv in conversations:
        user = await db.users.find_one({"id": conv["_id"]})
        if user:
            enriched_conversations.append({
                "user_id": conv["_id"],
                "user_name": f"{user['first_name']} {user['last_name']}",
                "user_email": user["email"],
                "company_name": user.get("company_name", ""),
                "last_message": conv["last_message"]["message"],
                "last_message_time": conv["last_message"]["created_at"],
                "last_sender": conv["last_message"]["sender_type"],
                "message_count": conv["message_count"]
            })
    
    return enriched_conversations

@api_router.post("/admin/quotes/{quote_id}/send-email")
async def send_quote_email(quote_id: str, current_admin: Admin = Depends(get_current_admin)):
    """Send quote details and pricing via email to the user"""
    try:
        # Get quote details
        quote = await db.quotes.find_one({"id": quote_id})
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Get user details
        user = await db.users.find_one({"id": quote["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # For now, we'll just update the quote to mark that email was sent
        # In a real implementation, you would integrate with an email service like SendGrid
        await db.quotes.update_one(
            {"id": quote_id},
            {
                "$set": {
                    "email_sent": True,
                    "email_sent_at": datetime.now(timezone.utc).isoformat(),
                    "email_sent_by": current_admin.username
                }
            }
        )
        
        return {"message": f"Quote email sent successfully to {user['email']}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send quote email: {str(e)}")

@api_router.put("/admin/quotes/{quote_id}/pricing")
async def update_quote_pricing(quote_id: str, pricing_data: dict, current_admin: Admin = Depends(get_current_admin)):
    """Update quote pricing and make it visible to user"""
    try:
        # Get quote details
        quote = await db.quotes.find_one({"id": quote_id})
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Update quote with pricing
        update_data = {
            "total_amount": pricing_data.get("total_amount", 0),
            "admin_notes": pricing_data.get("admin_notes", ""),
            "pricing_updated_at": datetime.now(timezone.utc).isoformat(),
            "pricing_updated_by": current_admin.username,
            "status": "approved"  # Auto-approve when pricing is added
        }
        
        # Update individual item prices if provided
        if "item_prices" in pricing_data:
            items = quote.get("items", [])
            item_prices = pricing_data["item_prices"]
            for i, item in enumerate(items):
                if i < len(item_prices):
                    item["price"] = item_prices[i]
            update_data["items"] = items
        
        await db.quotes.update_one(
            {"id": quote_id},
            {"$set": update_data}
        )
        
        return {"message": "Quote pricing updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update quote pricing: {str(e)}")

@api_router.get("/admin/chat/{user_id}/messages")
async def get_user_chat_messages(user_id: str, current_admin: Admin = Depends(get_current_admin)):
    """Get all messages for a specific user conversation"""
    messages = await db.chat_messages.find({"user_id": user_id}).sort("created_at", 1).to_list(length=None)
    return [ChatMessage(**{k: v for k, v in msg.items() if k != "_id"}) for msg in messages]

@api_router.get("/admin/chat/{user_id}/quote-context")
async def get_user_quote_context(user_id: str, current_admin: Admin = Depends(get_current_admin)):
    """Get user's quote information for chat context"""
    try:
        # Get user details
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's quotes
        quotes = await db.quotes.find({"user_id": user_id}).sort("created_at", -1).to_list(length=5)
        
        # Format quote context
        quote_context = []
        for quote in quotes:
            quote_info = {
                "quote_id": quote["id"],
                "project_name": quote.get("project_name", ""),
                "status": quote.get("status", "pending"),
                "total_amount": quote.get("total_amount", 0),
                "created_at": quote.get("created_at", ""),
                "items": quote.get("items", []),
                "company_name": quote.get("company_name", ""),
                "intended_use": quote.get("intended_use", "")
            }
            quote_context.append(quote_info)
        
        return {
            "user": {
                "id": user["id"],
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                "email": user.get("email", ""),
                "company_name": user.get("company_name", ""),
                "phone": user.get("phone", "")
            },
            "quotes": quote_context
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quote context: {str(e)}")

# Enhanced Product endpoints with stock filtering (existing)
@api_router.get("/products", response_model=List[Product])
async def get_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    in_stock: Optional[bool] = None,
    limit: int = Query(default=20, le=100),
    skip: int = Query(default=0, ge=0)
):
    filter_query = {}
    
    if category:
        filter_query["category"] = category
    if brand:
        filter_query["brand"] = brand
    if min_price is not None:
        filter_query["price"] = {"$gte": min_price}
    if max_price is not None:
        if "price" in filter_query:
            filter_query["price"]["$lte"] = max_price
        else:
            filter_query["price"] = {"$lte": max_price}
    if search:
        filter_query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$in": [search.lower()]}}
        ]
    if in_stock is not None:
        filter_query["in_stock"] = in_stock
    
    products = await db.products.find(filter_query).skip(skip).limit(limit).to_list(length=None)
    return [Product(**product) for product in products]

@api_router.get("/categories/with-counts", response_model=List[CategoryWithCount])
async def get_categories_with_counts():
    # Get all categories
    categories = await db.categories.find().to_list(length=None)
    
    # Count products for each category
    categories_with_counts = []
    for category in categories:
        count = await db.products.count_documents({"category": category["name"]})
        category_dict = {k: v for k, v in category.items() if k != "_id"}
        category_dict["product_count"] = count
        categories_with_counts.append(CategoryWithCount(**category_dict))
    
    return categories_with_counts

@api_router.get("/brands/with-counts", response_model=List[BrandWithCount])
async def get_brands_with_counts():
    # Get all brands
    brands = await db.brands.find().to_list(length=None)
    
    # Count products for each brand
    brands_with_counts = []
    for brand in brands:
        count = await db.products.count_documents({"brand": brand["name"]})
        brand_dict = {k: v for k, v in brand.items() if k != "_id"}
        brand_dict["product_count"] = count
        brands_with_counts.append(BrandWithCount(**brand_dict))
    
    return brands_with_counts

@api_router.get("/products/price-range")
async def get_price_range():
    pipeline = [
        {
            "$group": {
                "_id": None,
                "min_price": {"$min": "$price"},
                "max_price": {"$max": "$price"}
            }
        }
    ]
    
    result = await db.products.aggregate(pipeline).to_list(1)
    if result:
        return {"min_price": result[0]["min_price"], "max_price": result[0]["max_price"]}
    else:
        return {"min_price": 0, "max_price": 1000}

@api_router.get("/products/featured", response_model=List[Product])
async def get_featured_products():
    products = await db.products.find({"rating": {"$gte": 4.7}}).limit(8).to_list(length=None)
    return [Product(**product) for product in products]

@api_router.get("/products/trending", response_model=List[Product])
async def get_trending_products():
    products = await db.products.find({"review_count": {"$gte": 100}}).limit(6).to_list(length=None)
    return [Product(**product) for product in products]

@api_router.get("/products/deals", response_model=List[Product])
async def get_deals():
    products = await db.products.find({"original_price": {"$exists": True, "$ne": None}}).limit(6).to_list(length=None)
    return [Product(**product) for product in products]

@api_router.get("/products/new-arrivals", response_model=List[Product])
async def get_new_arrivals():
    # Get products sorted by creation date (newest first)
    products = await db.products.find({}).sort("created_at", -1).limit(8).to_list(length=None)
    return [Product(**product) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.get("/categories", response_model=List[Category])
async def get_categories():
    categories = await db.categories.find().to_list(length=None)
    return [Category(**category) for category in categories]

@api_router.get("/brands", response_model=List[Brand])
async def get_brands():
    brands = await db.brands.find().to_list(length=None)
    return [Brand(**brand) for brand in brands]

# Original status endpoints
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

@api_router.get("/")
async def root():
    return {"message": "OEH TRADERS API v2.0 - B2B Platform with User Auth & Quote System"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.get("/")
async def root():
    return {
        "message": "OEH TRADERS API v2.0 - B2B Platform with User Auth & Quote System",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/health")
async def health_check():
    try:
        # Test database connection
        await db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Add startup delay for Railway health checks
@app.on_event("startup")
async def startup_event():
    # Add a small delay to ensure app is fully ready
    await asyncio.sleep(2)
    
    try:
        # Test database connection
        await db.command("ping")
        logger.info("✅ Successfully connected to MongoDB")
        logger.info("✅ FastAPI application started successfully on port 8000")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        # Don't exit in production, just log the error
        logger.info("⚠️  Continuing without database connection")

# Add a simple immediate response endpoint
@api_router.get("/ready")
async def ready_check():
    return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()}

@api_router.get("/health")
async def health_check():
    try:
        # Test database connection
        await db.command("ping")
        return {
            "status": "healthy", 
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        # Return 503 but don't crash
        return {
            "status": "degraded",
            "database": "disconnected", 
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "server:app", 
        host="0.0.0.0", 
        port=port, 
        reload=False,
        access_log=True
    )