import os
import sys
import time
import io
import asyncio
import aiosqlite
import qrcode
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile

# ==============================================================
# CONFIGURATION
# ==============================================================
MASTER_BOT_TOKEN = "8841139690:AAFeUI5_9Yi9zgG1QinCytzZK_J0cA3rWWs"
OWNER_ID = 6914205738
DB_NAME = "bot_data.db"
TEMPLATES_DIR = "templates_storage"

os.makedirs(TEMPLATES_DIR, exist_ok=True)

bot = Bot(
    token=MASTER_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

ACTIVE_PROCESSES = {}

# ==============================================================
# CUSTOM TELEGRAM PREMIUM EMOJIS (FROM YOUR GIVEN IDs)
# ==============================================================
E = {
    "BOT": '<tg-emoji emoji-id="6082408856393099293">🤖</tg-emoji>',
    "STAR": '<tg-emoji emoji-id="6086924086791902713">🌟</tg-emoji>',
    "ROCKET": '<tg-emoji emoji-id="5780773956030043338">🚀</tg-emoji>',
    "BRAIN": '<tg-emoji emoji-id="6282648430825182490">🧠</tg-emoji>',
    "CHECK": '<tg-emoji emoji-id="6089418114171147667">✅</tg-emoji>',
    "CROSS": '<tg-emoji emoji-id="5785177332595561481">❌</tg-emoji>',
    "WARN": '<tg-emoji emoji-id="6089079808187174973">⚠️</tg-emoji>',
    "MONEY": '<tg-emoji emoji-id="6089104607328342288">💰</tg-emoji>',
    "CASH": '<tg-emoji emoji-id="6030734193594470413">💵</tg-emoji>',
    "GIFT": '<tg-emoji emoji-id="6093780439439249308">🎁</tg-emoji>',
    "CROWN": '<tg-emoji emoji-id="6089003761496232797">👑</tg-emoji>',
    "FOLDER": '<tg-emoji emoji-id="6093612746736145083">📁</tg-emoji>',
    "PACKAGE": '<tg-emoji emoji-id="5780560530515171033">🛍</tg-emoji>',
    "FIRE": '<tg-emoji emoji-id="6086954744268460848">🔥</tg-emoji>',
    "SPARKLE": '<tg-emoji emoji-id="6285088169817805553">✨</tg-emoji>',
    "DIAMOND": '<tg-emoji emoji-id="6086778246882399112">💎</tg-emoji>',
    "STATS": '<tg-emoji emoji-id="6093382540784046658">📊</tg-emoji>',
    "CHANNEL": '<tg-emoji emoji-id="6095891759462617671">📢</tg-emoji>',
    "FLASH": '<tg-emoji emoji-id="6087079590377820415">⚡</tg-emoji>',
    "TAG": '<tg-emoji emoji-id="6093890429256732821">🔖</tg-emoji>',
    "USER": '<tg-emoji emoji-id="6089024570612781324">👤</tg-emoji>',
    "ONLINE": '<tg-emoji emoji-id="6032975852990370635">🟢</tg-emoji>',
    "OFFLINE": '<tg-emoji emoji-id="6032707305865220377">🔴</tg-emoji>',
    "MAGIC": '<tg-emoji emoji-id="6285088169817805553">🪄</tg-emoji>',
    "CARD": '<tg-emoji emoji-id="6093612746736145083">💳</tg-emoji>',
    "GEAR": '<tg-emoji emoji-id="5780517739756000213">⚙️</tg-emoji>',
    "ONE": '<tg-emoji emoji-id="6089206028686070348">1️⃣</tg-emoji>',
    "TWO": '<tg-emoji emoji-id="6089206028686070348">2️⃣</tg-emoji>',
    "PIN": '<tg-emoji emoji-id="6089019283508040459">📌</tg-emoji>',
    "LOCK": '<tg-emoji emoji-id="6282846669335702032">🔒</tg-emoji>',
    "BELL": '<tg-emoji emoji-id="6093852083788715042">🔔</tg-emoji>'
}

# ==============================================================
# BUTTON CREATOR HELPER
# ==============================================================
def styled_btn(text: str, callback_data: str, style: str = "primary", url: str = None) -> InlineKeyboardButton:
    if url:
        return InlineKeyboardButton(text=text, url=url)
    return InlineKeyboardButton(text=text, callback_data=callback_data)

# ==============================================================
# DATABASE SETUP
# ==============================================================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                balance REAL DEFAULT 0.0,
                is_banned INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS force_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                name TEXT NOT NULL,
                invite_link TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                file_path TEXT NOT NULL,
                price REAL DEFAULT 0.0,
                banner_file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS gift_codes (
                code TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                max_uses INTEGER NOT NULL,
                used_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS redeemed_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                amount REAL NOT NULL,
                redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, code)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                bot_username TEXT NOT NULL,
                template_id INTEGER NOT NULL,
                is_running INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE
            )
        """)
        await db.commit()

# --- Helpers ---
async def is_admin(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,)) as cur:
            return (await cur.fetchone()) is not None

async def is_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return bool(row[0]) if row else False

async def get_user_balance(user_id: int) -> float:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return float(row[0]) if row else 0.0

async def update_balance(user_id: int, amount: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def get_setting(key: str, default: str = "") -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else default

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()

# ==============================================================
# FORCE JOIN CHANNELS CHECK
# ==============================================================
async def check_force_sub(user_id: int) -> tuple[bool, list]:
    if await is_admin(user_id):
        return True, []
        
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM force_channels") as cur:
            channels = await cur.fetchall()

    if not channels:
        return True, []

    unjoined = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["channel_id"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                unjoined.append(ch)
        except Exception:
            unjoined.append(ch)

    return (len(unjoined) == 0), unjoined

def get_force_sub_keyboard(unjoined_channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in unjoined_channels:
        buttons.append([styled_btn(f"Join: {ch['name']}", "", style="primary", url=ch["invite_link"])])
    buttons.append([styled_btn("Verify Membership", "verify_force_sub", style="success")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==============================================================
# DYNAMIC UPI QR GENERATOR
# ==============================================================
def generate_upi_qr(upi_id: str, amount: float, note: str = "Wallet Deposit") -> io.BytesIO:
    upi_url = f"upi://pay?pa={upi_id}&pn=ProBotControl&am={amount:.2f}&cu=INR&tn={note}"
    qr = qrcode.QRCode(version=1, box_size=10, border=3)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio

# ==============================================================
# SUBPROCESS CONTROLLER
# ==============================================================
async def start_bot_process(bot_id: int, file_path: str, token: str, owner_id: int):
    if bot_id in ACTIVE_PROCESSES:
        await stop_bot_process(bot_id)

    if not os.path.exists(file_path):
        print(f"[-] Error: Script file not found: {file_path}")
        return False

    try:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["BOT_TOKEN"] = token
        env["BOT_OWNER_ID"] = str(owner_id)

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            file_path,
            token,
            str(owner_id),
            env=env,
            stdout=None,
            stderr=None
        )
        ACTIVE_PROCESSES[bot_id] = process
        print(f"[+] Child bot #{bot_id} online (PID: {process.pid})")
        return True
    except Exception as e:
        print(f"[-] Error starting bot #{bot_id}: {e}")
        return False

async def stop_bot_process(bot_id: int):
    if bot_id in ACTIVE_PROCESSES:
        proc = ACTIVE_PROCESSES[bot_id]
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=3.0)
        except Exception:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
        del ACTIVE_PROCESSES[bot_id]
        print(f"[*] Child bot #{bot_id} stopped.")

async def restore_all_bots():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT ub.id, ub.token, ub.owner_id, ub.is_running, t.file_path 
            FROM user_bots ub
            JOIN templates t ON ub.template_id = t.id
            WHERE ub.is_running = 1
        """) as cur:
            bots = await cur.fetchall()
            for b in bots:
                if os.path.exists(b["file_path"]):
                    await start_bot_process(b["id"], b["file_path"], b["token"], b["owner_id"])
    print(f"[*] Total active child bots restored: {len(ACTIVE_PROCESSES)}")

