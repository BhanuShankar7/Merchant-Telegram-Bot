
import logging
import os
import contextlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import datetime
import uvicorn
from dotenv import load_dotenv

# Import Project Modules
import database
import bot

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load Env
load_dotenv()

# Lifecycle Manager for Bot + API
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Initializing Database...")
    database.init_db()
    
    logger.info("Starting Telegram Bot...")
    bot_app = bot.get_application()
    
    if bot_app:
        await bot_app.initialize()
        await bot_app.start()
        
        # Start Polling (Non-blocking mode via updater)
        # allowed_updates=None (all), drop_pending_updates=False
        await bot_app.updater.start_polling(drop_pending_updates=True)
        
        logger.info("Telegram Bot Started via Polling.")
        
        # yield control back to FastAPI
        yield
        
        # --- Shutdown ---
        logger.info("Stopping Telegram Bot...")
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        logger.info("Telegram Bot Stopped.")
    else:
        logger.warning("Telegram Bot Failed to Initialize (Check Token).")
        yield

# Initialize FastAPI with Lifespan
app = FastAPI(title="Merchant Bot API", lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# API MODELS & ENDPOINTS (Copied/Adapted from api.py)
# -----------------------------------------------------------------------------

class OrderRequest(BaseModel):
    member_id: str
    amount: int
    items: str
    type: str # 'Immediate' or 'Pre-order' or 'Takeaway'
    delivery_date: Optional[str] = None

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Merchant Bot API & Dashboard Backend"}

@app.get("/orders")
def get_orders():
    """Returns all orders."""
    orders = database.get_all_orders()
    for o in orders:
        if isinstance(o.get('time'), datetime.datetime):
            o['time'] = o['time'].isoformat()
    return orders

@app.get("/members")
def get_members():
    """Returns all members."""
    return database.get_all_members()

@app.post("/place-order")
def place_order(order: OrderRequest):
    """Allows staff/admin to place an order manually."""
    
    # Check Member Balance
    if order.member_id and order.member_id.lower() != "non-member":
        balance = database.get_member_balance(order.member_id)
        if balance < order.amount:
            raise HTTPException(status_code=400, detail="Insufficient member balance")
            
        new_bal = balance - order.amount
        database.update_member_coins(order.member_id, new_bal)
        saved_order = database.save_order(order.member_id, order.amount, order.type, order.delivery_date, order.items)
    else:
        # Guest
        import random
        guest_id = random.randint(1000, 9999)
        db_id = f"Guest-{guest_id}"
        saved_order = database.save_order(db_id, order.amount, order.type, order.delivery_date, order.items)

    return {"status": "Order Placed", "order": saved_order}

@app.post("/complete-order/{order_id}")
def complete_order(order_id: int):
    success = database.update_order_status(order_id, "Completed")
    if success:
        return {"status": "Order Completed"}
    raise HTTPException(status_code=400, detail="Failed to complete order")

if __name__ == "__main__":
    # Local Dev Run
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
