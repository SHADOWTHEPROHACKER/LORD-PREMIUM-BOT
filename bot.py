import json
import re
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8411845557:AAEyDQibkTOQbc3PTT2JW5G0rbNQZ4INNyE"  # <-- put your bot token here
ADMIN_ID = 5917434496
BOT_USERNAME = "lordgivingpremiumbot"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

DATA_FILE = "users.json"

APPS = {
    "YOUTUBE PREMIUM": 20,
    "CRUNCHYROLL PREMIUM": 15,
    "SPOTIFY PREMIUM": 50,
    "AMAZON PRIME": 60,
    "CHAT GPT PLUS": 40,
    "GEMINI PLUS": 50,
    "PREPLEXITY PREMIUM": 25
}

# ---------------- DB ----------------
def load_users():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"__stats__": {"total_topup": 0, "total_withdraws": 0}}

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def ensure_user(user: types.User):
    users = load_users()
    uid = str(user.id)

    if uid not in users:
        users[uid] = {
            "balance": 0,
            "state": None,
            "referred_by": None,
            "referrals": 0,
            "rank": "Bronze",
            "username": user.username or None
        }
    else:
        users[uid]["username"] = user.username or users[uid].get("username")

    save_users(users)
    return users

def update_rank(balance):
    if balance >= 500:
        return "Diamond"
    elif balance >= 200:
        return "Gold"
    elif balance >= 50:
        return "Silver"
    else:
        return "Bronze"

# ---------------- Keyboards ----------------
def main_kb(is_admin=False):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("💰 Balance", "➕ Add Money")
    kb.add("📤 Withdraw", "🏆 Rank")
    kb.add("🏆 Leaderboard", "👥 Refer")
    if is_admin:
        kb.add("👑 Admin Panel")
    return kb

def apps_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for app in APPS:
        kb.add(app)
    kb.add("⬅ Back")
    return kb

# ---------------- Start ----------------
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    ensure_user(message.from_user)
    users = load_users()
    uid = str(message.from_user.id)

    args = message.get_args()
    if args and args in users and users[uid]["referred_by"] is None and args != uid:
        users[uid]["referred_by"] = args
        users[args]["balance"] += 0.5
        users[args]["referrals"] += 1
        save_users(users)
        await bot.send_message(int(args), "🎉 You got ₹0.5 referral bonus!")

    await message.reply("👋 Welcome!", reply_markup=main_kb(message.from_user.id == ADMIN_ID))

# ---------------- User Buttons ----------------
@dp.message_handler(lambda m: m.text == "💰 Balance")
async def balance(message):
    users = load_users()
    u = users[str(message.from_user.id)]
    await message.reply(f"💰 Balance: ₹{u['balance']}")

@dp.message_handler(lambda m: m.text == "🏆 Rank")
async def rank(message):
    users = load_users()
    u = users[str(message.from_user.id)]
    await message.reply(f"🏆 Rank: {u['rank']}\n👥 Referrals: {u['referrals']}")

@dp.message_handler(lambda m: m.text == "🏆 Leaderboard")
async def leaderboard(message):
    users = load_users()
    real_users = [(uid, u) for uid, u in users.items() if uid.isdigit()]
    real_users.sort(key=lambda x: x[1]["balance"], reverse=True)

    text = "🏆 TOP 10 LEADERBOARD\n\n"
    for i, (uid, u) in enumerate(real_users[:10], start=1):
        uname = u.get("username")
        name = f"@{uname}" if uname else f"NoUsername_{uid}"
        text += f"{i}. {name} — ₹{u['balance']}\n"

    if len(real_users) == 0:
        text += "No users yet."

    await message.reply(text)

@dp.message_handler(lambda m: m.text == "👥 Refer")
async def refer(message):
    uid = message.from_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"
    await message.reply(f"🔗 Your link:\n{link}\nEarn ₹0.5 per user!")

# ---------------- Add Money ----------------
@dp.message_handler(lambda m: m.text == "➕ Add Money")
async def add_money(message):
    users = load_users()
    users[str(message.from_user.id)]["state"] = "WAIT_AMOUNT"
    save_users(users)
    await message.reply("💸 How much did you pay?")

# ---------------- Withdraw ----------------
@dp.message_handler(lambda m: m.text == "📤 Withdraw")
async def withdraw(message):
    users = load_users()
    users[str(message.from_user.id)]["state"] = "WAIT_APP"
    save_users(users)
    await message.reply("📦 Select the app:", reply_markup=apps_kb())

# ---------------- Admin Panel ----------------
@dp.message_handler(lambda m: m.text == "👑 Admin Panel")
async def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Statistics", "✏️ Edit Balance")
    kb.add("📢 Broadcast")
    kb.add("⬅ Back")
    await message.reply("👑 Admin Panel", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "📊 Statistics")
