
import logging
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
import database

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()


# Initialize Database is now handled in main.py lifespan
# try:
#     database.init_db()
# except Exception as e:
#     logger.error(f"DB Init Failed: {e}")


# MEMBER MENU (Coins)
# MEMBER MENU (Rupees)
MENU_MEMBER = {
    "Sprouts Salad": 50,
    "Protein Bowl": 55,
    "Chia Pudding": 65,
    "Oats + Chia": 65,
    "Papaya Bowl": 50,
    "Pineapple Bowl": 50,
    "Muskmelon Bowl": 50,
    "Watermelon Bowl": 50,
    "Mixed Fruit Bowl": 65,
    "Protein Veg Salad": 155
}

# NON-MEMBER MENU (Rupees)
MENU_NON_MEMBER = {
    "Sprouts Salad": 50,
    "Protein Bowl": 55,
    "Chia Pudding": 65,
    "Oats + Chia": 65,
    "Papaya Bowl": 50,
    "Pineapple Bowl": 50,
    "Muskmelon Bowl": 50,
    "Watermelon Bowl": 50,
    "Mixed Fruit Bowl": 65,
    "Protein Veg Salad": 155
}

# STATES
PLAN_SELECTION = 1
MEMBER_LOGIN = 2
MEMBER_SHOPPING = 3
NON_MEMBER_SHOPPING = 4
TAKEAWAY_SELECTION = 5
MEMBER_DELIVERY_CHOICE = 6
MEMBER_PREORDER_DATE = 7

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def get_greeting():
    h = datetime.now().hour
    if 5 <= h < 12: return "Good Morning ☀️"
    elif 12 <= h < 17: return "Good Afternoon 🌤️"
    elif 17 <= h < 21: return "Good Evening 🌆"
    else: return "Good Night 🌙"

def format_cart_table(cart, is_member):
    lines = []
    lines.append("Item | Qty | Price")
    lines.append("-" * 25)
    
    total = 0
    menu = MENU_MEMBER if is_member else MENU_NON_MEMBER
    
    for item, qty in cart.items():
        cost = menu.get(item, 0) * qty
        total += cost
        lines.append(f"{item} | {qty} | ₹{cost}")
    
    lines.append("-" * 25)
    return "\n".join(lines), total

