import telebot
import random
import time
import threading
import json
import os

TOKEN = '7102389575:AAHMc_209ElVL5Qlv7-bLhCkMIiVD9T8Obw'
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

sponsor_channels = [
    '@Vsi_PROMO',
    '@uaclub_casinoman'
]

ADMIN_ID = 7262164512
DATA_FILE = 'users_data.json'

# Жарти для фарт-картки
jokes = [
    "Фарт постукав — не прикидайся, що тебе немає вдома.",
    "Краще один раз пощастити, ніж сто разів пошкодувати.",
    "Фарт — це коли за тебе грають навіть ліхтарі на вулиці.",
    "Якщо не пощастило, почекай – скоро повезе!",
]

# Завантаження даних
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        users_data = json.load(f)
        users_data = {int(k): v for k, v in users_data.items()}
else:
    users_data = {}

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump({str(k): v for k, v in users_data.items()}, f, indent=4)

# Клавіатура з кнопками
main_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.row('🎁 Щоденний фарт', '🃏 Фарт-картка')
main_keyboard.row('🏆 Розіграші', '👯 Запросити друга')
main_keyboard.row('📊 Мій профіль', '📢 Спонсори / Новини')
main_keyboard.row('⭐️ Топ 5 гравців')
main_keyboard.row('📣 Додати свій канал у Jackpot Pulse')

# Привітальний текст
welcome_text = """<b>🎰 Ласкаво просимо в Jackpot Pulse!</b>

<b>✅ Що тут відбувається:</b>
• 🎁 Щодня заходиш → отримуєш бонус PulseCoins (15–100)
• 🃏 Відкриваєш Фарт-картки → ловиш призи
• 👯 Запрошуєш друзів → ще більше PulseCoins
• 🏆 Участь у розіграшах реальних грошей

<b>⚠️ Щоб користуватися ботом, потрібно бути підписаним на наші спонсорські канали.</b>
<i>⚠️ Якщо відписуєшся від будь-якого каналу — всі бонуси та участь анулюються!</i>
<b>🔥 Натискай кнопку нижче, щоб почати свій шлях до джекпоту!</b>"""

def get_channels_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    for ch in sponsor_channels:
        markup.add(telebot.types.InlineKeyboardButton(text=ch, url=f"https://t.me/{ch.strip('@')}"))
    # Додаємо кнопку перевірки підписки
    markup.add(telebot.types.InlineKeyboardButton(text="✅ Перевірити підписку", callback_data="check_subs"))
    return markup

def check_subscriptions(user_id):
    try:
        for channel in sponsor_channels:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        return True
    except Exception as e:
        print("Subscription check error:", e)
        return False

def reset_user(user_id):
    users_data[user_id] = {
        'balance': 0,
        'last_bonus': 0,
        'last_card': 0,
        'streak': 0,
        'referrals': 0,
        'tickets': 0,
        'last_active': int(time.time()),
        'referral_from': None,
        'lottery_participation': False
    }
    save_data()

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    ref_id = None

    if message.text:
        args = message.text.split()
        if len(args) > 1:
            try:
                ref_id = int(args[1])
            except:
                pass
        else:
            if len(message.text) > 6:
                try:
                    ref_id = int(message.text[6:])
                except:
                    pass

    if user_id not in users_data:
        users_data[user_id] = {
            'balance': 0,
            'last_bonus': 0,
            'last_card': 0,
            'streak': 0,
            'referrals': 0,
            'tickets': 0,
            'last_active': int(time.time()),
            'referral_from': None,
            'lottery_participation': False
        }
        if ref_id and ref_id != user_id:
            users_data[user_id]['referral_from'] = ref_id
            if ref_id in users_data:
                users_data[ref_id]['referrals'] += 1
                try:
                    bot.send_message(ref_id, f"<b>🎉 У тебе новий реферал: {message.from_user.first_name} (@{message.from_user.username})</b>")
                except:
                    pass
    else:
        users_data[user_id]['last_active'] = int(time.time())

    save_data()
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard)
    bot.send_message(message.chat.id, "<b>🔗 Наші канали для підписки:</b>", reply_markup=get_channels_buttons())