async def statistics(message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_users()
    total_users = len([u for u in users if u.isdigit()])
    stats = users.get("__stats__", {"total_topup": 0, "total_withdraws": 0})

    await message.reply(
        f"📊 BOT STATS\n\n"
        f"👥 Users: {total_users}\n"
        f"💰 Total Topup: ₹{stats['total_topup']}\n"
        f"📤 Withdraws: {stats['total_withdraws']}"
    )

@dp.message_handler(lambda m: m.text == "✏️ Edit Balance")
async def edit_balance_start(message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_users()
    users["__admin_state__"] = "WAIT_EDIT_UID"
    save_users(users)
    await message.reply("Send user ID:")

@dp.message_handler(lambda m: m.text == "📢 Broadcast")
async def broadcast_start(message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_users()
    users["__admin_state__"] = "WAIT_BROADCAST"
    save_users(users)
    await message.reply("Send broadcast message:")

@dp.message_handler(lambda m: m.text == "⬅ Back")
async def back(message):
    await message.reply("Back", reply_markup=main_kb(message.from_user.id == ADMIN_ID))

# ---------------- Main Handler ----------------
@dp.message_handler()
async def handler(message: types.Message):
    ensure_user(message.from_user)
    users = load_users()
    uid = str(message.from_user.id)

    # -------- ADMIN STATES --------
    if message.from_user.id == ADMIN_ID and "__admin_state__" in users:
        if users["__admin_state__"] == "WAIT_EDIT_UID":
            if message.text not in users:
                await message.reply("User not found.")
                return
            users["__edit_uid__"] = message.text
            users["__admin_state__"] = "WAIT_EDIT_AMOUNT"
            save_users(users)
            await message.reply("Send new balance:")
            return

        if users["__admin_state__"] == "WAIT_EDIT_AMOUNT":
            if not message.text.isdigit():
                await message.reply("Send number only.")
                return
            newbal = int(message.text)
            edit_uid = users["__edit_uid__"]
            users[edit_uid]["balance"] = newbal
            users[edit_uid]["rank"] = update_rank(newbal)
            users.pop("__admin_state__", None)
            users.pop("__edit_uid__", None)
            save_users(users)
            await message.reply("✅ Balance updated!")
            return

        if users["__admin_state__"] == "WAIT_BROADCAST":
            msg = message.text
            count = 0
            for u in users:
                if u.isdigit():
                    try:
                        await bot.send_message(int(u), msg)
                        count += 1
                    except:
                        pass
            users.pop("__admin_state__", None)
            save_users(users)
            await message.reply(f"✅ Sent to {count} users.")
            return

    # -------- USER STATES --------
    state = users[uid]["state"]

    if state == "WAIT_AMOUNT":
        nums = re.findall(r"\d+", message.text)
        if not nums:
            await message.reply("Send valid amount.")
            return
        amount = int(nums[0])
        users[uid]["state"] = None
        save_users(users)

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✅ ACCEPT", callback_data=f"add_accept:{uid}:{amount}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"add_reject:{uid}:{amount}")
        )

        uname = users[uid].get("username")
        name = f"@{uname}" if uname else f"NoUsername_{uid}"

        await bot.send_message(ADMIN_ID, f"💰 Topup Request\nUser: {name}\nID: {uid}\nAmount: ₹{amount}", reply_markup=kb)
        await message.reply("⏳ Sent for approval.")

    elif state == "WAIT_APP":
        app = message.text.strip()
        if app == "⬅ Back":
            users[uid]["state"] = None
            save_users(users)
            await message.reply("Back", reply_markup=main_kb(message.from_user.id == ADMIN_ID))
            return

        if app not in APPS:
            await message.reply("Select using buttons.")
            return

        price = APPS[app]
        if users[uid]["balance"] < price:
            await message.reply("Not enough balance.")
            return

        users[uid]["state"] = None
        save_users(users)

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✅ APPROVE", callback_data=f"wd_accept:{uid}:{app.replace(' ', '_')}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"wd_reject:{uid}:{app.replace(' ', '_')}")
        )

        uname = users[uid].get("username")
        name = f"@{uname}" if uname else f"NoUsername_{uid}"

        await bot.send_message(
            ADMIN_ID,
            f"📤 Withdraw Request\nUser: {name}\nID: {uid}\nApp: {app}\nPrice: ₹{price}",
            reply_markup=kb
        )

        await message.reply("⏳ Withdraw request sent.")

# ---------------- Callbacks ----------------
@dp.callback_query_handler(lambda c: True)
async def callbacks(call: types.CallbackQuery):
    users = load_users()
    data = call.data

    # Top-up callbacks
    if data.startswith("add_accept"):
        _, uid, amount = data.split(":")
        amount = int(amount)
        users[uid]["balance"] += amount
        users[uid]["rank"] = update_rank(users[uid]["balance"])
        users["__stats__"]["total_topup"] += amount
        save_users(users)
        await bot.send_message(int(uid), f"✅ ₹{amount} added to your wallet!")
        await call.message.edit_reply_markup(None)
        await call.answer("Topup Accepted")

    elif data.startswith("add_reject"):
        _, uid, amount = data.split(":")
        await bot.send_message(int(uid), "❌ Your topup was rejected.")
        await call.message.edit_reply_markup(None)
        await call.answer("Topup Rejected")

    # Withdraw callbacks
    elif data.startswith("wd_"):
        try:
            action, uid, app_safe = data.split(":")
            app = app_safe.replace("_", " ")
            price = APPS[app]
        except:
            await call.answer("Error processing request.", show_alert=True)
            return

        if action == "wd_accept":
            if users[uid]["balance"] < price:
                await call.message.edit_text("❌ Insufficient balance.")
                await call.answer()
                return
            users[uid]["balance"] -= price
            users[uid]["rank"] = update_rank(users[uid]["balance"])
            users["__stats__"]["total_withdraws"] += 1
            save_users(users)
            await bot.send_message(int(uid), f"✅ Your {app} approved!")
            await call.message.edit_reply_markup(None)
            await call.answer("Withdraw Approved")

        elif action == "wd_reject":
            await bot.send_message(int(uid), f"❌ Your {app} was rejected.")
            await call.message.edit_reply_markup(None)
            await call.answer("Withdraw Rejected")

# ---------------- Start ----------------
if __name__ == "__main__":
    print("Bot running...")
    executor.start_polling(dp, skip_updates=True)
