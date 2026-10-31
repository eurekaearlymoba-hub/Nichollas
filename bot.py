import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Mengatur log agar aktivitas bot terlihat di terminal
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Menyimpan daftar ID member grup secara sementara
GROUP_MEMBERS = set()

# --- FITUR 1: SIMPAN, PIN FORMAT, & BALASAN OTOMATIS KE CUSTOMER ---
async def keep_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    # Cek apakah perintah ini merupakan reply ke pesan format orderan
    if not message.reply_to_message:
        await message.reply_text("⚠️ Mohon reply ke pesan format orderan yang ingin disimpan!")
        return

    target_msg = message.reply_to_message
    customer = target_msg.from_user # Mendapatkan data customer yang mengirim format
    
    try:
        # 1. Pin pesan otomatis di grup
        await context.bot.pin_chat_message(
            chat_id=message.chat_id, 
            message_id=target_msg.message_id
        )
        
        # 2. Balasan otomatis ke customer (reply langsung ke pesan customer)
        balasan_customer = (
            f"Halo Kak {customer.first_name}! Format orderan kamu sudah kami **keep** dan catat ya. "
            f"Mohon tunggu sebentar, admin kami akan segera memproses pesananmu! ✨"
        )
        await target_msg.reply_text(balasan_customer, parse_mode="Markdown")

        # 3. Membuat Inline Keyboard (Tombol Interaktif) untuk Admin
        keyboard = [
            [
                InlineKeyboardButton("🙋‍♂️ Izin Ambil (/izin)", callback_data="btn_izin"),
                InlineKeyboardButton("💳 Lanjut Pembayaran (/pay)", callback_data="btn_pay")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Konfirmasi ke grup bahwa format berhasil disimpan dengan tombol
        await message.reply_text(
            "✅ **Format berhasil di-keep, di-pin, dan dibalas ke customer!**\nSilakan pilih aksi di bawah ini:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.reply_text(f"❌ Gagal mem-pin pesan. Pastikan bot adalah Admin dengan hak akses Pin Messages.\nError: {e}")


# --- FITUR 2: IZIN AMBIL ORDERAN & ABSEN ---
async def izin_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user
    
    admin_name = user.full_name
    
    rekap_teks = (
        f"📝 **REKAP ABSEN ORDERAN**\n"
        f"• Admin / Staff: {admin_name} (@{user.username if user.username else 'no_username'})\n"
        f"• Status: Mengambil orderan ini.\n"
        f"• Waktu: Tercatat otomatis."
    )
    
    await message.reply_text(rekap_teks, parse_mode="Markdown")


# --- HANDLER UNTUK TOMBOL INTERAKTIF (INLINE BUTTON) ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer() # Menghilangkan loading di tombol

    if query.data == "btn_izin":
        rekap_teks = (
            f"📝 **REKAP ABSEN ORDERAN (via Tombol)**\n"
            f"• Admin / Staff: {user.full_name} (@{user.username if user.username else 'no_username'})\n"
            f"• Status: Mengambil orderan ini."
        )
        await query.message.reply_text(rekap_teks, parse_mode="Markdown")
        
    elif query.data == "btn_pay":
        await query.message.reply_text(
            f"💳 **INSTRUKSI PEMBAYARAN**\n"
            f"Diproses oleh: {user.full_name}\n"
            f"Silakan kirimkan rincian nominal pembayaran yang harus diselesaikan oleh customer.",
            parse_mode="Markdown"
        )


# --- FITUR 3: TAG SELURUH MEMBER GRUP ---
async def tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⚠️ Perintah ini hanya bisa digunakan di dalam grup!")
        return

    pesan_broadcast = " ".join(context.args) if context.args else "Halo semuanya, ada pengumuman penting!"

    if not GROUP_MEMBERS:
        await update.message.reply_text(
            f"📢 **PENGUMUMAN UNTUK SEMUA MEMBER**\n\n{pesan_broadcast}",
            parse_mode="Markdown"
        )
        return

    mentions = [f"[Member](tg://user?id={member_id})" for member_id in GROUP_MEMBERS]
    tag_string = " ".join(mentions)
    final_text = f"📢 **PENGUMUMAN MASSAL**\n{pesan_broadcast}\n\n{tag_string}"
    
    await update.message.reply_text(final_text, parse_mode="Markdown")


# Merekam otomatis user yang aktif di grup agar masuk daftar /tagall
async def track_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and update.effective_user:
        if update.effective_chat.type in ["group", "supergroup"]:
            GROUP_MEMBERS.add(update.effective_user.id)


def main():
    # Mengambil token bot secara otomatis dari environment variable GitHub Secrets
    TOKEN = "9120926220:AAFFxtB18zse5fiAoffLO4VkGnwAHsvzrvg"
    
    app = Application.builder().token(TOKEN).build()

    # Mendaftarkan Handler Perintah & Callback Tombol
    app.add_handler(CommandHandler("keep", keep_format))
    app.add_handler(CommandHandler("izin", izin_order))
    app.add_handler(CommandHandler("tagall", tag_all))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Merekam pesan masuk untuk mendata member secara otomatis
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_members))

    print("Bot dengan tombol interaktif dan balasan otomatis sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
