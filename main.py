import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Any

from database import db, create_document, get_documents
from schemas import Product

app = FastAPI(title="Food Store API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Food Store Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or ("✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# -------------------------
# Food/Menu Endpoints
# -------------------------

SAMPLE_PRODUCTS = [
    {
        "title": "Classic Bubble Tea",
        "description": "Black tea with milk, chewy tapioca pearls.",
        "price": 4.99,
        "category": "Drinks",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1582582429416-1240ee0f3574?auto=format&fit=crop&w=900&q=60"
    },
    {
        "title": "Strawberry Matcha",
        "description": "Layered matcha with fresh strawberry puree.",
        "price": 5.99,
        "category": "Drinks",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=900&q=60"
    },
    {
        "title": "Taro Milk Tea",
        "description": "Creamy taro with brown sugar pearls.",
        "price": 5.49,
        "category": "Drinks",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1542621334-a254cf47733d?auto=format&fit=crop&w=900&q=60"
    },
    {
        "title": "Chicken Katsu Bowl",
        "description": "Crispy chicken katsu on steamed rice with slaw.",
        "price": 10.99,
        "category": "Bowls",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1617093727343-374698b1b08a?auto=format&fit=crop&w=900&q=60"
    },
    {
        "title": "Spicy Tuna Poke",
        "description": "Ahi tuna, spicy mayo, avocado, sesame.",
        "price": 12.49,
        "category": "Bowls",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1617191514902-1f539cfec1cf?auto=format&fit=crop&w=900&q=60"
    },
    {
        "title": "Crispy Fries",
        "description": "Golden fries with house seasoning.",
        "price": 3.99,
        "category": "Snacks",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1541599540903-216a46ca1dc0?auto=format&fit=crop&w=900&q=60"
    }
]


def _serialize(doc: dict) -> dict:
    from bson import ObjectId
    out = {**doc}
    if "_id" in out and isinstance(out["_id"], ObjectId):
        out["id"] = str(out.pop("_id"))
    return out


@app.get("/api/menu")
def get_menu(category: str | None = None):
    """Return menu products from DB. Seed sample data if empty."""
    if db is None:
        # If DB not available, return sample data (non-persistent)
        data = SAMPLE_PRODUCTS
        if category:
            data = [p for p in data if p.get("category") == category]
        return {"items": data}

    # Check if there are products; if none, seed with sample set
    count = db["product"].count_documents({})
    if count == 0:
        for item in SAMPLE_PRODUCTS:
            try:
                # Validate with schema then insert
                prod = Product(**{k: item[k] for k in ["title", "description", "price", "category", "in_stock"]})
                # Keep image as extra field
                data_dict = prod.model_dump()
                data_dict["image"] = item.get("image")
                create_document("product", data_dict)
            except Exception:
                # Continue even if one insert fails
                pass

    # Query products
    filt = {"category": category} if category else {}
    docs = get_documents("product", filt)
    items = [_serialize(d) for d in docs]
    return {"items": items}


@app.get("/api/categories")
def get_categories() -> dict:
    if db is None:
        cats = sorted(list({p["category"] for p in SAMPLE_PRODUCTS}))
        return {"categories": cats}
    cats = db["product"].distinct("category")
    cats = [c for c in cats if c]
    cats.sort()
    return {"categories": cats}


@app.get("/schema")
def get_schema() -> dict:
    # Minimal schema exposure for viewer
    return {
        "product": Product.model_json_schema()
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
