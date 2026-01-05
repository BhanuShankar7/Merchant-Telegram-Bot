# Merchant Demo Bot

This is a demo Telegram bot for a food merchant, built with **Python** and **python-telegram-bot**.

## Features
- **User Verification**: Distinguishes between Members and Non-Members.
- **Membership Validation**: Checks against a hardcoded list of valid IDs.
- **Dynamic Menu**: Shows discounted prices (10% off) for members.
- **Shopping Cart**: Allows users to select items and specify quantities.
- **Bill Generation**: Calculates subtotal, discounts, and final payable amount.

## Prerequisites
- Python 3.7 or higher.
- A Telegram Bot Token (obtained from [@BotFather](https://t.me/BotFather)).

## Valid Membership IDs (for testing)
- 97011
- 77452
- 63054
- 60053
- 73373
- 12325

## Setup and Run

1. **Install Dependencies**
   Open your terminal in this directory and run:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Token**
   Open `bot.py` in a text editor.
   Find the line:
   ```python
   TOKEN = "YOUR_BOT_TOKEN_HERE"
   ```
   Replace `YOUR_BOT_TOKEN_HERE` with your actual Telegram Bot Token.

3. **Run the Bot**
   Execute the script:
   ```bash
   python bot.py
   ```

4. **Interact**
   Open your bot in Telegram and send `/start`, `Hi`, or `Hello`.
"# Merchant-Telegram-Bot" 