# -----------------------------------------------------------------------------
# HANDLERS
# -----------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    
    greeting = get_greeting()
    msg = (
        f"🌟 {greeting}\n\n"
        "Welcome to *Neutrious Theory* 🥗💪\n"
        "Your health, our priority.\n\n"
        "Please select your plan:\n"
        "1️⃣ Membership\n"
        "2️⃣ Non-Membership\n\n"
        "Reply with *1* or *2*"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return PLAN_SELECTION

async def handle_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    
    if text == "1":
        await update.message.reply_text("🔐 Please enter your Membership ID :")
        return MEMBER_LOGIN
    elif text == "2":
        context.user_data["is_member"] = False
        context.user_data["cart"] = {}
        await show_non_member_menu(update, context)
        return NON_MEMBER_SHOPPING
    else:
        await update.message.reply_text("❌ Invalid option. Reply with 1 or 2.")
        return PLAN_SELECTION

async def handle_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # First ask ID, then PIN? Or stick to simple flow.
    # The prompt asked for PIN verification.
    # Let's assume input is ID first, then we ask PIN.
    # But to keep it simple as per prompt "Please enter your 4-digit Membership PIN",
    # we need to know WHO the user is. 
    # For this demo, let's parse "ID PIN" or just "ID".
    # Let's do: User enters ID, we check DB, if exists, ask PIN? 
    # To match prompt exactly: "Please enter your 4-digit Membership PIN". 
    # This implies the user is known. Let's just ask for ID first.
    
    text = update.message.text.strip()
    
    # Store ID temporarily
    if "temp_id" not in context.user_data:
        context.user_data["temp_id"] = text
        await update.message.reply_text("🔐 Enter your 4-digit PIN:")
        return MEMBER_LOGIN
    else:
        # Validate ID + PIN
        member_id = context.user_data["temp_id"]
        pin = text
        
        member = database.check_member(member_id, pin)
        if member:
            context.user_data["member_data"] = member
            context.user_data["is_member"] = True
            context.user_data["cart"] = {}
            
            coins = member['coins']
            
            msg = (
                "✅ PIN Verified Successfully!\n\n"
                f"💳 Membership Balance: ₹{coins}\n\n"
                f"💳 Membership Balance: ₹{coins}\n\n"
                "🍽️ Today’s Menu:\n"
            )
            i = 1
            for item, price in MENU_MEMBER.items():
                msg += f"{i}. {item} – ₹{price}\n"
                i += 1
            
            msg += "\n👉 Reply like:\n2 x 3 (Item 2, Qty 3)\nProtein Bowl * 2"
            
            # Add Button
            keyboard = [["✅ Place Order"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(msg, reply_markup=reply_markup)
            return MEMBER_SHOPPING
        else:
            del context.user_data["temp_id"]
            await update.message.reply_text("❌ Invalid ID or PIN. Try again from ID.")
            return MEMBER_LOGIN

async def show_non_member_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🍽️ Today’s Menu (Non-Member):\n\n"
    )
    i = 1
    for item, price in MENU_NON_MEMBER.items():
        msg += f"{i}. {item} – ₹{price}\n"
        i += 1
        
    msg += "\n👉 Reply like:\n1 x 2 (Item 1, Qty 2)\nProtein Bowl * 1"
    
    keyboard = [["✅ Place Order"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(msg, reply_markup=reply_markup)

async def handle_shopping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    cart = context.user_data.get("cart", {})
    is_member = context.user_data.get("is_member", False)
    
    # Check for keywords
    # Check for keywords
    if text.lower() in ["place order", "checkout", "✅ place order"]:
        if not cart:
            keyboard = [["✅ Place Order"]]
            markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("❌ Cart is empty.", reply_markup=markup)
            return MEMBER_SHOPPING if is_member else NON_MEMBER_SHOPPING
        
        if is_member:
            return await ask_member_delivery_option(update, context)
        else:
            return await finalize_non_member_order(update, context)
            
    if is_member and text.lower() in ["balance", "coins", "membership balance"]:
        member_id = context.user_data["member_data"]["member_id"]
        coins = database.get_member_balance(member_id)
        msg = (
            "💳 *Membership Balance*\n\n"
            f"Available: ₹{coins}\n"
            "Status: Active ✅"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return MEMBER_SHOPPING

    # Parse Multiple Items
    # Split by comma or newline
    order_lines = re.split(r'[,\n]', text)
    items_updates = []
    
    for line in order_lines:
        # Check for removal command
        is_removal = False
        clean_line = line.strip()
        if clean_line.lower().startswith("remove"):
            is_removal = True
            clean_line = clean_line[6:].strip() # Remove "remove" keyword
            
        # Regex to match "2x4", "Item x 2", "Item * 2"
        # \s* allows matches with or without spaces
        match = re.search(r"(.+?)\s*[xX*]\s*(\d+)", clean_line)
        if match:
            input_identifier = match.group(1).strip()
            qty = int(match.group(2))
            
            menu = MENU_MEMBER if is_member else MENU_NON_MEMBER
            valid_item = None
            
            # Check if input is a number (Menu Index)
            if input_identifier.isdigit():
                idx = int(input_identifier) - 1
                menu_keys = list(menu.keys())
                if 0 <= idx < len(menu_keys):
                    valid_item = menu_keys[idx]
            else:
                # Fuzzy match item name
                for menu_item in menu:
                    if input_identifier.lower() in menu_item.lower():
                        valid_item = menu_item
                        break
            
            if valid_item:
                if is_removal:
                    # Remove Logic
                    if valid_item in cart:
                        current_qty = cart[valid_item]
                        new_qty = current_qty - qty
                        if new_qty <= 0:
                            del cart[valid_item]
                            items_updates.append(f"❌ Removed: {valid_item}")
                        else:
                            cart[valid_item] = new_qty
                            items_updates.append(f"📉 Decreased: {valid_item} (Now x{new_qty})")
                    else:
                        items_updates.append(f"⚠️ Not in cart: {valid_item}")
                else:
                    # Add Logic
                    if qty > 0:
                        cart[valid_item] = cart.get(valid_item, 0) + qty 
                        items_updates.append(f"✅ Added: {valid_item} x {qty}")
                    elif qty == 0:
                        if valid_item in cart: 
                            del cart[valid_item]
                            items_updates.append(f"❌ Removed: {valid_item}")
            else:
                items_updates.append(f"⚠️ Not Found: {input_identifier}")

    # Re-send button with every update
    keyboard = [["✅ Place Order"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if items_updates:
        context.user_data["cart"] = cart
        
        # Show dynamic table
        table_str, total = format_cart_table(cart, is_member)
        
        update_summary = "\n".join(items_updates)
        msg = (
            f"{update_summary}\n\n"
            "🛒 *Your Cart Updated*\n"
            f"{table_str}\n"
        )
        if is_member:
            msg += f"Total: ₹{total}\n"
            member_coins = context.user_data["member_data"]["coins"]
            msg += f"💡 Your Balance: ₹{member_coins}\n"
        else:
            msg += f"Total Amount: ₹{total}\n"
            
        msg += "\nType more items or click '✅ Place Order'"
        
        keyboard = [["✅ Place Order"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)
        return MEMBER_SHOPPING if is_member else NON_MEMBER_SHOPPING
    else:
        await update.message.reply_text("❌ Format not recognized. Try: 2x3 or Protein Bowl x2", reply_markup=reply_markup)
        return MEMBER_SHOPPING if is_member else NON_MEMBER_SHOPPING

async def ask_member_delivery_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Checks coin balance and asks for Delivery vs Takeaway"""
    cart = context.user_data["cart"]
    member_data = context.user_data["member_data"]
    member_id = member_data["member_id"]
    
    # Calculate Total
    total_coins = 0
    for item, qty in cart.items():
        total_coins += MENU_MEMBER[item] * qty
        
    current_balance = database.get_member_balance(member_id)
    
    # Pre-check funds
    if total_coins > current_balance:
        await update.message.reply_text(
            "❌ Insufficient Membership Balance\n\n"
            f"Required: ₹{total_coins}\n"
            f"Available: ₹{current_balance}\n\n"
            "⚠️ Please remove items or recharge membership."
        )
        return MEMBER_SHOPPING
    
    # Funds OK -> Ask Option
    context.user_data["final_coins"] = total_coins
    
    current_hour = datetime.now().hour
    
    # Logic: Delivery only available 12 AM to 8 AM for TODAY
    if 0 <= current_hour < 8:
        msg = (
            "✅ Order Ready for Processing!\n\n"
            "Select Service Type:\n"
            "1️⃣ Today's Delivery 🚚 (6:00 AM - 9:00 AM)\n"
            "2️⃣ Pre-order for Later 📅\n"
            "3️⃣ Takeaway 🥡\n\n"
            "Reply *1*, *2*, *3* or *Cancel*"
        )
    else:
        msg = (
            "✅ Order Ready for Processing!\n\n"
            "⚠️ Today's Delivery Closed (Order before 8 AM)\n\n"
            "Select Service Type:\n"
            "2️⃣ Pre-order for Tomorrow 📅\n"
            "3️⃣ Takeaway 🥡\n\n"
            "Reply *2*, *3* or *Cancel*"
        )
        
    # Remove keyboard for selection
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return MEMBER_DELIVERY_CHOICE

async def handle_member_delivery_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    current_hour = datetime.now().hour
    is_delivery_time = 0 <= current_hour < 8
    
    if text == "1":
        if is_delivery_time:
            # TODAY'S Delivery
            # Implicitly Today's Date
            today = datetime.now().strftime("%d-%m-%Y")
            delivery_info = f"Delivery 🚚\n📅 Date: {today} (Today)\n⏰ Slot: 6:00 AM - 9:00 AM"
            return await process_member_transaction(update, context, "Delivery", delivery_info)
        else:
             await update.message.reply_text("❌ Today's delivery closed. Try Pre-order (2) or Takeaway (3).")
             return MEMBER_DELIVERY_CHOICE

    elif text == "3":
        # Takeaway -> Standard finish
        return await process_member_transaction(update, context, "Takeaway 🥡", "20 minutes")
        
    elif text == "2":
        # Pre-order (Both scenarios)
        tom = datetime.now() + timedelta(days=1)
        tom_str = tom.strftime("%d-%m-%Y")
        
        await update.message.reply_text(
            "📅 **Pre-order Selected**\n\n"
            f"Ordering for Date: {tom_str} (Tomorrow)\n"
            "Delivery Slot: **6:00 AM - 9:00 AM**\n\n"
            "Reply **'Yes'** to confirm or **'Cancel'** to go back."
        , parse_mode="Markdown")
        
        context.user_data["preorder_date_str"] = tom_str
        return MEMBER_PREORDER_DATE
    elif text.lower() == "cancel" or text == "4":
        await update.message.reply_text("🚫 Delivery selection cancelled. Returning to cart.")
        return MEMBER_SHOPPING
    else:
        await update.message.reply_text("❌ Invalid choice. Reply 1, 2, 3 or Cancel.")
        return MEMBER_DELIVERY_CHOICE

async def handle_member_preorder_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().lower()
    
    if text in ["yes", "y", "confirm"]:
        date_str = context.user_data.get("preorder_date_str", "Tomorrow")
        delivery_info = f"Delivery 🚚\n📅 Date: {date_str}\n⏰ Slot: 6:00 AM - 9:00 AM"
        return await process_member_transaction(update, context, "Pre-order Delivery", delivery_info)
    elif text in ["cancel", "no", "stop"]:
        await update.message.reply_text(
            "🚫 Your Order Cancelled!\n\n"
            "Thank you for visiting *Neutrious Theory* 🙏",
            parse_mode="Markdown"
        )
        return MEMBER_SHOPPING
    else:
        await update.message.reply_text("❌ Please reply 'Yes' to confirm or 'Cancel' to stop.")
        return MEMBER_PREORDER_DATE

async def process_member_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE, type_label, time_info) -> int:
    # Final deduction and receipt
    cart = context.user_data["cart"]
    member_id = context.user_data["member_data"]["member_id"]
    total_coins = context.user_data["final_coins"]
    
    # Re-read balance just in case
    current_balance = database.get_member_balance(member_id)
    new_balance = current_balance - total_coins
    
    # Verify again (race condition minimal in this demo)
    if new_balance < 0:
        await update.message.reply_text("❌ Insufficient coins.")
        return MEMBER_SHOPPING
        
    # Update DB
    database.update_member_coins(member_id, new_balance)
    
    table_str, _ = format_cart_table(cart, True)
    
    order_type = "Immediate"
    del_date = None
    
    if type_label == "Delivery":
        pickup_msg = time_info
        # Check if text contains "Today" to determine type for Cancellation logic
        if "(Today)" in time_info:
            order_type = "Immediate"
        else:
            order_type = "Pre-order"
             # Extract date logic handled loosely
            del_date = context.user_data.get("preorder_date_str")
            
    elif "Pre-order" in type_label:
        order_type = "Pre-order"
        del_date = context.user_data.get("preorder_date_str")
        pickup_msg = f"{type_label}\n{time_info}"
    else:
        pickup_msg = f"📦 {type_label}\n⏰ Ready in: {time_info}"
        order_type = "Immediate" # Takeaway treated as same-day logic
    
    # SAVE ORDER
    # Create Item Summary
    items_summary = ", ".join([f"{k} x{v}" for k, v in cart.items()])
    database.save_order(member_id, total_coins, order_type, del_date, items_summary)
    
    msg = (
        "✅ Thank you for your Order! 🙏\n\n"
        "🧾 Bill Details:\n"
        f"{table_str}\n"
        f"Total Used: ₹{total_coins}\n\n"
        f"💳 Remaining Balance: ₹{new_balance}\n\n"
        f"{pickup_msg}\n\n"
        "To cancel, type: */cancel_order*\n\n"
        "🌟 *Neutrious Theory* 🌟"
    )
    await update.message.reply_text(msg)
    return ConversationHandler.END

async def finalize_non_member_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cart = context.user_data["cart"]
    table_str, total = format_cart_table(cart, False)
    
    context.user_data["final_total"] = total
    
    msg = (
        "🛒 Order Summary\n\n"
        f"{table_str}\n"
        f"Total Amount: ₹{total}\n\n"
        "⏰ Please select takeaway time:\n"
        "1️⃣ 15 minutes\n"
        "2️⃣ 30 minutes\n"
        "3️⃣ 45 minutes"
    )
    await update.message.reply_text(msg)
    return TAKEAWAY_SELECTION

async def handle_takeaway(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    times = {"1": "15 minutes", "2": "30 minutes", "3": "45 minutes"}
    
    if text not in times:
         await update.message.reply_text("❌ Please reply 1, 2, or 3.")
         return TAKEAWAY_SELECTION
         
    pickup_time = times[text]
    total = context.user_data["final_total"]

    # Generate Guest ID
    import random
    guest_id = random.randint(1000, 9999)
    db_id = f"Guest-{guest_id}"
    
    
    # Save Order
    # Create Item Summary
    cart = context.user_data.get("cart", {})
    items_summary = ", ".join([f"{k} x{v}" for k, v in cart.items()])
    
    database.save_order(db_id, total, "Takeaway", None, items_summary)
    
    msg = (
        "✅ Order Confirmed!\n\n"
        f"🔢 **Your Order ID: {guest_id}**\n"
        f"📍 Please pay ₹{total} at the shop counter\n"
        f"⏰ Pickup Time: {pickup_time}\n\n"
        "Thank you for visiting *Neutrious Theory* 🥗"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🚫 Operation cancelled. /start to reset.")
    return ConversationHandler.END

async def handle_cancel_last_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles logic to cancel the last active order."""
    try:
        # Check if user passed an Order ID (e.g., /cancel_order 1234)
        args = context.args
        target_order_id = None
        
        if args and len(args) > 0:
            if args[0].isdigit():
                target_order_id = int(args[0])
        
        # Determine Member ID or identifying info
        member_id = None
        if "member_data" in context.user_data:
            member_id = context.user_data["member_data"]["member_id"]
        
        # If we have neither session nor explicit ID
        if not member_id and not target_order_id:
            await update.message.reply_text(
                "❌ **Session Expired or Not Found**\n"
                "Please login again or provide your Order ID.\n\n"
                "Usage: `/cancel_order <Order_ID>`\n"
                "Example: `/cancel_order 12`",
                parse_mode="Markdown"
            )
            return

        order_to_cancel = None
        
        # Strategy 1: Look up by Order ID if provided
        if target_order_id:
            # We need a db function to get order by ID
            # Currently we primarily have get_last_active_order. 
            # I'll rely on a manual search since I can't easily change DB interface right now without risk.
            # Actually, let's use a quick search similar to update_order_status
             all_orders = database.get_all_orders() # efficient enough for demo
             for o in all_orders:
                 if o['id'] == target_order_id:
                     order_to_cancel = o
                     member_id = o['member_id'] # found owner
                     break
                     
        # Strategy 2: Look up last active order for cached member
        elif member_id:
            order_to_cancel = database.get_last_active_order(member_id)

        if not order_to_cancel:
            await update.message.reply_text("❌ No active order found to cancel.")
            return
            
        # Check status
        if order_to_cancel['status'] != 'Active':
             await update.message.reply_text("❌ Order is already processed or cancelled.")
             return

        # Check Rules
        now = datetime.now()
        
        # Parse Time
        # DB 'time' might be str or datetime depending on DB mode. 
        # get_last_active_order handles conversion, but let's be safe.
        order_time = order_to_cancel["time"]
        if isinstance(order_time, str):
            try:
                # Attempt common formats
                order_time = datetime.strptime(order_time, "%Y-%m-%d %H:%M:%S.%f")
            except:
                try:
                    order_time = datetime.strptime(order_time, "%Y-%m-%d %H:%M:%S")
                except:
                    order_time = now # Fallback

        order_type = order_to_cancel["type"]
        refund_amt = order_to_cancel["amount"]
        
        can_cancel = False
        fail_reason = ""
        
        if "Takeaway" in order_type or order_type == "Immediate":
            # Rule: Within 15 mins
            elapsed = (now - order_time).total_seconds()
            if elapsed < 900: # 15 * 60
                can_cancel = True
            else:
                fail_reason = "Cancellation time (15 mins) exceeded."
                
        elif order_type == "Pre-order":
            # Rule: Next day before 6 AM
            del_date_str = order_to_cancel["delivery_date"]
            try:
                del_date = datetime.strptime(del_date_str, "%d-%m-%Y")
                if now.date() == del_date.date():
                    if now.hour < 6:
                        can_cancel = True
                    else:
                        fail_reason = "Cannot cancel on Delivery Day after 6:00 AM."
                elif now.date() < del_date.date():
                    can_cancel = True
                else:
                    fail_reason = "Order date passed."
            except:
                can_cancel = False
                fail_reason = "Date error."

        if can_cancel:
            success = database.cancel_order_refund(order_to_cancel["id"], member_id, refund_amt)
            if success:
                # Update coins in local session if possible
                if "member_data" in context.user_data and context.user_data["member_data"]["member_id"] == member_id:
                     context.user_data["member_data"]["coins"] += refund_amt
                     
                new_bal = database.get_member_balance(member_id)
                await update.message.reply_text(
                    "✅ **Order Cancelled Successfully**\n\n"
                    f"🔢 Order ID: {order_to_cancel['id']}\n"
                    f"💰 Refunded: ₹{refund_amt}\n"
                    f"💳 Wallet Balance: ₹{new_bal}\n\n"
                    "Thank you for visiting *Neutrious Theory* 🙏",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Database Error: Could not cancel.")
        else:
            await update.message.reply_text(f"❌ Cancel Failed: {fail_reason}")
            
    except Exception as e:
        logger.error(f"Cancel Error: {e}")
        await update.message.reply_text("❌ An error occurred while processing cancellation.")


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------


def get_application():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found.")
        return None

    application = ApplicationBuilder().token(TOKEN).job_queue(None).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex(r"(?i)^(Hi|Hello|Good)"), start)
        ],
        states={
            PLAN_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plan_selection)],
            MEMBER_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login)],
            MEMBER_SHOPPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_shopping)],
            MEMBER_DELIVERY_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_member_delivery_choice)],
            MEMBER_PREORDER_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_member_preorder_date)],
            NON_MEMBER_SHOPPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_shopping)],
            TAKEAWAY_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_takeaway)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    # Global Handler for Order Cancellation (Outside Conversation)
    application.add_handler(CommandHandler("cancel_order", handle_cancel_last_order))
    application.add_handler(MessageHandler(filters.Regex(r"(?i)cancel order"), handle_cancel_last_order))

    return application

def main():
    application = get_application()
    if application:
        print("Bot is running...")
        application.run_polling()

if __name__ == "__main__":
    main()