@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def callback_check_subs(call):
    user_id = call.from_user.id
    if check_subscriptions(user_id):
        bot.answer_callback_query(call.id, "✅ Всі канали підписані!")
    else:
        reset_user(user_id)
        bot.answer_callback_query(call.id, "❌ Ти відписався від одного з каналів. Твої бонуси анульовані!")
        bot.send_message(user_id, "<b>❗️ Ти відписався від наших спонсорських каналів.\nУсі бонуси скинуто. Підпишись знову, щоб грати!</b>")

@bot.message_handler(func=lambda m: m.text == '🎁 Щоденний фарт')
def daily_bonus(message):
    user_id = message.from_user.id
    if not check_subscriptions(user_id):
        bot.send_message(message.chat.id, "<b>Спершу підпишись на всі наші спонсорські канали!</b>", reply_markup=main_keyboard)
        return

    now = int(time.time())
    last = users_data[user_id]['last_bonus']
    users_data[user_id]['last_active'] = now

    if now - last < 86400:
        bot.send_message(message.chat.id, "<b>🕐 Ти вже сьогодні отримав фарт! Завітай завтра 😉</b>", reply_markup=main_keyboard)
    else:
        bonus = random.randint(15, 100)
        users_data[user_id]['balance'] += bonus
        users_data[user_id]['last_bonus'] = now
        users_data[user_id]['streak'] += 1
        save_data()
        bot.send_message(message.chat.id, f"<b>🎉 Плюс удачі {bonus} фартів! 🎉</b>\n\n", reply_markup=main_keyboard)
        bot.send_message(message.chat.id,
            f"<b>🔮 Пульс удачі б’ється рівно 👊</b>\n\n"
            f"<b>+{bonus} PulseCoins 💸</b>\n"
            f"<b>🔥 Стрік:</b> {users_data[user_id]['streak']} дні(в)",
            reply_markup=main_keyboard)

@bot.message_handler(func=lambda m: m.text == '🃏 Фарт-картка')
def fart_card(message):
    user_id = message.from_user.id
    if not check_subscriptions(user_id):
        bot.send_message(message.chat.id, "<b>⚠️ Спершу підпишись на всі наші спонсорські канали!</b>", reply_markup=main_keyboard)
        return

    now = int(time.time())
    last_card = users_data[user_id].get('last_card', 0)
    if now - last_card < 86400:
        bot.send_message(message.chat.id, "<b>⏳ Фарт-картку можна відкривати лише раз на добу. Заходь завтра!</b>", reply_markup=main_keyboard)
        return

    users_data[user_id]['last_card'] = now
    users_data[user_id]['last_active'] = now

    outcomes = [
        ("💰 <b>+50 PulseCoins!</b>", 50),
        ("🎟 <b>Квиток на розіграш!</b>", 0),
        (f"🤣 <i>{random.choice(jokes)}</i>", 0),
        ("🤷‍♂️ <b>Нічого не випало цього разу. Спробуй ще!</b>", 0)
    ]
    text, coins = random.choice(outcomes)
    if "Квиток" in text:
        users_data[user_id]['tickets'] += 1
    if coins > 0:
        users_data[user_id]['balance'] += coins
    save_data()
    bot.send_message(message.chat.id, f"<b>🃏 Твоя фарт-картка показує:</b>\n\n{text}", reply_markup=main_keyboard)

