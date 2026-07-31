import os
import math
import logging
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from locations import LOCATIONS
from geocode import build_geocached_locations

# ─── Setup ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
WIB = pytz.timezone("Asia/Jakarta")

# Koordinat diverifikasi Google Maps saat startup
VERIFIED_LOCATIONS: dict = {}

# ─── Utility ────────────────────────────────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon/2)**2)
    return R * 2 * math.asin(math.sqrt(a))


def get_current_slot():
    hour = datetime.now(WIB).hour
    if 3 <= hour <= 6:
        return "03:00-06:59"
    elif 7 <= hour <= 11:
        return "07:00-11:59"
    elif 12 <= hour <= 15:
        return "12:00-15:59"
    elif 16 <= hour <= 20:
        return "16:00-20:59"
    else:
        return "21:00-02:59"


def get_nearby(user_lat, user_lon, slot, max_km):
    results = []
    for name, lat, lon in VERIFIED_LOCATIONS.get(slot, []):
        dist = haversine(user_lat, user_lon, lat, lon)
        if dist <= max_km:
            # Link Google Maps langsung ke nama lokasi (lebih user-friendly)
            gmaps = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            results.append((name, dist, gmaps))
    results.sort(key=lambda x: x[1])
    return results


def format_location_list(locations, slot, radius_km):
    now_str = datetime.now(WIB).strftime("%H:%M WIB")
    lines = [
        f"🚖 *Rekomendasi Lokasi Bluebird*",
        f"🕐 Slot: `{slot}` | Sekarang: `{now_str}`",
        f"📍 Radius: *{radius_km} km* | Ditemukan: *{len(locations)} lokasi*",
        "",
    ]
    for i, (name, dist, gmaps) in enumerate(locations, 1):
        lines.append(f"*{i}. {name}*")
        lines.append(f"   📏 {dist:.1f} km · [Buka Maps]({gmaps})")
        lines.append("")
    return "\n".join(lines)

# ─── Handlers ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[KeyboardButton("📍 Kirim Lokasi Saya", request_location=True)]]
    markup = ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "👋 Halo, Driver Bluebird!\n\n"
        "Bot ini akan memberikan rekomendasi lokasi jemput berdasarkan "
        "*posisi* dan *jam* kamu sekarang.\n\n"
        "Tap tombol di bawah untuk kirim lokasi kamu 👇",
        parse_mode="Markdown",
        reply_markup=markup,
    )


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    user_lat, user_lon = loc.latitude, loc.longitude
    slot = get_current_slot()

    context.user_data["lat"] = user_lat
    context.user_data["lon"] = user_lon
    context.user_data["slot"] = slot

    await update.message.reply_text("🔍 Mencari lokasi terdekat...")

    nearby = get_nearby(user_lat, user_lon, slot, max_km=7)

    if nearby:
        text = format_location_list(nearby, slot, radius_km=7)
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        await update.message.reply_text(
            "✅ Selesai! Mau cari lagi? Kirim lokasi ulang kapan saja."
        )
    else:
        keyboard = [[InlineKeyboardButton("🔍 Perluas ke 10 km", callback_data="expand_10")]]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"⚠️ Tidak ada lokasi rekomendasi dalam *7 km* untuk slot *{slot}*.\n\n"
            "Mau perluas pencarian hingga *10 km*?",
            parse_mode="Markdown",
            reply_markup=markup,
        )


async def handle_expand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_lat = context.user_data.get("lat")
    user_lon = context.user_data.get("lon")
    slot = context.user_data.get("slot")

    if not user_lat or not user_lon:
        await query.edit_message_text("⚠️ Sesi habis. Silakan kirim lokasi ulang.")
        return

    nearby = get_nearby(user_lat, user_lon, slot, max_km=10)

    if nearby:
        text = format_location_list(nearby, slot, radius_km=10)
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
    else:
        await query.edit_message_text(
            f"😔 Tidak ada lokasi rekomendasi dalam *10 km* untuk slot *{slot}*.\n\n"
            "Coba lagi di jam berikutnya ya, Driver!",
            parse_mode="Markdown",
        )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Cara pakai bot ini:*\n\n"
        "1️⃣ Ketik /start\n"
        "2️⃣ Tap tombol *📍 Kirim Lokasi Saya*\n"
        "3️⃣ Bot tampilkan lokasi rekomendasi dalam 7 km sesuai jam sekarang\n"
        "4️⃣ Jika tidak ada, tap tombol untuk perluas ke 10 km\n\n"
        "📌 *Slot waktu:*\n"
        "• 03.00–06.59 → Perumahan Cinere/Pamulang\n"
        "• 07.00–11.59 → Perkantoran Pancoran/SCBD\n"
        "• 12.00–15.59 → Mall & RS Jakarta\n"
        "• 16.00–20.59 → Hotel & Kawasan Pusat\n"
        "• 21.00–02.59 → Hiburan & Mall Malam\n\n"
        "Untuk mulai ulang ketik /start",
        parse_mode="Markdown",
    )

# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    global VERIFIED_LOCATIONS

    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable tidak ditemukan!")

    # Geocode semua lokasi saat startup (pakai cache kalau sudah ada)
    logger.info("Memverifikasi koordinat lokasi via Google Maps...")
    VERIFIED_LOCATIONS = build_geocached_locations(LOCATIONS)
    logger.info("Koordinat siap!")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(CallbackQueryHandler(handle_expand, pattern="^expand_10$"))

    logger.info("Bot Bluebird berjalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