# ==============================================================
# UI MENUS & MAIN DASHBOARD
# ==============================================================
def get_main_menu(is_adm: bool = False):
    keyboard = [
        [
            styled_btn("My Profile", "btn_profile", style="primary"),
            styled_btn("Redeem Code", "btn_redeem_code", style="success")
        ],
        [
            styled_btn("Create New Bot", "btn_new_bot", style="success"),
            styled_btn("My Hosted Bots", "btn_my_bots", style="primary")
        ],
        [
            styled_btn("Help & Guide", "btn_help", style="primary")
        ]
    ]
    if is_adm:
        keyboard.append([styled_btn("Admin Panel", "admin_panel", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

MAIN_BANNER_TEXT = (
    f"{E['STAR']} <i><b>Welcome to the Bot Hosting & Control Center</b></i>\n\n"
    f"{E['ROCKET']} <i><b>Design • Deploy • Manage your Telegram bots with high speed.</b></i>\n\n"
    f"{E['BRAIN']} <i>Smart cloud tools, clean interface, and 24/7 continuous uptime.</i>\n\n"
    f"{E['PIN']} <i>Please choose an option below to continue:</i>"
)

async def send_welcome_dashboard(chat_id: int, old_message: types.Message = None):
    if old_message:
        try:
            await old_message.delete()
        except Exception:
            pass

    is_adm = await is_admin(chat_id)
    welcome_photo = await get_setting("welcome_photo_id")
    kb = get_main_menu(is_adm)

    if welcome_photo:
        try:
            await bot.send_photo(chat_id=chat_id, photo=welcome_photo, caption=MAIN_BANNER_TEXT, reply_markup=kb)
            return
        except Exception:
            pass

    await bot.send_message(chat_id=chat_id, text=MAIN_BANNER_TEXT, reply_markup=kb)

# ==============================================================
# FSM STATES
# ==============================================================
class UserStates(StatesGroup):
    selecting_category = State()
    waiting_token = State()
    deposit_amount = State()
    deposit_screenshot = State()
    redeem_code = State()

class AdminStates(StatesGroup):
    add_funds_user = State()
    add_funds_amt = State()
    debit_funds_user = State()
    debit_funds_amt = State()
    ban_user = State()
    unban_user = State()
    add_admin = State()
    del_admin = State()
    add_ch_id = State()
    add_ch_name = State()
    add_ch_link = State()
    set_upi = State()
    set_welcome_photo = State()
    broadcast_msg = State()
    add_category_name = State()
    tpl_category = State()
    tpl_name = State()
    tpl_desc = State()
    tpl_price = State()
    tpl_banner = State()
    tpl_file = State()
    edit_tpl_price = State()
    gift_name = State()
    gift_amount = State()
    gift_max_uses = State()

# ==============================================================
# GLOBAL CANCEL HANDLER
# ==============================================================
@dp.message(Command("cancel"))
async def cancel_action(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(f"{E['CROSS']} <i>Action has been cancelled.</i>")
    await send_welcome_dashboard(message.from_user.id)

# ==============================================================
# START & MEMBERSHIP VERIFICATION
# ==============================================================
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id

    if await is_banned(user_id):
        await message.answer(f"{E['CROSS']} <i><b>You have been banned from accessing this platform.</b></i>")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET username=?, full_name=?
        """, (user_id, message.from_user.username or "N/A", message.from_user.full_name, message.from_user.username or "N/A", message.from_user.full_name))
        await db.commit()

    is_joined, unjoined = await check_force_sub(user_id)
    if not is_joined:
        await message.answer(
            f"{E['WARN']} <i><b>Please join our official channels to unlock access:</b></i>",
            reply_markup=get_force_sub_keyboard(unjoined)
        )
        return

    await send_welcome_dashboard(user_id)

@dp.callback_query(F.data == "verify_force_sub")
async def verify_force_sub(call: types.CallbackQuery):
    is_joined, unjoined = await check_force_sub(call.from_user.id)
    if is_joined:
        await send_welcome_dashboard(call.from_user.id, call.message)
    else:
        await call.answer("You have not joined all the required channels yet.", show_alert=True)

@dp.callback_query(F.data == "main_menu")
async def back_to_main(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await send_welcome_dashboard(call.from_user.id, call.message)

# ==============================================================
# USER GIFT CODE REDEMPTION
# ==============================================================
@dp.callback_query(F.data == "btn_redeem_code")
async def ask_redeem_code(call: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Cancel", "main_menu", style="danger")]])
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        f"{E['GIFT']} <i><b>Redeem Gift or Promotional Code</b></i>\n\n"
        f"<i>Please type and send your gift code below:</i>",
        reply_markup=kb
    )
    await state.set_state(UserStates.redeem_code)

@dp.message(UserStates.redeem_code)
async def process_gift_redemption(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    code_input = message.text.strip().upper()
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM gift_codes WHERE code = ?", (code_input,)) as cur:
            gift = await cur.fetchone()

        if not gift:
            await message.answer(f"{E['CROSS']} <i><b>Invalid Code!</b> Please enter a valid code or send /cancel.</i>")
            return

        if gift["used_count"] >= gift["max_uses"]:
            await message.answer(f"{E['WARN']} <i><b>This gift code has reached its maximum usage limit!</b></i>")
            await state.clear()
            return

        async with db.execute("SELECT id FROM redeemed_codes WHERE user_id = ? AND code = ?", (user_id, code_input)) as cur:
            already = await cur.fetchone()
            if already:
                await message.answer(f"{E['WARN']} <i><b>You have already claimed this gift code!</b></i>")
                await state.clear()
                return

        amount = gift["amount"]
        await db.execute("INSERT INTO redeemed_codes (user_id, code, amount) VALUES (?, ?, ?)", (user_id, code_input, amount))
        await db.execute("UPDATE gift_codes SET used_count = used_count + 1 WHERE code = ?", (code_input,))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [styled_btn("View Profile", "btn_profile", style="success")],
        [styled_btn("Main Menu", "main_menu", style="primary")]
    ])
    await message.answer(
        f"{E['SPARKLE']} <i><b>Gift Code Successfully Redeemed!</b></i>\n\n"
        f"{E['MONEY']} <i>An amount of <b>₹{amount:.2f}</b> has been credited to your balance.</i>\n"
        f"{E['TAG']} <i>Code: <code>{code_input}</code></i>",
        reply_markup=kb
    )

# ==============================================================
# CREATE / CLONE BOT FLOW
# ==============================================================
@dp.callback_query(F.data == "btn_new_bot")
async def new_bot_start(call: types.CallbackQuery, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, name FROM categories") as cur:
            categories = await cur.fetchall()

    if not categories:
        await call.answer("No categories available at the moment.", show_alert=True)
        return

    buttons = []
    for cat in categories:
        buttons.append([styled_btn(f"{cat['name']}", f"user_cat_{cat['id']}", style="primary")])
    buttons.append([styled_btn("Cancel", "main_menu", style="danger")])

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['ROCKET']} <i><b>Select Bot Category</b></i>\n\n"
        f"<i>Please choose a category from the options below:</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(UserStates.selecting_category)

@dp.callback_query(UserStates.selecting_category, F.data.startswith("user_cat_"))
async def show_templates_in_category(call: types.CallbackQuery, state: FSMContext):
    cat_id = int(call.data.replace("user_cat_", ""))

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, name, price FROM templates WHERE category_id = ?", (cat_id,)) as cur:
            templates = await cur.fetchall()

    if not templates:
        await call.answer("There are no bot templates in this category yet.", show_alert=True)
        return

    buttons = []
    for tpl in templates:
        badge = "FREE" if tpl["price"] == 0 else f"₹{tpl['price']}"
        style_type = "success" if tpl["price"] == 0 else "primary"
        buttons.append([styled_btn(f"{tpl['name']} [{badge}]", f"show_tpl_{tpl['id']}", style=style_type)])
    
    buttons.append([styled_btn("Back to Categories", "btn_new_bot", style="danger")])

    bot_list_header = (
        f"{E['BOT']} <i><b>Available Bot Templates</b></i>\n\n"
        f"{E['SPARKLE']} <i><b>Create • Clone • Deploy your bots easily.</b></i>\n\n"
        f"{E['GEAR']} <i>Select a template below to inspect details:</i>"
    )

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        bot_list_header,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data.startswith("show_tpl_"))
async def show_template_guide_card(call: types.CallbackQuery, state: FSMContext):
    template_id = int(call.data.replace("show_tpl_", ""))

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM templates WHERE id = ?", (template_id,)) as cur:
            tpl = await cur.fetchone()

    if not tpl:
        await call.answer("Template not found.", show_alert=True)
        return

    await state.update_data(selected_template_id=template_id, template_name=tpl["name"], template_price=tpl["price"])

    price_str = "FREE (₹0)" if tpl["price"] == 0 else f"₹{tpl['price']:.2f}"

    guide_caption = (
        f"{E['BOT']} <i><b>Bot Connection Setup</b></i>\n\n"
        f"{E['TAG']} <i><b>Title:</b> {tpl['name']}</i>\n"
        f"{E['MONEY']} <i><b>Price:</b> <code>{price_str}</code></i>\n\n"
        f"{E['MAGIC']} <i><b>Setup Instructions:</b></i>\n"
        f"{E['ONE']} <i>Open @BotFather and create a new bot.</i>\n"
        f"{E['TWO']} <i>Copy the API Token received.</i>\n\n"
        f"{E['PIN']} <i><b>Features:</b></i>\n<i>{tpl['description']}</i>\n\n"
        f"<i>To cancel anytime, send: /cancel</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [styled_btn("Connect This Bot", "proceed_connect_bot", style="success")],
        [styled_btn("Back", f"user_cat_{tpl['category_id']}", style="danger")]
    ])

    try:
        await call.message.delete()
    except Exception:
        pass

    if tpl["banner_file_id"]:
        await call.message.answer_photo(
            photo=tpl["banner_file_id"],
            caption=guide_caption,
            reply_markup=kb
        )
    else:
        await call.message.answer(guide_caption, reply_markup=kb)

@dp.callback_query(F.data == "proceed_connect_bot")
async def ask_token_for_template(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tpl_name = data.get("template_name", "Bot")
    tpl_price = data.get("template_price", 0.0)

    user_id = call.from_user.id
    balance = await get_user_balance(user_id)

    if tpl_price > 0 and balance < tpl_price:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Deposit Funds", "wallet_deposit", style="success")],
            [styled_btn("Cancel", "main_menu", style="danger")]
        ])
        await call.message.answer(
            f"{E['CROSS']} <i><b>Insufficient Balance!</b></i>\n\n"
            f"<i>Required: <b>₹{tpl_price:.2f}</b></i>\n"
            f"<i>Current Balance: <b>₹{balance:.2f}</b></i>\n\n"
            f"<i>Please top up your wallet balance to continue.</i>",
            reply_markup=kb
        )
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Cancel", "main_menu", style="danger")]])
    await call.message.answer(
        f"{E['BOT']} <i><b>Selected Template:</b> <code>{tpl_name}</code></i>\n\n"
        f"<i>Please paste and send your Telegram Bot <b>API Token</b> below:</i>",
        reply_markup=kb
    )
    await state.set_state(UserStates.waiting_token)

@dp.message(UserStates.waiting_token)
async def process_user_token_and_deploy(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    token = message.text.strip()
    user_id = message.from_user.id

    temp_bot = None
    try:
        temp_bot = Bot(token=token)
        bot_info = await temp_bot.get_me()
    except Exception:
        await message.answer(f"{E['CROSS']} <i><b>Invalid Token!</b> Please provide a valid bot token from @BotFather:</i>")
        return
    finally:
        if temp_bot:
            await temp_bot.session.close()

    data = await state.get_data()
    template_id = data.get("selected_template_id")

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT name, file_path, price FROM templates WHERE id = ?", (template_id,)) as cur:
            tpl = await cur.fetchone()

    if not tpl:
        await message.answer(f"{E['CROSS']} <i>Error: Template configuration not found.</i>")
        await state.clear()
        return

    price = tpl["price"]
    balance = await get_user_balance(user_id)

    if price > 0:
        if balance < price:
            await message.answer(f"{E['CROSS']} <i>Insufficient balance (Price: ₹{price}, Balance: ₹{balance}).</i>")
            await state.clear()
            return
        await update_balance(user_id, -price)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO user_bots (owner_id, token, bot_username, template_id, is_running)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(token) DO UPDATE SET is_running = 1, template_id = ?, owner_id = ?
        """, (user_id, token, bot_info.username, template_id, template_id, user_id))
        await db.commit()
        
        async with db.execute("SELECT id FROM user_bots WHERE token = ?", (token,)) as cur:
            row = await cur.fetchone()
            bot_id = row[0]

    started = await start_bot_process(bot_id, tpl["file_path"], token, user_id)
    await state.clear()

    if started:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("My Hosted Bots", "btn_my_bots", style="success")],
            [styled_btn("Main Menu", "main_menu", style="primary")]
        ])
        await message.answer(
            f"{E['SPARKLE']} <i><b>Congratulations! Your bot is live!</b></i>\n\n"
            f"{E['BOT']} <i><b>Bot:</b> @{bot_info.username}</i>\n"
            f"{E['PACKAGE']} <i><b>Template:</b> <code>{tpl['name']}</code></i>\n"
            f"{E['MONEY']} <i><b>Fee:</b> <code>₹{price:.2f}</code></i>\n"
            f"{E['ONLINE']} <i><b>Status:</b> <code>Online & Running 24/7</code> {E['FLASH']}</i>",
            reply_markup=kb
        )
    else:
        await message.answer(f"{E['WARN']} <i>Bot recorded, but process launch encountered an error. Check server logs.</i>")

