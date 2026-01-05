
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import database
import datetime

# Initialize DB (will likely switch to SQLITE)
database.init_db()

app = FastAPI()

# Enable CORS for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class OrderRequest(BaseModel):
    member_id: str # Use "NON-MEMBER" for non-members or actual ID
    amount: int
    items: str # Description of items
    type: str # 'Immediate' or 'Pre-order' or 'Takeaway'
    delivery_date: Optional[str] = None

class Member(BaseModel):
    member_id: str
    name: str
    coins: int

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Merchant Bot API"}

@app.get("/orders")
def get_orders():
    """Returns all orders."""
    orders = database.get_all_orders()
    # Serialize datetime objects
    for o in orders:
        if isinstance(o.get('time'), datetime.datetime):
            o['time'] = o['time'].isoformat()
    return orders

@app.get("/members")
def get_members():
    """Returns all members."""
    members = database.get_all_members()
    return members

@app.post("/place-order")
def place_order(order: OrderRequest):
    """Allows staff/admin to place an order manually."""
    # If member, check/deduct balance?
    # For simplicity, if member_id is provided and valid, we deduct coins.
    
    saved_order = None
    
    # 1. Check if Member
    if order.member_id and order.member_id.lower() != "non-member":
        # Simplified: We assume staff verified the user if they entered an ID.
        # But we should check balance if we want to be strict.
        balance = database.get_member_balance(order.member_id)
        if balance < order.amount:
            raise HTTPException(status_code=400, detail="Insufficient member balance")
            
        new_bal = balance - order.amount
        database.update_member_coins(order.member_id, new_bal)
        saved_order = database.save_order(order.member_id, order.amount, order.type, order.delivery_date, order.items)
    else:
        # Non-member
        # Generate random Guest ID
        import random
        guest_id = random.randint(1000, 9999)
        db_id = f"Guest-{guest_id}"
        saved_order = database.save_order(db_id, order.amount, order.type, order.delivery_date, order.items)

    if saved_order is None and database.DB_MODE != "MOCK":
        # If save_order didn't return (it returns None in SQL mode currently in my impl, wait)
        # We can just return success
        pass
    return {"status": "Order Placed", "order": saved_order}

@app.post("/complete-order/{order_id}")
def complete_order(order_id: int):
    success = database.update_order_status(order_id, "Completed")
    if success:
        return {"status": "Order Completed"}
    raise HTTPException(status_code=400, detail="Failed to complete order")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
