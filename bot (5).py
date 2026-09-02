import os
import logging
import traceback
import asyncio
from datetime import datetime

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import psycopg2
from psycopg2.pool import SimpleConnectionPool

# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN belum diisi!")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL belum diisi!")

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# =========================================================
# CONFIG
# =========================================================

ADMIN_ID = 7640270845
SOURCE_CHANNEL = -1003748208059

# =========================================================
# DATABASE POOL
# =========================================================

db_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    dsn=DATABASE_URL
)

def get_conn():
    return db_pool.getconn()

def release_conn(conn):
    db_pool.putconn(conn)

# =========================================================
# INIT DATABASE
# =========================================================

def init_db():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        joined_at TIMESTAMP DEFAULT NOW()
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_users (
        user_id BIGINT,
        date TEXT,
        UNIQUE(user_id, date)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS referrals (
        referrer_id BIGINT,
        invited_id BIGINT UNIQUE
    )
    """)

    conn.commit()

    cur.close()
    release_conn(conn)

init_db()

# =========================================================
# USERS
# =========================================================

def add_user(user_id):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO users (
        user_id
    )
    VALUES (%s)
    ON CONFLICT (user_id)
    DO NOTHING
    """, (user_id,))

    conn.commit()

    cur.close()
    release_conn(conn)

def user_exists(user_id):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT 1
    FROM users
    WHERE user_id=%s
    """, (user_id,))

    result = cur.fetchone()

    cur.close()
    release_conn(conn)

    return result is not None

def get_total_users():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT COUNT(*)
    FROM users
    """)

    total = cur.fetchone()[0]

    cur.close()
    release_conn(conn)

    return total

def get_all_users():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT user_id
    FROM users
    """)

    users = [row[0] for row in cur.fetchall()]

    cur.close()
    release_conn(conn)

    return users

# =========================================================
# DAILY USERS
# =========================================================

def add_daily_user(user_id):

    today = datetime.now().strftime("%Y-%m-%d")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO daily_users (
        user_id,
        date
    )
    VALUES (%s, %s)
    ON CONFLICT DO NOTHING
    """, (
        user_id,
        today
    ))

    conn.commit()

    cur.close()
    release_conn(conn)

def get_today_users():

    today = datetime.now().strftime("%Y-%m-%d")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT COUNT(*)
    FROM daily_users
    WHERE date=%s
    """, (today,))

    total = cur.fetchone()[0]

    cur.close()
    release_conn(conn)

    return total

# =========================================================
# REFERRALS
# =========================================================

def add_referral(
    referrer_id,
    invited_id
):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO referrals (
        referrer_id,
        invited_id
    )
    VALUES (%s, %s)
    ON CONFLICT (invited_id)
    DO NOTHING
    """, (
        referrer_id,
        invited_id
    ))

    conn.commit()

    cur.close()
    release_conn(conn)