# ==============================================================
# MY BOTS MANAGER
# ==============================================================
@dp.callback_query(F.data == "btn_my_bots")
async def show_my_bots_list(call: types.CallbackQuery):
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT ub.id, ub.bot_username, ub.is_running, t.name as tpl_name
            FROM user_bots ub
            JOIN templates t ON ub.template_id = t.id
            WHERE ub.owner_id = ?
            ORDER BY ub.id DESC
        """, (user_id,)) as cur:
            bots = await cur.fetchall()

    if not bots:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Create New Bot", "btn_new_bot", style="success")],
            [styled_btn("Main Menu", "main_menu", style="primary")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(
            f"{E['PACKAGE']} <i><b>Hosted Bots Manager</b></i>\n\n"
            f"{E['CROSS']} <i>You do not have any active hosted bots currently.</i>",
            reply_markup=kb
        )
        return

    buttons = []
    for b in bots:
        is_live = (b["id"] in ACTIVE_PROCESSES) and (b["is_running"] == 1)
        btn_style = "success" if is_live else "danger"
        status_tag = "ONLINE" if is_live else "STOPPED"
        btn_text = f"@{b['bot_username']} [{status_tag}]"
        buttons.append([styled_btn(btn_text, f"open_bot_{b['id']}", style=btn_style)])

    buttons.append([styled_btn("Deploy Another Bot", "btn_new_bot", style="primary")])
    buttons.append([styled_btn("Main Menu", "main_menu", style="danger")])

    text = (
        f"{E['BOT']} <i><b>My Hosted Bots</b></i>\n\n"
        f"<i>Select any bot below to manage power state, restart, or delete:</i>"
    )

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("open_bot_"))
async def open_single_bot_controller(call: types.CallbackQuery):
    bot_id = int(call.data.replace("open_bot_", ""))
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT ub.id, ub.token, ub.bot_username, ub.is_running, ub.created_at, t.name as tpl_name
            FROM user_bots ub
            JOIN templates t ON ub.template_id = t.id
            WHERE ub.id = ? AND ub.owner_id = ?
        """, (bot_id, user_id)) as cur:
            bot_item = await cur.fetchone()

    if not bot_item:
        await call.answer("Bot record not found.", show_alert=True)
        return

    is_live = (bot_id in ACTIVE_PROCESSES) and (bot_item["is_running"] == 1)
    status_text = "ONLINE & RUNNING" if is_live else "STOPPED / OFFLINE"
    dot_icon = E['ONLINE'] if is_live else E['OFFLINE']

    if is_live:
        toggle_btn = styled_btn("Stop Bot", f"botact_stop_{bot_id}", style="danger")
    else:
        toggle_btn = styled_btn("Start Bot", f"botact_start_{bot_id}", style="success")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [styled_btn("Restart Bot", f"botact_restart_{bot_id}", style="primary")],
        [toggle_btn],
        [styled_btn("Delete Bot", f"botact_confirm_del_{bot_id}", style="danger")],
        [
            styled_btn("My Bots", "btn_my_bots", style="primary"),
            styled_btn("Main Menu", "main_menu", style="danger")
        ]
    ])

    token_preview = bot_item['token'][:10] + "..." + bot_item['token'][-4:]

    text = (
        f"{E['BOT']} <i><b>Bot Control Dashboard</b></i>\n\n"
        f"• <i><b>Username:</b> @{bot_item['bot_username']}</i>\n"
        f"• <i><b>Template:</b> <code>{bot_item['tpl_name']}</code></i>\n"
        f"• <i><b>Status:</b> {dot_icon} <code>{status_text}</code></i>\n"
        f"• <i><b>Token:</b> <code>{token_preview}</code></i>\n"
        f"• <i><b>Created:</b> <code>{bot_item['created_at'][:19]}</code></i>"
    )

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("botact_"))
async def execute_bot_actions(call: types.CallbackQuery):
    data_parts = call.data.replace("botact_", "").split("_")
    action = data_parts[0]
    bot_id = int(data_parts[-1])
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT ub.*, t.file_path, t.name as tpl_name FROM user_bots ub
            JOIN templates t ON ub.template_id = t.id
            WHERE ub.id = ? AND ub.owner_id = ?
        """, (bot_id, user_id)) as cur:
            bot_data = await cur.fetchone()

    if not bot_data:
        await call.answer("Bot record not found.", show_alert=True)
        return

    if action == "restart":
        await stop_bot_process(bot_id)
        await start_bot_process(bot_id, bot_data["file_path"], bot_data["token"], user_id)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE user_bots SET is_running = 1 WHERE id = ?", (bot_id,))
            await db.commit()
        await call.answer("Bot restarted successfully.", show_alert=True)

    elif action == "stop":
        await stop_bot_process(bot_id)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE user_bots SET is_running = 0 WHERE id = ?", (bot_id,))
            await db.commit()
        await call.answer("Bot stopped.", show_alert=True)

    elif action == "start":
        await start_bot_process(bot_id, bot_data["file_path"], bot_data["token"], user_id)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE user_bots SET is_running = 1 WHERE id = ?", (bot_id,))
            await db.commit()
        await call.answer("Bot started and online.", show_alert=True)

    elif action == "confirm":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Yes, Delete Permanently", f"botact_dodelete_{bot_id}", style="danger")],
            [styled_btn("Cancel", f"open_bot_{bot_id}", style="success")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(
            f"{E['WARN']} <i><b>Are you sure you want to delete @{bot_data['bot_username']}?</b></i>\n\n"
            f"<i>This bot instance will be stopped and removed permanently.</i>",
            reply_markup=kb
        )
        return

    elif action == "dodelete":
        await stop_bot_process(bot_id)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("DELETE FROM user_bots WHERE id = ? AND owner_id = ?", (bot_id, user_id))
            await db.commit()
        await call.answer("Bot removed permanently.", show_alert=True)
        await show_my_bots_list(call)
        return

    await open_single_bot_controller(call)

# ==============================================================
# PROFILE & WALLET SYSTEM
# ==============================================================
@dp.callback_query(F.data == "btn_profile")
async def show_profile_wallet(call: types.CallbackQuery):
    user_id = call.from_user.id
    balance = await get_user_balance(user_id)

    profile_text = (
        f"{E['USER']} <i><b>Account:</b> {call.from_user.full_name}</i>\n"
        f"{E['TAG']} <i><b>User ID:</b> <code>{user_id}</code></i>\n\n"
        f"{E['MONEY']} <i><b>Current Balance:</b></i>\n"
        f"<i><b>₹{balance:.2f}</b></i>\n\n"
        f"<i>Use the options below to manage your wallet balance:</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            styled_btn("Deposit Funds", "wallet_deposit", style="success"),
            styled_btn("Redeem Code", "btn_redeem_code", style="primary")
        ],
        [styled_btn("Main Menu", "main_menu", style="danger")]
    ])

    try:
        user_photos = await bot.get_user_profile_photos(user_id, limit=1)
        if user_photos.total_count > 0:
            photo_file_id = user_photos.photos[0][-1].file_id
            await call.message.delete()
            await call.message.answer_photo(photo=photo_file_id, caption=profile_text, reply_markup=kb)
            return
    except Exception:
        pass

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(profile_text, reply_markup=kb)

@dp.callback_query(F.data == "wallet_deposit")
async def ask_deposit_amount(call: types.CallbackQuery, state: FSMContext):
    admin_upi = await get_setting("admin_upi")
    if not admin_upi:
        await call.answer("UPI ID not configured yet. Please contact admin.", show_alert=True)
        return

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        f"{E['CASH']} <i><b>Enter Deposit Amount (₹):</b></i>\n\n<i>(e.g., 50, 100, 200, 500)</i>"
    )
    await state.set_state(UserStates.deposit_amount)

@dp.message(UserStates.deposit_amount)
async def process_deposit_amount(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric amount:</i>")
        return

    admin_upi = await get_setting("admin_upi")
    
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("INSERT INTO deposits (user_id, amount, status) VALUES (?, ?, 'PENDING')", (message.from_user.id, amount))
        await db.commit()
        dep_id = cur.lastrowid

    await state.update_data(dep_id=dep_id, amount=amount)

    qr_io = generate_upi_qr(admin_upi, amount, f"Wallet-Dep-{message.from_user.id}")
    qr_file = BufferedInputFile(qr_io.read(), filename="qr.png")

    caption = (
        f"{E['CARD']} <i><b>Add Funds Via UPI QR</b></i>\n\n"
        f"• <i><b>Amount:</b> <code>₹{amount:.2f}</code></i>\n"
        f"• <i><b>UPI ID:</b> <code>{admin_upi}</code></i>\n\n"
        f"{E['PIN']} <i><b>Instructions:</b></i>\n"
        f"<i>1. Scan the QR code with any UPI app to pay.</i>\n"
        f"<i>2. After paying, click 'Send Screenshot' to send proof.</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [styled_btn("Send Screenshot", "deposit_send_ss", style="success")],
        [styled_btn("Cancel", "main_menu", style="danger")]
    ])

    await message.answer_photo(photo=qr_file, caption=caption, reply_markup=kb)

@dp.callback_query(F.data == "deposit_send_ss")
async def prompt_screenshot(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(f"{E['PIN']} <i><b>Please upload your payment screenshot (Photo) now:</b></i>")
    await state.set_state(UserStates.deposit_screenshot)

@dp.message(UserStates.deposit_screenshot, F.photo)
async def handle_deposit_screenshot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    dep_id = data.get("dep_id")
    amount = data.get("amount")

    if not dep_id:
        await message.answer(f"{E['CROSS']} <i>Session expired. Please restart deposit.</i>")
        await state.clear()
        return

    photo_id = message.photo[-1].file_id

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            styled_btn("Approve Funds", f"adm_dep_app_{dep_id}", style="success"),
            styled_btn("Reject", f"adm_dep_rej_{dep_id}", style="danger")
        ]
    ])

    admin_caption = (
        f"{E['FLASH']} <i><b>New Deposit Request</b></i>\n\n"
        f"• <i><b>ID:</b> <code>#{dep_id}</code></i>\n"
        f"• <i><b>User:</b> {message.from_user.full_name} (<code>{message.from_user.id}</code>)</i>\n"
        f"• <i><b>Amount:</b> <code>₹{amount:.2f}</code></i>"
    )

    try:
        await bot.send_photo(chat_id=OWNER_ID, photo=photo_id, caption=admin_caption, reply_markup=admin_kb)
    except Exception as e:
        print(f"[Error] Failed to forward payment proof: {e}")

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Main Menu", "main_menu", style="primary")]])
    await message.answer(
        f"{E['CHECK']} <i><b>Screenshot received!</b> Administrators will verify and credit your wallet.</i>",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("adm_dep_"))
async def process_deposit_decision(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        return

    parts = call.data.replace("adm_dep_", "").split("_")
    action, dep_id = parts[0], int(parts[1])

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM deposits WHERE id = ?", (dep_id,)) as cur:
            deposit = await cur.fetchone()

    if not deposit or deposit["status"] != "PENDING":
        await call.answer("Deposit already processed.", show_alert=True)
        return

    if action == "app":
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE deposits SET status = 'APPROVED' WHERE id = ?", (dep_id,))
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (deposit["amount"], deposit["user_id"]))
            await db.commit()

        await call.message.edit_caption(
            caption=f"{call.message.caption}\n\n{E['ONLINE']} <i><b>Status: Approved (+₹{deposit['amount']} Credited)</b></i>",
            reply_markup=None
        )

        try:
            await bot.send_message(
                chat_id=deposit["user_id"],
                text=f"{E['SPARKLE']} <i><b>Deposit Approved!</b> <code>₹{deposit['amount']:.2f}</code> has been credited to your balance.</i>"
            )
        except Exception:
            pass

        await call.answer("Deposit approved.", show_alert=True)

    elif action == "rej":
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE deposits SET status = 'REJECTED' WHERE id = ?", (dep_id,))
            await db.commit()

        await call.message.edit_caption(
            caption=f"{call.message.caption}\n\n{E['OFFLINE']} <i><b>Status: Rejected</b></i>",
            reply_markup=None
        )

        try:
            await bot.send_message(
                chat_id=deposit["user_id"],
                text=f"{E['CROSS']} <i><b>Deposit Rejected!</b> Verification was unsuccessful. Please check proof or contact admin.</i>"
            )
        except Exception:
            pass

        await call.answer("Deposit rejected.", show_alert=True)

@dp.callback_query(F.data == "btn_help")
async def show_help(call: types.CallbackQuery):
    text = (
        f"{E['WARN']} <i><b>Help & Documentation Guide</b></i>\n\n"
        f"<i>1. Open @BotFather to create a bot and get an API Token.</i>\n"
        f"<i>2. Use 'Create New Bot' to select a template and connect.</i>\n"
        f"<i>3. Use 'My Hosted Bots' to Start, Stop, Restart, or Delete bots.</i>\n"
        f"<i>4. Top up balance using 'Deposit Funds' or redeem promo codes.</i>\n\n"
        f"<i>Send /cancel at any point to abort inputs.</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back", "main_menu", style="danger")]])
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(text, reply_markup=kb)

# ==============================================================
# MASTER ADMIN CONTROL PANEL
# ==============================================================
@dp.callback_query(F.data == "admin_panel")
async def admin_dashboard(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        await call.answer("Access Denied.", show_alert=True)
        return

    current_upi = await get_setting("admin_upi", "Not Set")
    has_welcome_photo = "Custom Banner Set" if (await get_setting("welcome_photo_id")) else "Default Banner"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            styled_btn("Statistics", "adm_stats", style="primary"),
            styled_btn("Gift Codes", "adm_manage_gifts", style="success")
        ],
        [
            styled_btn("Set Banner Photo", "adm_set_welcome_photo", style="primary"),
            styled_btn("Configure UPI", "adm_set_upi", style="success")
        ],
        [
            styled_btn("Manage Categories", "adm_manage_cats", style="primary"),
            styled_btn("Manage Templates", "adm_manage_tpl_menu", style="primary")
        ],
        [
            styled_btn("Upload Template", "adm_upload_tpl", style="success"),
            styled_btn("Broadcast Message", "adm_broadcast", style="primary")
        ],
        [
            styled_btn("Credit Balance", "adm_add_funds", style="success"),
            styled_btn("Debit Balance", "adm_debit_funds", style="danger")
        ],
        [
            styled_btn("Ban User", "adm_ban_user", style="danger"),
            styled_btn("Unban User", "adm_unban_user", style="success")
        ],
        [
            styled_btn("Manage Admins", "adm_manage_admins", style="primary"),
            styled_btn("Force Channels", "adm_force_channels", style="primary")
        ],
        [styled_btn("Main Menu", "main_menu", style="danger")]
    ])

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['CROWN']} <i><b>Master Admin Control Panel</b></i>\n\n"
        f"• <i><b>Admin:</b> {call.from_user.full_name}</i>\n"
        f"• <i><b>UPI ID:</b> <code>{current_upi}</code></i>\n"
        f"• <i><b>Banner Photo:</b> <code>{has_welcome_photo}</code></i>\n\n"
        f"<i>Select an option below to manage platform settings:</i>",
        reply_markup=kb
    )

# --- Set Welcome Banner Photo ---
@dp.callback_query(F.data == "adm_set_welcome_photo")
async def adm_set_welcome_photo_menu(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [styled_btn("Remove Custom Banner", "adm_remove_welcome_photo", style="danger")],
        [styled_btn("Back to Admin Panel", "admin_panel", style="primary")]
    ])

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['SPARKLE']} <i><b>Set Welcome Banner Photo</b></i>\n\n"
        f"<i>Please upload the photo to be displayed on the main welcome dashboard:</i>",
        reply_markup=kb
    )
    await state.set_state(AdminStates.set_welcome_photo)

@dp.message(AdminStates.set_welcome_photo, F.photo)
async def adm_save_welcome_photo(message: types.Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await set_setting("welcome_photo_id", photo_file_id)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>Welcome banner photo updated successfully!</b></i>", reply_markup=kb)

@dp.callback_query(F.data == "adm_remove_welcome_photo")
async def adm_remove_welcome_photo(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await set_setting("welcome_photo_id", "")
    await call.answer("Banner removed.", show_alert=True)
    await admin_dashboard(call)

# ==============================================================
# TEMPLATES MANAGEMENT
# ==============================================================
@dp.callback_query(F.data == "adm_manage_tpl_menu")
async def adm_manage_templates_list(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT t.id, t.name, t.price, c.name as cat_name 
            FROM templates t
            JOIN categories c ON t.category_id = c.id
        """) as cur:
            templates = await cur.fetchall()

    if not templates:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Upload Template", "adm_upload_tpl", style="success")],
            [styled_btn("Admin Panel", "admin_panel", style="primary")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(f"{E['CROSS']} <i>No bot templates found.</i>", reply_markup=kb)
        return

    buttons = []
    for tpl in templates:
        p_badge = "FREE" if tpl['price'] == 0 else f"₹{tpl['price']}"
        buttons.append([styled_btn(f"{tpl['name']} [{tpl['cat_name']}] - {p_badge}", f"adm_tpl_detail_{tpl['id']}", style="primary")])
    buttons.append([styled_btn("Upload New Template", "adm_upload_tpl", style="success")])
    buttons.append([styled_btn("Admin Panel", "admin_panel", style="danger")])

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        f"{E['PACKAGE']} <i><b>Manage Templates Dashboard</b></i>\n\n"
        f"<i>Select any template to inspect, edit pricing, or delete:</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data.startswith("adm_tpl_detail_"))
async def adm_template_single_view(call: types.CallbackQuery):
    tpl_id = int(call.data.replace("adm_tpl_detail_", ""))

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT t.*, c.name as cat_name 
            FROM templates t
            JOIN categories c ON t.category_id = c.id
            WHERE t.id = ?
        """, (tpl_id,)) as cur:
            tpl = await cur.fetchone()

    if not tpl:
        await call.answer("Template not found.", show_alert=True)
        return

    price_str = "FREE (₹0)" if tpl["price"] == 0 else f"₹{tpl['price']:.2f}"

    text = (
        f"{E['PACKAGE']} <i><b>Template Details & Configuration</b></i>\n\n"
        f"• <i><b>Name:</b> <code>{tpl['name']}</code></i>\n"
        f"• <i><b>Category:</b> <code>{tpl['cat_name']}</code></i>\n"
        f"• <i><b>Current Price:</b> <code>{price_str}</code></i>\n"
        f"• <i><b>Script Path:</b> <code>{tpl['file_path']}</code></i>\n\n"
        f"{E['TAG']} <i><b>Features:</b></i>\n<i>{tpl['description']}</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [styled_btn("Edit Price", f"adm_tpled_prc_{tpl_id}", style="primary")],
        [styled_btn("Delete Template", f"adm_tpled_del_{tpl_id}", style="danger")],
        [styled_btn("Back to Templates", "adm_manage_tpl_menu", style="success")]
    ])

    try:
        await call.message.delete()
    except Exception:
        pass

    if tpl["banner_file_id"]:
        await call.message.answer_photo(photo=tpl["banner_file_id"], caption=text, reply_markup=kb)
    else:
        await call.message.answer(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_tpled_prc_"))
async def adm_edit_template_price_prompt(call: types.CallbackQuery, state: FSMContext):
    tpl_id = int(call.data.replace("adm_tpled_prc_", ""))
    await state.update_data(edit_tpl_id=tpl_id)
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['CASH']} <i><b>Enter new price (₹, 0 for free):</b></i>")
    await state.set_state(AdminStates.edit_tpl_price)

@dp.message(AdminStates.edit_tpl_price)
async def adm_save_template_price(message: types.Message, state: FSMContext):
    try:
        new_price = float(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric value:</i>")
        return

    data = await state.get_data()
    tpl_id = data["edit_tpl_id"]

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE templates SET price = ? WHERE id = ?", (new_price, tpl_id))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back to Templates", "adm_manage_tpl_menu", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>Template price updated to ₹{new_price:.2f}!</b></i>", reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_tpled_del_"))
async def adm_delete_template_confirm(call: types.CallbackQuery):
    tpl_id = int(call.data.replace("adm_tpled_del_", ""))

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT file_path FROM templates WHERE id = ?", (tpl_id,)) as cur:
            row = await cur.fetchone()
            if row and os.path.exists(row[0]):
                try:
                    os.remove(row[0])
                except Exception:
                    pass
        await db.execute("DELETE FROM templates WHERE id = ?", (tpl_id,))
        await db.commit()

    await call.answer("Template deleted permanently.", show_alert=True)
    await adm_manage_templates_list(call)

# ==============================================================
# GIFT CODES CONTROLLER
# ==============================================================
@dp.callback_query(F.data == "adm_manage_gifts")
async def adm_gift_codes_menu(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM gift_codes ORDER BY created_at DESC") as cur:
            gifts = await cur.fetchall()

    buttons = []
    for g in gifts:
        btn_txt = f"Delete: {g['code']} - ₹{g['amount']} ({g['used_count']}/{g['max_uses']})"
        buttons.append([styled_btn(btn_txt, f"adm_delgift_{g['code']}", style="danger")])

    buttons.append([styled_btn("Generate Gift Code", "adm_add_gift_start", style="success")])
    buttons.append([styled_btn("Admin Panel", "admin_panel", style="primary")])

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['GIFT']} <i><b>Gift Codes Management</b></i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data == "adm_add_gift_start")
async def adm_create_gift_step1(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['TAG']} <i><b>Step 1:</b> Enter the Gift Code name (e.g., <code>BONUS50</code>):</i>")
    await state.set_state(AdminStates.gift_name)

@dp.message(AdminStates.gift_name)
async def adm_create_gift_step2(message: types.Message, state: FSMContext):
    code_name = message.text.strip().upper()
    await state.update_data(gift_code=code_name)
    await message.answer(f"{E['CASH']} <i><b>Step 2:</b> Enter the monetary value (₹) for <code>{code_name}</code>:</i>")
    await state.set_state(AdminStates.gift_amount)

@dp.message(AdminStates.gift_amount)
async def adm_create_gift_step3(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric value:</i>")
        return

    await state.update_data(gift_amount=amount)
    await message.answer(f"{E['USER']} <i><b>Step 3:</b> Enter the maximum usage limit (e.g., <code>10</code>):</i>")
    await state.set_state(AdminStates.gift_max_uses)

@dp.message(AdminStates.gift_max_uses)
async def adm_create_gift_finish(message: types.Message, state: FSMContext):
    try:
        max_uses = int(message.text.strip())
        if max_uses <= 0:
            raise ValueError
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid integer:</i>")
        return

    data = await state.get_data()
    code = data["gift_code"]
    amount = data["gift_amount"]

    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                INSERT INTO gift_codes (code, amount, max_uses, used_count)
                VALUES (?, ?, ?, 0)
            """, (code, amount, max_uses))
            await db.commit()
    except Exception:
        await message.answer(f"{E['CROSS']} <i>Error: Code already exists.</i>")
        await state.clear()
        return

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Gift Codes List", "adm_manage_gifts", style="success")]])
    await message.answer(
        f"{E['CHECK']} <i><b>Gift Code Created Successfully!</b></i>\n\n"
        f"• <i><b>Code:</b> <code>{code}</code></i>\n"
        f"• <i><b>Amount:</b> <code>₹{amount:.2f}</code></i>\n"
        f"• <i><b>Max Users:</b> <code>{max_uses}</code></i>",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("adm_delgift_"))