# Обробник кнопки "📢 Спонсори / Новини"
@bot.message_handler(func=lambda m: m.text == '📢 Спонсори / Новини')
def sponsors_news(message):
    user_id = message.from_user.id
    if not check_subscriptions(user_id):
        bot.send_message(message.chat.id, "<b>⚠️ Підпишись на всі спонсорські канали, щоб користуватися ботом.</b>", reply_markup=main_keyboard)
        return

    text = "<b>📢 Наші спонсорські канали та новини:</b>"
    markup = telebot.types.InlineKeyboardMarkup()
    for ch in sponsor_channels:
        markup.add(telebot.types.InlineKeyboardButton(text=ch, url=f"https://t.me/{ch.strip('@')}"))
    markup.add(telebot.types.InlineKeyboardButton(text="✅ Перевірити підписку", callback_data="check_subscription"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

# Обробник callback кнопки "✅ Перевірити підписку"
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription_callback(call):
    user_id = call.from_user.id
    if check_subscriptions(user_id):
        bot.answer_callback_query(call.id, "✅ Ти підписаний на всі канали! Продовжуй у тому ж дусі 🥳")
    else:
        bot.answer_callback_query(call.id, "❌ Ти не підписаний на всі канали. Підпишись, будь ласка!")

@bot.message_handler(func=lambda m: m.text == '📊 Мій профіль')
def my_profile(message):
    user_id = message.from_user.id
    data = users_data.get(user_id)
    if data:
        users_data[user_id]['last_active'] = int(time.time())
        save_data()
        bot.send_message(message.chat.id,
            f"<b>📊 Твій профіль:</b>\n\n"
            f"🪙 PulseCoins: {data['balance']}\n"
            f"📆 Стрік: {data['streak']} дні(в)\n"
            f"👥 Запрошено друзів: {data['referrals']}\n"
            f"🎟 Квитків на розіграш: {data['tickets']}",
            reply_markup=main_keyboard)
    else:
        bot.send_message(message.chat.id, "<b>❗️ Профіль ще порожній. Натисни /start</b>", reply_markup=main_keyboard)

@bot.message_handler(func=lambda m: m.text == '⭐️ Топ 5 гравців')
def show_top5(message):
    if not users_data:
        bot.send_message(message.chat.id, "<b>❌ Поки що немає гравців.</b>")
        return
    top5 = sorted(users_data.items(), key=lambda x: x[1].get('balance', 0), reverse=True)[:5]

    text = "<b>🏆 Топ 5 гравців за PulseCoins:</b>\n\n"
    for i, (user_id, data) in enumerate(top5, start=1):
        try:
            user = bot.get_chat(user_id)
            username = f"@{user.username}" if user.username else str(user_id)
        except:
            username = str(user_id)
        text += f"{i}. {username} — <b>{data.get('balance',0)}</b> PulseCoins\n"

    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == '👯 Запросити друга')
def invite_friend(message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/JackpotPulse_bot?start={user_id}"
    bot.send_message(message.chat.id,
        f"<b>👯 Запроси друзів!</b>\n\n"
        f"🔗 Твоє посилання: {ref_link}\n"
        f"✅ За кожного — +20 PulseCoins\n🎯 Активність 3 дні — ще +10",
        reply_markup=main_keyboard)

@bot.message_handler(func=lambda m: m.text == '🏆 Розіграші')
def lottery(message):
    user_id = message.from_user.id
    if not check_subscriptions(user_id):
        bot.send_message(message.chat.id, "<b>⚠️ Спершу підпишись на всі наші спонсорські канали!</b>", reply_markup=main_keyboard)
        return
    tickets = users_data.get(user_id, {}).get('tickets', 0)
    info = (
        "<b>🏆 Jackpot Pulse — Розіграші</b>\n\n"
        "🎁 Приз: 500 грн - (5 переможців по 100 грн)\n📆 Щовівторка о 19:00\n\n"
        "🔸 Як взяти участь:\n• 1000 PulseCoins\n• або 25 друзів\n• або <b>15 квитків</b> 🎟\n\n"
        f"🎟 У тебе: {tickets} квитків\n\n"
        "Натисни кнопку нижче, щоб взяти участь!"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ Взяти участь", callback_data="join_lottery"))
    bot.send_message(message.chat.id, info, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "join_lottery")
def handle_join_lottery(call):
    user_id = call.from_user.id
    user = users_data.get(user_id)
    if not user:
        bot.answer_callback_query(call.id, "❗️ Спочатку натисни /start")
        return

    if user['tickets'] >= 15:
        user['tickets'] -= 15
        method = "квитки"
    elif user['balance'] >= 1000:
        user['balance'] -= 1000
        method = "PulseCoins"
    elif user['referrals'] >= 25:
        user['referrals'] -= 25
        method = "друзі"
    else:
        bot.answer_callback_query(call.id, "❌ Недостатньо умов для участі!")
        return# Обробник callback кнопки "✅ Перевірити підписку"
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription_callback(call):
    user_id = call.from_user.id
    if check_subscriptions(user_id):
        bot.answer_callback_query(call.id, "✅ Ти підписаний на всі канали! Продовжуй у тому ж дусі 🥳")
    else:
        bot.answer_callback_query(call.id, "❌ Ти не підписаний на всі канали. Підпишись, будь ласка!")

@bot.message_handler(func=lambda m: m.text == '📊 Мій профіль')
def my_profile(message):
    user_id = message.from_user.id
    data = users_data.get(user_id)
    if data:
        users_data[user_id]['last_active'] = int(time.time())
        save_data()
        bot.send_message(message.chat.id,
            f"<b>📊 Твій профіль:</b>\n\n"
            f"🪙 PulseCoins: {data['balance']}\n"
            f"📆 Стрік: {data['streak']} дні(в)\n"
            f"👥 Запрошено друзів: {data['referrals']}\n"
            f"🎟 Квитків на розіграш: {data['tickets']}",
            reply_markup=main_keyboard)
    else:
        bot.send_message(message.chat.id, "<b>❗️ Профіль ще порожній. Натисни /start</b>", reply_markup=main_keyboard)

@bot.message_handler(func=lambda m: m.text == '⭐️ Топ 5 гравців')
def show_top5(message):
    if not users_data:
        bot.send_message(message.chat.id, "<b>❌ Поки що немає гравців.</b>")
        return
    top5 = sorted(users_data.items(), key=lambda x: x[1].get('balance', 0), reverse=True)[:5]

    text = "<b>🏆 Топ 5 гравців за PulseCoins:</b>\n\n"
    for i, (user_id, data) in enumerate(top5, start=1):
        try:
            user = bot.get_chat(user_id)
            username = f"@{user.username}" if user.username else str(user_id)
        except:
            username = str(user_id)
        text += f"{i}. {username} — <b>{data.get('balance',0)}</b> PulseCoins\n"

    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == '👯 Запросити друга')
def invite_friend(message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/JackpotPulse_bot?start={user_id}"
    bot.send_message(message.chat.id,
        f"<b>👯 Запроси друзів!</b>\n\n"
        f"🔗 Твоє посилання: {ref_link}\n"
        f"✅ За кожного — +20 PulseCoins\n🎯 Активність 3 дні — ще +10",
        reply_markup=main_keyboard)

@bot.message_handler(func=lambda m: m.text == '🏆 Розіграші')
def lottery(message):
    user_id = message.from_user.id
    if not check_subscriptions(user_id):
        bot.send_message(message.chat.id, "<b>⚠️ Спершу підпишись на всі наші спонсорські канали!</b>", reply_markup=main_keyboard)
        return
    tickets = users_data.get(user_id, {}).get('tickets', 0)
    info = (
        "<b>🏆 Jackpot Pulse — Розіграші</b>\n\n"
        "🎁 Приз: 500 грн - (5 переможців по 100 грн)\n📆 Щовівторка о 19:00\n\n"
        "🔸 Як взяти участь:\n• 1000 PulseCoins\n• або 25 друзів\n• або <b>15 квитків</b> 🎟\n\n"
        f"🎟 У тебе: {tickets} квитків\n\n"
        "Натисни кнопку нижче, щоб взяти участь!"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ Взяти участь", callback_data="join_lottery"))
    bot.send_message(message.chat.id, info, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "join_lottery")
def handle_join_lottery(call):
    user_id = call.from_user.id
    user = users_data.get(user_id)
    if not user:
        bot.answer_callback_query(call.id, "❗️ Спочатку натисни /start")
        return

    if user['tickets'] >= 15:
        user['tickets'] -= 15
        method = "квитки"
    elif user['balance'] >= 1000:
        user['balance'] -= 1000
        method = "PulseCoins"
    elif user['referrals'] >= 25:
        user['referrals'] -= 25
        method = "друзі"
    else:
        bot.answer_callback_query(call.id, "❌ Недостатньо умов для участі!")
        return# Обробник callback кнопки "✅ Перевірити підписку"
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription_callback(call):
    user_id = call.from_user.id
    if check_subscriptions(user_id):
        bot.answer_callback_query(call.id, "✅ Ти підписаний на всі канали! Продовжуй у тому ж дусі 🥳")
    else:
        bot.answer_callback_query(call.id, "❌ Ти не підписаний на всі канали. Підпишись, будь ласка!")

@bot.message_handler(func=lambda m: m.text == '📊 Мій профіль')
def my_profile(message):
    user_id = message.from_user.id
    data = users_data.get(user_id)
    if data:
        users_data[user_id]['last_active'] = int(time.time())
        save_data()
        bot.send_message(message.chat.id,
            f"<b>📊 Твій профіль:</b>\n\n"
            f"🪙 PulseCoins: {data['balance']}\n"
            f"📆 Стрік: {data['streak']} дні(в)\n"
            f"👥 Запрошено друзів: {data['referrals']}\n"
            f"🎟 Квитків на розіграш: {data['tickets']}",
            reply_markup=main_keyboard)
    else:
        bot.send_message(message.chat.id, "<b>❗️ Профіль ще порожній. Натисни /start</b>", reply_markup=main_keyboard)

@bot.message_handler(func=lambda m: m.text == '⭐️ Топ 5 гравців')
def show_top5(message):
    if not users_data:
        bot.send_message(message.chat.id, "<b>❌ Поки що немає гравців.</b>")
        return
    top5 = sorted(users_data.items(), key=lambda x: x[1].get('balance', 0), reverse=True)[:5]

    text = "<b>🏆 Топ 5 гравців за PulseCoins:</b>\n\n"
    for i, (user_id, data) in enumerate(top5, start=1):
        try:
            user = bot.get_chat(user_id)
            username = f"@{user.username}" if user.username else str(user_id)
        except:
            username = str(user_id)
        text += f"{i}. {username} — <b>{data.get('balance',0)}</b> PulseCoins\n"

    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == '👯 Запросити друга')
def invite_friend(message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/JackpotPulse_bot?start={user_id}"
    bot.send_message(message.chat.id,
        f"<b>👯 Запроси друзів!</b>\n\n"
        f"🔗 Твоє посилання: {ref_link}\n"
        f"✅ За кожного — +20 PulseCoins\n🎯 Активність 3 дні — ще +10",
        reply_markup=main_keyboard)

@bot.message_handler(func=lambda m: m.text == '🏆 Розіграші')
def lottery(message):
    user_id = message.from_user.id
    if not check_subscriptions(user_id):
        bot.send_message(message.chat.id, "<b>⚠️ Спершу підпишись на всі наші спонсорські канали!</b>", reply_markup=main_keyboard)
        return
    tickets = users_data.get(user_id, {}).get('tickets', 0)
    info = (
        "<b>🏆 Jackpot Pulse — Розіграші</b>\n\n"
        "🎁 Приз: 500 грн - (5 переможців по 100 грн)\n📆 Щовівторка о 19:00\n\n"
        "🔸 Як взяти участь:\n• 1000 PulseCoins\n• або 25 друзів\n• або <b>15 квитків</b> 🎟\n\n"
        f"🎟 У тебе: {tickets} квитків\n\n"
        "Натисни кнопку нижче, щоб взяти участь!"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ Взяти участь", callback_data="join_lottery"))
    bot.send_message(message.chat.id, info, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "join_lottery")
def handle_join_lottery(call):
    user_id = call.from_user.id
    user = users_data.get(user_id)
    if not user:
        bot.answer_callback_query(call.id, "❗️ Спочатку натисни /start")
        return

    if user['tickets'] >= 15:
        user['tickets'] -= 15
        method = "квитки"
    elif user['balance'] >= 1000:
        user['balance'] -= 1000
        method = "PulseCoins"
    elif user['referrals'] >= 25:
        user['referrals'] -= 25
        method = "друзі"
    else:
        bot.answer_callback_query(call.id, "❌ Недостатньо умов для участі!")
        return

@bot.callback_query_handler(func=lambda call: call.data == "join_lottery")
def handle_join_lottery(call):
    user_id = call.from_user.id  # отримуємо user_id
    if user_id not in users_data:
        # ініціалізуємо дані користувача, якщо немає
        users_data[user_id] = {
            'balance': 0,
            'last_bonus': 0,
            'last_card': 0,
            'streak': 0,
            'referrals': 0,
            'tickets': 0,
            'last_active': int(time.time()),
            'referral_from': None,
            'lottery_participation': False
        }
    # Оновлюємо поле
    users_data[user_id]['lottery_participation'] = True
    save_data()  # зберігаємо після оновлення

    bot.answer_callback_query(call.id, "✅ Ти успішно приєднався до розіграшу!")

try:
        user_info = bot.get_chat(user_id)
        uname = f"@{user_info.username}" if user_info.username else user_info.first_name
        bot.send_message(ADMIN_ID, f"🎟 Новий учасник розіграшу: <b>{uname}</b>, через {method}")
except:
        pass

@bot.message_handler(commands=['runlottery'])
def run_lottery(message):
    if message.from_user.id != ADMIN_ID:
        return

    participants = {uid: data for uid, data in users_data.items() if data.get('lottery_participation', False)}
    if not participants:
        bot.send_message(message.chat.id, "<b>❌ Немає учасників для розіграшу.</b>")
        return

    user_ids = list(participants.keys())
    random.shuffle(user_ids)
    winners = user_ids[:5]

    result = "<b>🎉 Результати розіграшу:</b>\n\n"

    for idx, uid in enumerate(winners, start=1):
        try:
            user_info = bot.get_chat(uid)
            uname = f"@{user_info.username}" if user_info.username else f"<code>{uid}</code>"
            result += f"{idx}. {uname}\n"
            # Знімаємо бонуси учасника
            if users_data[uid]['tickets'] >= 5:
                users_data[uid]['tickets'] -= 5
            elif users_data[uid]['balance'] >= 500:
                users_data[uid]['balance'] -= 500
            elif users_data[uid]['referrals'] >= 15:
                users_data[uid]['referrals'] -= 25
            users_data[uid]['lottery_participation'] = False
            save_data()
        except Exception as e:
            result += f"{idx}. ❌ Користувач {uid} (помилка: {e})\n"

    bot.send_message(message.chat.id, result)

@bot.message_handler(commands=['top'])
def top_rating(message):
    sorted_users = sorted(users_data.items(), key=lambda x: x[1]['balance'], reverse=True)
    top_5 = sorted_users[:5]
    text = "<b>🔥 Топ 5 користувачів за PulseCoins:</b>\n\n"
    for i, (uid, data) in enumerate(top_5, start=1):
        try:
            user_info = bot.get_chat(uid)
            uname = f"@{user_info.username}" if user_info.username else user_info.first_name
        except:
            uname = str(uid)
        text += f"{i}. {uname} — <b>{data['balance']}</b>\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == '📣 Додати свій канал у Jackpot Pulse')
def add_channel_request(message):
    bot.send_message(
        message.chat.id,
        "<b>📣 Хочеш додати свій канал у Jackpot Pulse?</b>\n\n"
        "Звертайся до наших менеджерів:\n"
        "👤 @vsi_promo_admin\n"
        "👤 @oleksandra_managerr\n\n"
        "Вони допоможуть тобі з рекламою та співпрацею!",
        reply_markup=main_keyboard
    )

# Адмінська команда для розсилки промо всім користувачам
@bot.message_handler(commands=['send_promo'])
def send_promo_to_all(message):
    if message.from_user.id != ADMIN_ID:
        return

    promo_text = (
        "<b>📣 УВАГА ВСІМ ВЛАСНИКАМ КАНАЛІВ!</b>\n\n"
        "⭐️ <b>Хочеш отримати безкоштовне спонсорство в Jackpot Pulse?</b> ⭐️\n\n"
        "🎯 Приведи найбільше рефералів сьогодні — і твій канал БЕЗКОШТОВНО отримає рекламу в нашому боті на 1 день! 🚀\n\n"
        "🔥 <i>Це чудовий шанс збільшити свою аудиторію і отримати крутий бонус!</i>\n\n"
        "👥 Чим більше активних підписників ти приведеш — тим більша твоя перемога!\n\n"
        "📩 Пиши менеджерам для участі:\n"
        "👤 @vsi_promo_admin\n"
        "👤 @oleksandra_managerr\n\n"
        "Не пропусти! 🎉"
    )

    count = 0
    for user_id in users_data.keys():
        try:
            bot.send_message(user_id, promo_text)
            count += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"Помилка надсилання {user_id}: {e}")

    bot.send_message(message.chat.id, f"Повідомлення надіслано {count} користувачам.")
# Функція для автоматичної перевірки підписок (можна викликати раз на годину/день)
def auto_check_subscriptions():
    while True:
        print("Перевірка підписок користувачів...")
        for user_id in list(users_data.keys()):
            if not check_subscriptions(user_id):
                reset_user(user_id)
                try:
                    bot.send_message(user_id, "<b>❗️ Ти відписався від спонсорських каналів, всі бонуси анульовано. Підпишись знову, щоб грати!</b>")
                except:
                    pass
        time.sleep(3600)  # перевіряти щогодини

# Запускаємо фоновий потік перевірки підписок
threading.Thread(target=auto_check_subscriptions, daemon=True).start()

print("Бот запущено...")
bot.infinity_polling()