def get_referral_count(
    referrer_id
):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT COUNT(*)
    FROM referrals
    WHERE referrer_id=%s
    """, (referrer_id,))

    total = cur.fetchone()[0]

    cur.close()
    release_conn(conn)

    return total

# =========================================================
# KEYBOARD
# =========================================================

def start_keyboard(user_id):

    buttons = [
        [
            InlineKeyboardButton(
                "🔥 VVIP",
                callback_data="vvip"
            ),

            InlineKeyboardButton(
                "📢 Undang Teman",
                callback_data="referral"
            ),
        ],

        [
            InlineKeyboardButton(
                "⭐ Testimoni",
                callback_data="testimoni"
            ),

            InlineKeyboardButton(
                "👥 Daftar Teman",
                callback_data="daftar_teman"
            ),
        ],

        [
            InlineKeyboardButton(
                "⭐ Testimoni Andini",
                callback_data="testimoni_andini"
            )
        ]
    ]

    if user_id == ADMIN_ID:
        buttons.append([
            InlineKeyboardButton(
                "👥 User",
                callback_data="user_count"
            )
        ])

    return InlineKeyboardMarkup(buttons)

def vip_keyboard():

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 VIP HIJABERS", callback_data="vip_hijabers")],
        [InlineKeyboardButton("📁 VIP ANDINI (*89VID+100GAMBAR)", callback_data="vip_andini")],
        [InlineKeyboardButton("📁 VIP KUMPULAN TIKTOK(15.612VID)", callback_data="vip_tiktok")],
        [InlineKeyboardButton("📁 VIP TWITTER (12.425 VID)", callback_data="vip_twitter")],
        [InlineKeyboardButton("📁 VIP RUSSIA (4.531 VID)", callback_data="vip_ometv")],
        [InlineKeyboardButton("📁 VIP BBC", callback_data="vip_bbc")],
        [InlineKeyboardButton("📁 VIP INDONESIA", callback_data="vip_kolpri")],
        [InlineKeyboardButton("📁 VIP KUMOULAN JAV", callback_data="vip_random")],
        [InlineKeyboardButton("📁 VIP PRENIUM", callback_data="vip_premium")],
        [InlineKeyboardButton("📁 VIP PELAJAR [A]", callback_data="vip_bocil_a")],
        [InlineKeyboardButton("📁 VIP PELAJAR [B]", callback_data="vip_bocil_b")],
        [InlineKeyboardButton("📁 VIP ANIME HENTAI ", callback_data="vip_anime")],
        [InlineKeyboardButton("📁 VIP GAME HENTAI ", callback_data="vip_game")],
        [InlineKeyboardButton("🛒 Ambil Semua VIP", callback_data="vip_all")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="menu")]
    ])

# =========================================================
# PAYMENT TEXT
# =========================================================

def get_payment_text(
    user,
    amount
):

    name = (
        user.last_name
        if user.last_name
        else user.first_name
    )

    mention = (
        f'<a href="tg://user?id={user.id}">'
        f'{name}</a>'
    )

    return (
        f"👋 Hallo {mention}\n\n"
        f"Silakan lakukan pembayaran sebesar:\n"
        f"<b>Rp. {amount}</b>\n\n"
        f"menggunakan QRIS berikut.\n\n"
        f"setelah berhasil melakukan pembayaran, link grup otomatis akan terkirim.\n\n"
        f"⚠️ Pembayaran hanya berlaku "
        f"beberapa menit."
    )

# =========================================================
# PROMO LOOP (DIPERBAIKI DENGAN PARALEL)
# =========================================================

async def send_hourly_promo(context: ContextTypes.DEFAULT_TYPE):
    start_time = datetime.now()
    logging.info(f"🕐 [START] Menjalankan promo pada: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    users = get_all_users()
    total = len(users)
    logging.info(f"📊 Total user: {total}")

    # Batas konkurensi (5 user sekaligus, aman untuk rate limit)
    semaphore = asyncio.Semaphore(5)

    async def send_to_user(user_id):
        async with semaphore:
            try:
                msg = await context.bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=SOURCE_CHANNEL,
                    message_id=3
                )
                await context.bot.edit_message_caption(
                    chat_id=user_id,
                    message_id=msg.message_id,
                    caption=(
                        "🔥 <b>BIG PROMO MODAL 10K JOIN VVIP SELAMANYA!!</b>\n\n"
                        "Join sekarang dan nikmati akses premium terbaru 🔥"
                    ),
                    reply_markup=start_keyboard(user_id),
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.warning(f"⚠️ Gagal kirim promo ke {user_id}: {e}")

    # Buat task untuk semua user
    tasks = [send_to_user(uid) for uid in users]
    # Eksekusi secara paralel
    await asyncio.gather(*tasks)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logging.info(f"✅ [END] Selesai mengirim promo pada: {end_time.strftime('%Y-%m-%d %H:%M:%S')} (durasi {duration:.2f} detik)")

# =========================================================
# PHOTO HANDLER
# =========================================================

async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "✅ Bukti transfer berhasil diterima.\n"
        "Mohon tunggu verifikasi admin."
    )

# =========================================================
# FUNGSI KIRIM MENU UTAMA
# =========================================================

async def send_main_menu_to_user(chat_id, user, bot):
    name = user.last_name if user.last_name else user.first_name
    mention = f'<a href="tg://user?id={user.id}">{name}</a>'
    msg = await bot.copy_message(
        chat_id=chat_id,
        from_chat_id=SOURCE_CHANNEL,
        message_id=13
    )
    await bot.edit_message_caption(
        chat_id=chat_id,
        message_id=msg.message_id,
        caption=(
            f"Halo {mention}\n\n"
            f"Selamat datang di "
            f"<b>VVIP ASUPAN VIRAL</b>"
        ),
        reply_markup=start_keyboard(user.id),
        parse_mode="HTML"
    )

# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    is_new_user = not user_exists(user.id)

    add_user(user.id)
    add_daily_user(user.id)

    # =====================================================
    # REFERRAL
    # =====================================================

    if context.args and is_new_user:

        try:

            referrer_id = int(context.args[0])

            if referrer_id != user.id:

                add_referral(
                    referrer_id,
                    user.id
                )

                invited_count = get_referral_count(
                    referrer_id
                )

                notif_text = (
                    f"🎉 Kamu berhasil mengundang "
                    f"1 teman!\n\n"
                    f"📊 Total referral:\n"
                    f"<b>{invited_count}/15</b>"
                )

                if invited_count >= 15:

                    notif_text += (
                        "\n\n🏆 SELAMAT!\n"
                        "Kamu mendapatkan "
                        "1 VVIP GRATIS!"
                    )

                try:

                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=notif_text,
                        parse_mode="HTML"
                    )

                except:
                    pass

        except Exception as e:

            logging.warning(
                f"Referral error: {e}"
            )

    # =====================================================
    # WELCOME MESSAGE
    # =====================================================

    await send_main_menu_to_user(update.effective_chat.id, user, context.bot)

# =========================================================
# BUTTON HANDLER
# =========================================================

async def handle_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    user = query.from_user

    await query.answer()

    # =====================================================
    # USER COUNT
    # =====================================================

    if query.data == "user_count":

        if user.id != ADMIN_ID:
            return

        total_today = get_today_users()
        total_all = get_total_users()

        await query.message.reply_text(
            f"👥 Hari ini: {total_today}\n"
            f"👥 Total semua: {total_all}"
        )

    # =====================================================
    # VVIP
    # =====================================================

    elif query.data == "vvip":

        await query.edit_message_caption(
            caption=(
                "<b>📚 DAFTAR VVIP</b>\n\n"
                "Pilih paket di bawah 👇"
            ),

            reply_markup=vip_keyboard(),
            parse_mode="HTML"
        )

    # =====================================================
    # TESTIMONI (biasa)
    # =====================================================

    elif query.data == "testimoni":

        testimoni_ids = [25, 26, 27, 28, 29, 30]

        for msg_id in testimoni_ids:
            await context.bot.copy_message(
                chat_id=query.message.chat_id,
                from_chat_id=SOURCE_CHANNEL,
                message_id=msg_id
            )

        await query.message.reply_text(
            "Klik tombol di bawah untuk kembali ke menu.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu")]
            ])
        )

    # =====================================================
    # TESTIMONI ANDINI
    # =====================================================

    elif query.data == "testimoni_andini":

        await context.bot.copy_message(
            chat_id=query.message.chat_id,
            from_chat_id=SOURCE_CHANNEL,
            message_id=31
        )

        await query.message.reply_text(
            "Klik tombol di bawah untuk kembali ke menu.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu")]
            ])
        )

    # =====================================================
    # REFERRAL
    # =====================================================

    elif query.data == "referral":

        bot_username = (
            await context.bot.get_me()
        ).username

        ref_link = (
            f"https://t.me/"
            f"{bot_username}?start={user.id}"
        )

        await query.edit_message_caption(
            caption=(
                f"🔗 Link referral kamu:\n\n"
                f"<code>{ref_link}</code>"
            ),

            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Kembali",
                        callback_data="menu"
                    )
                ]
            ]),

            parse_mode="HTML"
        )

    # =====================================================
    # DAFTAR TEMAN
    # =====================================================

    elif query.data == "daftar_teman":

        bot_username = (
            await context.bot.get_me()
        ).username

        ref_link = (
            f"https://t.me/"
            f"{bot_username}?start={user.id}"
        )

        invited_count = get_referral_count(
            user.id
        )

        sisa = max(
            0,
            15 - invited_count
        )

        if invited_count >= 15:

            status_text = (
                "🏆 Kamu sudah mendapatkan "
                "VVIP GRATIS!"
            )

        else:

            status_text = (
                f"Undang {sisa} orang lagi "
                f"untuk mendapatkan "
                f"VVIP GRATIS!"
            )

        caption = (
            f"👥 <b>DAFTAR TEMAN</b>\n\n"
            f"🔗 Link referral:\n"
            f"<code>{ref_link}</code>\n\n"
            f"📊 Referral valid:\n"
            f"<b>{invited_count}/15</b>\n\n"
            f"{status_text}"
        )

        await query.edit_message_caption(
            caption=caption,

            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Kembali",
                        callback_data="menu"
                    )
                ]
            ]),

            parse_mode="HTML"
        )

    # =====================================================
    # VIP 15K (message_id=4) untuk: ANIME, INDONESIA
    # =====================================================

    elif query.data in [
        "vip_anime",
        "vip_kolpri"
    ]:

        await context.bot.copy_message(
            chat_id=query.message.chat_id,
            from_chat_id=SOURCE_CHANNEL,
            message_id=4
        )

        await query.message.reply_text(
            get_payment_text(
                user,
                "15.000"
            ),
            parse_mode="HTML"
        )

    # =====================================================
    # VIP 20K (message_id=2) untuk: HIJABERS, RANDOM, TWITTER, RUSSIA, PREMIUM, GAME, BBC, TIKTOK
    # =====================================================

    elif query.data in [
        "vip_hijabers",
        "vip_random",
        "vip_twitter",
        "vip_ometv",
        "vip_premium",
        "vip_game",
        "vip_bbc",
        "vip_tiktok"
    ]:

        await context.bot.copy_message(
            chat_id=query.message.chat_id,
            from_chat_id=SOURCE_CHANNEL,
            message_id=2
        )

        await query.message.reply_text(
            get_payment_text(
                user,
                "20.000"
            ),
            parse_mode="HTML"
        )

    # =====================================================
    # VIP 25K (message_id=22) untuk: PANIS A, PANIS B
    # =====================================================

    elif query.data in [
        "vip_bocil_a",
        "vip_bocil_b"
    ]:

        await context.bot.copy_message(
            chat_id=query.message.chat_id,
            from_chat_id=SOURCE_CHANNEL,
            message_id=22
        )

        await query.message.reply_text(
            get_payment_text(
                user,
                "25.000"
            ),
            parse_mode="HTML"
        )

    # =====================================================
    # VIP ANDINI (harga 30.000, message_id=23)
    # =====================================================

    elif query.data == "vip_andini":

        await context.bot.copy_message(
            chat_id=query.message.chat_id,
            from_chat_id=SOURCE_CHANNEL,
            message_id=23
        )

        await query.message.reply_text(
            get_payment_text(
                user,
                "30.000"
            ),
            parse_mode="HTML"
        )

    # =====================================================
    # VIP ALL (message_id=24) harga 75.000
    # =====================================================

    elif query.data == "vip_all":

        await context.bot.copy_message(
            chat_id=query.message.chat_id,
            from_chat_id=SOURCE_CHANNEL,
            message_id=24
        )

        await query.message.reply_text(
            get_payment_text(
                user,
                "75.000"
            ),
            parse_mode="HTML"
        )

    # =====================================================
    # MENU (kembali ke utama)
    # =====================================================

    elif query.data == "menu":
        await query.message.delete()
        await send_main_menu_to_user(query.message.chat_id, user, context.bot)

# =========================================================
# MAIN
# =========================================================

def main():

    app = Application.builder().token(
        BOT_TOKEN
    ).build()

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_button
        )
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_photo
        )
    )

    # =====================================================
    # JOB QUEUE - JALANKAN SETIAP JAM
    # =====================================================
    app.job_queue.run_repeating(
        send_hourly_promo,
        interval=3600,
        first=0
    )

    print("Bot aktif 🚀")

    try:

        app.run_polling(
            drop_pending_updates=False
        )

    except Exception:

        traceback.print_exc()

if __name__ == "__main__":
    main()