async def adm_delete_gift_code(call: types.CallbackQuery):
    code = call.data.replace("adm_delgift_", "")
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM gift_codes WHERE code = ?", (code,))
        await db.commit()
    await call.answer("Gift code removed.", show_alert=True)
    await adm_gift_codes_menu(call)

# ==============================================================
# CATEGORIES CONTROLLER
# ==============================================================
@dp.callback_query(F.data == "adm_manage_cats")
async def adm_categories_menu(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM categories") as cur:
            categories = await cur.fetchall()

    buttons = []
    for cat in categories:
        buttons.append([styled_btn(f"Delete: {cat['name']}", f"adm_delcat_{cat['id']}", style="danger")])

    buttons.append([styled_btn("Add New Category", "adm_add_cat_start", style="success")])
    buttons.append([styled_btn("Admin Panel", "admin_panel", style="primary")])

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        f"{E['FOLDER']} <i><b>Categories Management</b></i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data == "adm_add_cat_start")
async def adm_add_category_prompt(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['FOLDER']} <i><b>Enter new category name:</b></i>")
    await state.set_state(AdminStates.add_category_name)

@dp.message(AdminStates.add_category_name)
async def adm_save_category(message: types.Message, state: FSMContext):
    cat_name = message.text.strip()
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO categories (name) VALUES (?)", (cat_name,))
            await db.commit()
        await state.clear()
        kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back to Categories", "adm_manage_cats", style="primary")]])
        await message.answer(f"{E['CHECK']} <i><b>Category Added:</b> <code>{cat_name}</code></i>", reply_markup=kb)
    except Exception:
        await message.answer(f"{E['CROSS']} <i>Error: Category name already exists.</i>")

@dp.callback_query(F.data.startswith("adm_delcat_"))
async def adm_delete_category(call: types.CallbackQuery):
    cat_id = int(call.data.replace("adm_delcat_", ""))
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        await db.commit()
    await call.answer("Category deleted.", show_alert=True)
    await adm_categories_menu(call)

# ==============================================================
# TEMPLATE UPLOADER
# ==============================================================
@dp.callback_query(F.data == "adm_upload_tpl")
async def adm_upload_tpl_step0(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, name FROM categories") as cur:
            categories = await cur.fetchall()

    if not categories:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Create Category First", "adm_add_cat_start", style="success")],
            [styled_btn("Admin Panel", "admin_panel", style="primary")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(f"{E['CROSS']} <i>Please create a category first before adding templates.</i>", reply_markup=kb)
        return

    buttons = []
    for cat in categories:
        buttons.append([styled_btn(f"{cat['name']}", f"adm_pickcat_{cat['id']}", style="primary")])
    buttons.append([styled_btn("Admin Panel", "admin_panel", style="danger")])

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        f"{E['FOLDER']} <i><b>Step 1:</b> Select a Category:</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(AdminStates.tpl_category)

@dp.callback_query(AdminStates.tpl_category, F.data.startswith("adm_pickcat_"))
async def adm_upload_tpl_step1(call: types.CallbackQuery, state: FSMContext):
    cat_id = int(call.data.replace("adm_pickcat_", ""))
    await state.update_data(category_id=cat_id)

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['TAG']} <i><b>Step 2:</b> Enter Template Name:</i>")
    await state.set_state(AdminStates.tpl_name)

@dp.message(AdminStates.tpl_name)
async def adm_upload_tpl_step2(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer(f"{E['PIN']} <i><b>Step 3:</b> Enter Features / Description:</i>")
    await state.set_state(AdminStates.tpl_desc)

@dp.message(AdminStates.tpl_desc)
async def adm_upload_tpl_step3(message: types.Message, state: FSMContext):
    await state.update_data(desc=message.text.strip())
    await message.answer(f"{E['MONEY']} <i><b>Step 4:</b> Enter Price (₹, enter 0 for free):</i>")
    await state.set_state(AdminStates.tpl_price)

@dp.message(AdminStates.tpl_price)
async def adm_upload_tpl_step4(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric amount:</i>")
        return

    await state.update_data(price=price)
    await message.answer(f"{E['SPARKLE']} <i><b>Step 5:</b> Send Demo Banner Photo:</i>")
    await state.set_state(AdminStates.tpl_banner)

@dp.message(AdminStates.tpl_banner, F.photo)
async def adm_upload_tpl_step5(message: types.Message, state: FSMContext):
    banner_file_id = message.photo[-1].file_id
    await state.update_data(banner_file_id=banner_file_id)

    await message.answer(f"{E['PACKAGE']} <i><b>Step 6:</b> Upload standalone Python script (<code>.py</code>):</i>")
    await state.set_state(AdminStates.tpl_file)

@dp.message(AdminStates.tpl_file, F.document)
async def adm_upload_tpl_finish(message: types.Message, state: FSMContext):
    if not message.document.file_name.endswith(".py"):
        await message.answer(f"{E['CROSS']} <i>Please upload a Python (<code>.py</code>) file only!</i>")
        return

    data = await state.get_data()
    file_info = await bot.get_file(message.document.file_id)
    save_name = f"tpl_{int(time.time())}.py"
    local_path = os.path.join(TEMPLATES_DIR, save_name)

    await bot.download_file(file_info.file_path, local_path)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO templates (category_id, name, description, file_path, price, banner_file_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data["category_id"], data["name"], data["desc"], local_path, data["price"], data["banner_file_id"]))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(
        f"{E['CHECK']} <i><b>Template Added Successfully!</b></i>\n\n"
        f"• <i><b>Name:</b> <code>{data['name']}</code></i>\n"
        f"• <i><b>Price:</b> <code>₹{data['price']}</code></i>",
        reply_markup=kb
    )

# ==============================================================
# BOT STATISTICS
# ==============================================================
@dp.callback_query(F.data == "adm_stats")
async def show_bot_statistics(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1") as cur:
            banned_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM user_bots") as cur:
            total_bots = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM categories") as cur:
            total_cats = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM templates") as cur:
            total_templates = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM gift_codes") as cur:
            total_gifts = (await cur.fetchone())[0]
        async with db.execute("SELECT SUM(balance) FROM users") as cur:
            total_wallet_funds = (await cur.fetchone())[0] or 0.0

    stats_text = (
        f"{E['STATS']} <i><b>Live Server Statistics & Analytics</b></i>\n\n"
        f"• <i><b>Total Users:</b> <code>{total_users}</code> (Banned: <code>{banned_users}</code>)</i>\n"
        f"• <i><b>Hosted Bots:</b> <code>{total_bots}</code></i>\n"
        f"• <i><b>Active Subprocesses:</b> <code>{len(ACTIVE_PROCESSES)}</code></i>\n"
        f"• <i><b>Categories:</b> <code>{total_cats}</code> | <b>Templates:</b> <code>{total_templates}</code></i>\n"
        f"• <i><b>Active Gift Codes:</b> <code>{total_gifts}</code></i>\n"
        f"• <i><b>Total Wallet Holding:</b> <code>₹{total_wallet_funds:.2f}</code></i>\n"
        f"• <i><b>Server Status:</b> <code>Optimal & Running 24/7</code> {E['FLASH']}</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back to Admin", "admin_panel", style="primary")]])
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(stats_text, reply_markup=kb)

# ==============================================================
# CREDIT / DEBIT FUNDS
# ==============================================================
@dp.callback_query(F.data == "adm_add_funds")
async def adm_add_funds_step1(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['CASH']} <i><b>Enter User Telegram ID:</b></i>")
    await state.set_state(AdminStates.add_funds_user)

@dp.message(AdminStates.add_funds_user)
async def adm_add_funds_step2(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric ID:</i>")
        return

    await state.update_data(target_id=target_id)
    await message.answer(f"<i>Enter amount (₹) to credit to User <code>{target_id}</code>:</i>")
    await state.set_state(AdminStates.add_funds_amt)

@dp.message(AdminStates.add_funds_amt)
async def adm_add_funds_step3(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        amt = float(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric amount:</i>")
        return

    data = await state.get_data()
    target_id = data["target_id"]

    await update_balance(target_id, amt)
    await state.clear()

    try:
        await bot.send_message(chat_id=target_id, text=f"{E['GIFT']} <i><b>Admin added ₹{amt:.2f} to your balance!</b></i>")
    except Exception:
        pass

    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>₹{amt:.2f} credited to User <code>{target_id}</code>!</b></i>", reply_markup=kb)

@dp.callback_query(F.data == "adm_debit_funds")
async def adm_debit_funds_step1(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['CASH']} <i><b>Enter User Telegram ID:</b></i>")
    await state.set_state(AdminStates.debit_funds_user)

@dp.message(AdminStates.debit_funds_user)
async def adm_debit_funds_step2(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric ID:</i>")
        return

    await state.update_data(target_id=target_id)
    await message.answer(f"<i>Enter amount (₹) to debit from User <code>{target_id}</code>:</i>")
    await state.set_state(AdminStates.debit_funds_amt)

@dp.message(AdminStates.debit_funds_amt)
async def adm_debit_funds_step3(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        amt = float(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric amount:</i>")
        return

    data = await state.get_data()
    target_id = data["target_id"]

    await update_balance(target_id, -amt)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>₹{amt:.2f} debited from User <code>{target_id}</code>!</b></i>", reply_markup=kb)

# ==============================================================
# BAN / UNBAN USERS
# ==============================================================
@dp.callback_query(F.data == "adm_ban_user")
async def adm_ban_step1(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['CROSS']} <i><b>Enter User Telegram ID to ban:</b></i>")
    await state.set_state(AdminStates.ban_user)

@dp.message(AdminStates.ban_user)
async def adm_ban_step2(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Invalid ID:</i>")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['CROSS']} <i>User <code>{target_id}</code> has been banned.</i>", reply_markup=kb)

@dp.callback_query(F.data == "adm_unban_user")
async def adm_unban_step1(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['ONLINE']} <i><b>Enter User Telegram ID to unban:</b></i>")
    await state.set_state(AdminStates.unban_user)

@dp.message(AdminStates.unban_user)
async def adm_unban_step2(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Invalid ID:</i>")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['ONLINE']} <i>User <code>{target_id}</code> has been unbanned.</i>", reply_markup=kb)

# ==============================================================
# MANAGE ADMINS (OWNER ONLY)
# ==============================================================
@dp.callback_query(F.data == "adm_manage_admins")
async def adm_admins_menu(call: types.CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("Access restricted to Main Owner.", show_alert=True)
        return

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM admins") as cur:
            admins = await cur.fetchall()

    adm_list_str = "\n".join([f"• <code>{a[0]}</code>" for a in admins]) if admins else "<i>No Sub-Administrators assigned.</i>"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            styled_btn("Add Admin", "adm_add_admin_action", style="success"),
            styled_btn("Remove Admin", "adm_del_admin_action", style="danger")
        ],
        [styled_btn("Admin Panel", "admin_panel", style="primary")]
    ])

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['CROWN']} <i><b>Administrators Management</b></i>\n\n"
        f"• <i><b>Main Owner:</b> <code>{OWNER_ID}</code></i>\n\n"
        f"• <i><b>Sub-Admins:</b></i>\n{adm_list_str}",
        reply_markup=kb
    )

@dp.callback_query(F.data == "adm_add_admin_action")
async def adm_add_admin_input(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['USER']} <i>Enter Telegram User ID to grant Admin rights:</i>")
    await state.set_state(AdminStates.add_admin)

@dp.message(AdminStates.add_admin)
async def adm_add_admin_finish(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        new_admin = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Invalid ID:</i>")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?, ?)", (new_admin, message.from_user.id))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back", "adm_manage_admins", style="primary")]])
    await message.answer(f"{E['CHECK']} <i>User <code>{new_admin}</code> assigned as Admin!</i>", reply_markup=kb)

@dp.callback_query(F.data == "adm_del_admin_action")
async def adm_del_admin_input(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['USER']} <i>Enter Telegram User ID to revoke Admin rights:</i>")
    await state.set_state(AdminStates.del_admin)

@dp.message(AdminStates.del_admin)
async def adm_del_admin_finish(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        del_adm = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Invalid ID:</i>")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM admins WHERE user_id = ?", (del_adm,))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back", "adm_manage_admins", style="primary")]])
    await message.answer(f"{E['CHECK']} <i>User <code>{del_adm}</code> removed from Admin list!</i>", reply_markup=kb)

# ==============================================================
# FORCE JOIN CHANNELS
# ==============================================================
@dp.callback_query(F.data == "adm_force_channels")
async def adm_channels_menu(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM force_channels") as cur:
            channels = await cur.fetchall()

    buttons = []
    for ch in channels:
        buttons.append([styled_btn(f"Delete: {ch['name']}", f"adm_delch_{ch['id']}", style="danger")])
    buttons.append([styled_btn("Add New Channel", "adm_add_channel", style="success")])
    buttons.append([styled_btn("Admin Panel", "admin_panel", style="primary")])

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['CHANNEL']} <i><b>Force Join Channels Management</b></i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data == "adm_add_channel")
async def adm_channel_add_step1(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        f"{E['CHANNEL']} <i><b>Step 1:</b> Enter Channel ID or Username (e.g., <code>@MyChannel</code>):</i>"
    )
    await state.set_state(AdminStates.add_ch_id)

@dp.message(AdminStates.add_ch_id)
async def adm_channel_add_step2(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    await state.update_data(ch_id=message.text.strip())
    await message.answer(f"{E['TAG']} <i><b>Step 2:</b> Enter Channel Display Name:</i>")
    await state.set_state(AdminStates.add_ch_name)

@dp.message(AdminStates.add_ch_name)
async def adm_channel_add_step3(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    await state.update_data(ch_name=message.text.strip())
    await message.answer(f"{E['PIN']} <i><b>Step 3:</b> Enter Invite Link (e.g., <code>https://t.me/...</code>):</i>")
    await state.set_state(AdminStates.add_ch_link)

@dp.message(AdminStates.add_ch_link)
async def adm_channel_add_step4(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    link = message.text.strip()
    data = await state.get_data()

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO force_channels (channel_id, name, invite_link) VALUES (?, ?, ?)", (data["ch_id"], data["ch_name"], link))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back to Channels", "adm_force_channels", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>Force Join Channel Added!</b></i>", reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_delch_"))
async def adm_del_channel(call: types.CallbackQuery):
    ch_id = int(call.data.replace("adm_delch_", ""))
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM force_channels WHERE id = ?", (ch_id,))
        await db.commit()
    await call.answer("Channel deleted.", show_alert=True)
    await adm_channels_menu(call)

# ==============================================================
# CONFIGURE UPI & BROADCAST
# ==============================================================
@dp.callback_query(F.data == "adm_set_upi")
async def adm_set_upi_start(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['CARD']} <i><b>Enter your UPI ID (e.g., <code>merchant@bank</code>):</b></i>")
    await state.set_state(AdminStates.set_upi)

@dp.message(AdminStates.set_upi)
async def adm_set_upi_finish(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    upi = message.text.strip()
    await set_setting("admin_upi", upi)
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>UPI ID Set: <code>{upi}</code></b></i>", reply_markup=kb)

@dp.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_start(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['CHANNEL']} <i><b>Send message to broadcast to all registered users:</b></i>")
    await state.set_state(AdminStates.broadcast_msg)

@dp.message(AdminStates.broadcast_msg)
async def adm_broadcast_finish(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_banned = 0") as cur:
            users = await cur.fetchall()

    count = 0
    await message.answer("<i>Broadcasting message...</i>")
    for u in users:
        try:
            await message.copy_to(chat_id=u[0])
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>Broadcast delivered to <code>{count}</code> active users!</b></i>", reply_markup=kb)

# ==============================================================
# MAIN ENTRY POINT
# ==============================================================
async def main():
    await init_db()
    print("[*] Restoring hosted child bots...")
    await restore_all_bots()
    print("[+] Master Bot Engine is Online & Running!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n[!] Master Bot Stopped.")