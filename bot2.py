import telebot
import random
import time
import threading
import json
import os
import re
daily_top5 = []
TASK_FILE = 'task.json'
current_task = "❗️Завдання ще не встановлено."
current_task_reward = 50  # Скільки PulseToken давати за виконання


# Ось тут:
current_task = "Виконайте завдання: Підпишіться на канал X і надішліть повідомлення."

TOKEN = '7102389575:AAGNcHAzhyut7t-pL0CO0U8UFw3UtDaExlw'
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

sponsor_channels = [
    '@Vsi_PROMO',
    '@casinomania_official',
    '@Jackpot_Pulse',
    '@gospodispin',
    '@Lucky_Club_777',
    '@PROMO_OT_SAINT'
]
ADMIN_GROUP_ID = -1002729364136
ADMIN_ID = 7262164512
DATA_FILE = 'users_data.json'
PROMO_FILE = 'promo_codes.json'

jokes = [
    "Фарт постукав — не прикидайся, що тебе немає вдома.",
    "Краще один раз пощастити, ніж сто разів пошкодувати.",
    "Фарт — це коли за тебе грають навіть ліхтарі на вулиці.",
    "Якщо не пощастило, почекай – скоро повезе!",
]

def is_admin(message):
    return (message.from_user.id == ADMIN_ID) or (message.chat.id == ADMIN_GROUP_ID)

def load_promos():
    try:
        with open(PROMO_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_promos(data):
    with open(PROMO_FILE, 'w') as f:
        json.dump(data, f, indent=4)


if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        users_data = json.load(f)
        users_data = {int(k): v for k, v in users_data.items()}
else:
    users_data = {}

if os.path.exists(TASK_FILE):
    with open(TASK_FILE, 'r', encoding='utf-8') as f:
        task_data = json.load(f)
        current_task = task_data.get("text", "❗️Завдання ще не встановлено.")
        current_task_reward = task_data.get("reward", 50)

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({str(k): v for k, v in users_data.items()}, f, indent=4, ensure_ascii=False)

def update_daily_top5():
    global daily_top5
    sorted_users = sorted(users_data.items(), key=lambda x: x[1]['balance'], reverse=True)
    daily_top5 = sorted_users[:5]

main_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.row('🎁 Щоденний фарт', '🃏 Фарт-картка')
main_keyboard.row('🏆 Розіграші', '👯 Запросити друга')
main_keyboard.row('📊 Мій профіль', '📢 Спонсори / Новини')
main_keyboard.row('⭐️ Топ 5 гравців', '📣 Додати свій канал у Jackpot Pulse')
main_keyboard.row('💼 Баланс / Промокод', '📝 Завдання')  # Кнопка для завдання

welcome_text = """<b>🎰 Ласкаво просимо в Jackpot Pulse!</b>

<b>✅ Що тут відбувається:</b>
• 🎁 Щодня заходиш → отримуєш бонус PulseCoins (15–100)
• 🃏 Відкриваєш Фарт-картки → ловиш призи
• 👯 Запрошуєш друзів → ще більше PulseCoins
• 🏆 Участь у розіграшах реальних грошей

<b>⚠️ Щоб користуватися ботом, потрібно бути підписаним на наші спонсорські канали.</b>
<i>⚠️ Якщо відписуєшся від будь-якого каналу — всі бонуси та участь анулюються!</i>
<b>🔥 Натискай кнопку нижче, щоб почати свій шлях до джекпоту!</b>"""


@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    ref_id = None

    if user_id not in users_data:
        users_data[user_id] = {
            'balance': 0,
            'pulse_token': 0,
            'last_bonus': 0,
            'last_card': 0,
            'streak': 0,
            'referrals': 0,
            'referrals_today': 0,
            'tickets': 0,
            'last_active': int(time.time()),
            'referral_from': None,
            'lottery_participation': False,
            'last_task_done': 0,
            'phone_number': None,
            'last_unsubscribed_time': 0,
            'last_task_request': 0
        }

    if message.text:
        args = message.text.split()
        if len(args) > 1:
            try:
                ref_id = int(args[1])
            except:
                pass
        elif len(message.text) > 6:
            try:
                ref_id = int(message.text[6:])
            except:
                pass

    # ✅ РЕФЕРАЛЬНА ЛОГІКА — ТУТ ВСЕРЕДИНІ ФУНКЦІЇ
    if ref_id and ref_id != user_id and users_data[user_id].get('referral_from') is None:
        users_data[user_id]['referral_from'] = ref_id
        if ref_id in users_data:
            users_data[ref_id]['referrals'] += 1
            users_data[ref_id]['referrals_today'] = users_data[ref_id].get('referrals_today', 0) + 1
            users_data[ref_id]['balance'] += 20

            try:
                bot.send_message(
                    ref_id,
                    f"<b>🎉 У тебе новий реферал: {message.from_user.first_name} (@{message.from_user.username})</b>\n💰 +20 PulseCoins!"
                )
            except:
                pass

    users_data[user_id]['last_active'] = int(time.time())
    save_data()

    # 🔒 Перевірка номера телефону
    if not users_data[user_id].get('phone_number'):
        request_contact_btn = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        contact_button = telebot.types.KeyboardButton("📲 Поділитися номером", request_contact=True)
        request_contact_btn.add(contact_button)
        bot.send_message(message.chat.id,
            "📲 <b>Будь ласка, поділися своїм номером телефону, щоб продовжити.</b>\nЦе потрібно для захисту від спаму.",
            reply_markup=request_contact_btn)
        return

    # ✅ Якщо номер вже збережений — продовжуємо
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard)
    bot.send_message(message.chat.id, "<b>🔗 Наші канали для підписки:</b>", reply_markup=get_channels_buttons())



def get_channels_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    for ch in sponsor_channels:
        markup.add(telebot.types.InlineKeyboardButton(text=ch, url=f"https://t.me/{ch.strip('@')}"))
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

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    contact = message.contact

    if contact.user_id != user_id:
        bot.send_message(message.chat.id, "⚠️ Надішли саме свій номер.")
        return

    phone = contact.phone_number

    # ✅ Перевірка номера має бути тут, всередині функції
    if not re.match(r'^\+?\d{1,4}\d{6,14}$', phone):
        bot.send_message(message.chat.id, "❌ Невірний формат номера телефону.")
        return

    users_data[user_id]['phone_number'] = phone if phone.startswith("+") else f"+{phone}"
    save_data()

    bot.send_message(message.chat.id, "✅ Номер прийнято! Тепер ти можеш користуватися ботом.", reply_markup=main_keyboard)
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard)
    bot.send_message(message.chat.id, "<b>🔗 Наші канали для підписки:</b>", reply_markup=get_channels_buttons())


@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def callback_check_subs(call):
    user_id = call.from_user.id
    if check_subscriptions(user_id):
        bot.answer_callback_query(call.id, "✅ Всі канали підписані!")
    else:
        bot.answer_callback_query(call.id, "❌ Ти не підписаний на всі канали.")
        bot.send_message(user_id, "<b>⚠️ Ти не підписаний на всі спонсорські канали. Підпишись, щоб отримувати бонуси.</b>")


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
        bot.send_message(message.chat.id, f"<b>🎉 Плюс удачі {bonus} фартів! 🎉</b>", reply_markup=main_keyboard)
        bot.send_message(message.chat.id,
            f"<b>🔮 Пульс удачі б’ється рівно 👊</b>"
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

@bot.message_handler(func=lambda m: m.text == '📊 Мій профіль')
def my_profile(message):
    user_id = message.from_user.id
    data = users_data.get(user_id)
    if data:
        users_data[user_id]['last_active'] = int(time.time())
        save_data()
        bot.send_message(message.chat.id,
            f"<b>📊 Твій профіль:</b>\n"
            f"🪙 PulseCoins: {data['balance']}\n"
            f"📆 Стрік: {data['streak']} дні(в)\n"
            f"👥 Запрошено друзів: {data['referrals']}\n"
            f"🎟 Квитків на розіграш: {data['tickets']}",
            reply_markup=main_keyboard)
    else:
        bot.send_message(message.chat.id, "<b>❗️ Профіль ще порожній. Натисни /start</b>", reply_markup=main_keyboard)

@bot.message_handler(func=lambda m: m.text == '🏆 Розіграші')
def lottery(message):
    user_id = message.from_user.id
    if not check_subscriptions(user_id):
        bot.send_message(message.chat.id, "<b>⚠️ Спершу підпишись на всі наші спонсорські канали!</b>", reply_markup=main_keyboard)
        return

    tickets = users_data.get(user_id, {}).get('tickets', 0)
    info = (
    "<b>🏆 Jackpot Pulse — Розіграші</b>\n"
    "🎁 Приз: 500 грн - (5 переможців по 100 грн)\n"
    "📆 Щонеділі о 19:00\n"
    "🔸 Як взяти участь:\n"
    "• 1000 PulseCoins\n"
    "• або 25 друзів\n"
    "• або <b>15 квитків</b> 🎟\n"
    f"🎟 У тебе: {tickets} квитків\n"
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

    user['lottery_participation'] = True
    save_data()
    bot.answer_callback_query(call.id, "✅ Ти успішно приєднався до розіграшу!")

    try:
        user_info = bot.get_chat(user_id)
        uname = f"@{user_info.username}" if user_info.username else user_info.first_name
        bot.send_message(ADMIN_ID, f"🎟 Новий учасник розіграшу: <b>{uname}</b>, через {method}")
    except:
        pass


# Команда для запуску розіграшу вручну
@bot.message_handler(commands=['run_lottery'])
def run_lottery(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")

    # Фільтруємо користувачів, які беруть участь в розіграші
    participants = [user_id for user_id, data in users_data.items() if data['lottery_participation']]
    
    if not participants:
        return bot.reply_to(message, "❌ Немає учасників для розіграшу!")

    # Вибір переможців (наприклад, 5 переможців)
    winners = random.sample(participants, min(5, len(participants)))
    
    # Збираємо інформацію про переможців
    winners_info = []
    for winner in winners:
        try:
            user_info = bot.get_chat(winner)
            uname = f"@{user_info.username}" if user_info.username else user_info.first_name
            winners_info.append(f"{uname} (ID: {winner})")
            bot.send_message(winner, f"🎉 Ти виграв розіграш! Вітаємо! 🎉")
        except Exception as e:
            print(f"Не вдалося надіслати повідомлення переможцю {winner}: {e}")

    # Повідомлення адміністратору з усією інформацією про переможців
    winners_text = "\n".join(winners_info)
    bot.send_message(ADMIN_ID, f"✅ Розіграш завершено! Ось переможці:\n\n{winners_text}")
    
    # Оповіщення про завершення розіграшу
    bot.reply_to(message, f"✅ Розіграш завершено! Переможці вибрані. Ось список переможців:\n\n{winners_text}")

@bot.message_handler(func=lambda m: m.text == '👯 Запросити друга')
def invite_friend(message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/JackpotPulse_bot?start={user_id}"
    bot.send_message(message.chat.id,
        f"<b>👯 Запроси друзів!</b>\n\n"
        f"🔗 Твоє посилання: {ref_link}\n"
        f"✅ За кожного — +20 PulseCoins\n🎯 Активність 3 дні — ще +10",
        reply_markup=main_keyboard)


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
    markup.add(telebot.types.InlineKeyboardButton(text="✅ Перевірити підписку", callback_data="check_subs"))
    bot.send_message(message.chat.id, text, reply_markup=markup)


def update_daily_top5():
    global daily_top5
    sorted_users = sorted(users_data.items(), key=lambda x: x[1].get('referrals_today', 0), reverse=True)
    daily_top5 = sorted_users[:5]

# Функція для виведення Топ-5
@bot.message_handler(func=lambda m: m.text == '⭐️ Топ 5 гравців')
def show_top_5(message):
    # Оновлюємо Топ-5
    update_daily_top5()

    # Формуємо текст для виведення
    text = "<b>🔥 Щоденний Топ 5 рефералів:</b>\n\n"
    for i, (uid, data) in enumerate(daily_top5, start=1):
        try:
            user_info = bot.get_chat(uid)
            uname = f"@{user_info.username}" if user_info.username else user_info.first_name
        except:
            uname = str(uid)
        # Використовуємо referrals_today для кожного користувача
        text += f"{i}. {uname} — <b>{data.get('referrals_today', 0)}</b> рефералів\n"

    # Відправляємо повідомлення з Топ-5
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard)


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


# Додаємо готові промокоди
ready_promos = {
    't6cz-xuk8-nhao-ejs6': {'value': 25, 'activations': 30},
    'qpwr-ckpw-iqnk-eo47': {'value': 20, 'activations': 30},
    'q3pf-xgb6-9owd-6vjt': {'value': 15, 'activations': 30},
    'nnf1-56z3-urzx-ocq3': {'value': 20, 'activations': 30},
    '1gpw-gvvh-n8ty-g4ds': {'value': 20, 'activations': 30},
    'cxae-68zk-3cs0-lyte': {'value': 15, 'activations': 30},
    '62j1-6zsh-j5i6-s8k7': {'value': 15, 'activations': 30},
    '74c2-eu9v-in1u-rtgh': {'value': 30, 'activations': 30},
    '8ttb-r3km-m0ol-lk7k': {'value': 25, 'activations': 30},
    'dygo-l42j-d6bj-5b38': {'value': 20, 'activations': 30},
    '9gt8-2zvl-tx3v-dsei': {'value': 25, 'activations': 30},
    'bipg-jvs8-n4qj-ppkk': {'value': 20, 'activations': 30},
    'ig2j-inlo-qbzw-o78i': {'value': 25, 'activations': 30},
    'spbx-ldu7-x9om-wfmb': {'value': 25, 'activations': 30},
    '4ocs-s1ig-164x-qyvk': {'value': 25, 'activations': 30},
    'mvod-y9tk-s2xf-uul9': {'value': 15, 'activations': 30},
    'bgcj-5duz-1iev-eqdh': {'value': 15, 'activations': 30},
    '0fiz-wki6-txmt-oppv': {'value': 15, 'activations': 30},
    'y9wg-xsr7-hhmz-i0bd': {'value': 30, 'activations': 30},
    '3hu6-s0de-8ona-xq81': {'value': 30, 'activations': 30},
    'fchg-t8a5-bqno-lksz': {'value': 20, 'activations': 30},
    'ox35-9qtm-c4qq-vkv5': {'value': 20, 'activations': 30},
    '1the-1rf8-aawk-6n4y': {'value': 20, 'activations': 30},
    'xqd7-clb4-9n49-zbyn': {'value': 30, 'activations': 30},
    '0mlm-tnix-wsqa-s10y': {'value': 15, 'activations': 30},
    'nl84-0s7e-c0ad-smuj': {'value': 15, 'activations': 30},
    'c4b8-sk3y-giw1-t6bq': {'value': 25, 'activations': 30},
    'tmym-xrl3-ztdh-kps4': {'value': 15, 'activations': 30},
    'suxe-i3cz-an5l-tbyo': {'value': 30, 'activations': 30},
    'tgt3-znkg-9mnr-ht08': {'value': 15, 'activations': 30},
    '7usj-k7zt-f4un-9ghp': {'value': 25, 'activations': 30},
    'y1qd-lua7-hkqt-ql11': {'value': 30, 'activations': 30},
    'cmd7-k6cw-7a1y-o0dm': {'value': 15, 'activations': 30},
    '3ipx-yrmk-wkd3-fvyk': {'value': 30, 'activations': 30},
    'z174-k22u-soyy-cwyv': {'value': 30, 'activations': 30},
    'isus-lx3b-vzv3-efib': {'value': 20, 'activations': 30},
    '3dkf-edm2-iyiq-1vxw': {'value': 20, 'activations': 30},
    's9g1-63ly-7oen-ftio': {'value': 25, 'activations': 30},
    'y52l-cwkz-1j64-rt47': {'value': 30, 'activations': 30},
    '93kl-2kvd-w6y5-bqmr': {'value': 30, 'activations': 30},
    '3syo-akh4-kq0m-egoc': {'value': 25, 'activations': 30},
    'r9qc-af7d-85cg-w397': {'value': 15, 'activations': 30},
    'q6fz-g4af-ywd5-jvnk': {'value': 25, 'activations': 30},
    'zz8h-7bmx-ke5y-a7k9': {'value': 15, 'activations': 30},
    'zeca-579k-l1b9-xotr': {'value': 20, 'activations': 30},
    'ejtu-ezos-i4sh-87fr': {'value': 25, 'activations': 30},
    'nt65-mglo-85gl-s72x': {'value': 30, 'activations': 30},
    'yii9-i4ck-bc4x-l5l8': {'value': 20, 'activations': 30},
    'f07a-4jvz-cmcb-yql9': {'value': 25, 'activations': 30},
    '2jw1-jv1n-a4bo-qey5': {'value': 25, 'activations': 30},
    'jifb-9rii-u5uz-9vly': {'value': 25, 'activations': 30},
    'c7jg-50wo-xrtu-3ca2': {'value': 20, 'activations': 30},
    'w6x4-5fz7-ktrt-xcd5': {'value': 15, 'activations': 30},
    '8l5a-2cxv-6388-l558': {'value': 30, 'activations': 30},
    'istt-hpw7-ycir-ccl1': {'value': 30, 'activations': 30},
    'jmln-yb5s-iv5f-d4w8': {'value': 15, 'activations': 30},
    '8kvm-fmxe-dzny-7odw': {'value': 20, 'activations': 30},
    'teuc-9hbs-m1gl-xm7w': {'value': 25, 'activations': 30},
    'h4mu-oxv1-cz2h-xssl': {'value': 25, 'activations': 30},
    'qj97-bu0x-coel-byq8': {'value': 20, 'activations': 30},
    'pijd-j2vy-chbw-as0i': {'value': 25, 'activations': 30},
    'tid5-eii7-25iy-ez7e': {'value': 25, 'activations': 30}
}

# Запис у файл промокодів, якщо ще не існує
if not os.path.exists(PROMO_FILE):
    with open(PROMO_FILE, "w") as f:
        json.dump(ready_promos, f, indent=4)

@bot.message_handler(func=lambda m: m.text == '💼 Баланс / Промокод')
def balance_or_promo(message):
    user_id = message.from_user.id
    if user_id not in users_data:
        return

    if not check_subscriptions(user_id):
        bot.send_message(user_id, "<b>⚠️ Спершу підпишись на всі наші спонсорські канали!</b>", reply_markup=main_keyboard)
        return

    data = users_data[user_id]
    pulse_token = data.get('pulse_token', 0)
    missing = 500 - pulse_token

    text = (
        f"<b>💼 Твій баланс:</b>\n"
        f"🪙 PulseCoins: {data['balance']}\n"
        f"🧧 PulseToken (промокоди): {pulse_token}\n\n"
        f"💸 Для виводу потрібно мінімум 500 PulseToken"
    )

    if pulse_token < 500:
        text += f"\n❗️ Залишилось ще {missing} PulseToken до виводу"

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("💸 Вивести 500 PulseToken", callback_data="withdraw_request"))
    markup.add(telebot.types.InlineKeyboardButton("🎟 Активувати промокод", callback_data="activate_promo"))

    bot.send_message(user_id, text, reply_markup=markup)

def can_user_withdraw(user_id):
    user = users_data.get(user_id, {})
    pulse_token = user.get('pulse_token', 0)
    referrals = user.get('referrals', 0)
    tasks_done = user.get('tasks_done_count', 0)
    streak = user.get('streak', 0)

    if pulse_token < 500:
        return False, "❌ Недостатньо PulseToken для виводу. Потрібно мінімум 500."

    if referrals < 20:
        return False, f"👥 Потрібно щонайменше 20 друзів для виводу. У тебе зараз: {referrals}"

    if tasks_done < 5:
        return False, f"📝 Потрібно виконати мінімум 5 завдань. У тебе зараз: {tasks_done}"

    if streak < 7:
        return False, f"🔥 Потрібно мати стрік щонайменше 7 днів. У тебе зараз: {streak}"

    return True, ""


@bot.callback_query_handler(func=lambda call: call.data == "withdraw_request")
def withdraw_request(call):
    user_id = call.from_user.id
    now = int(time.time())
    user = users_data.get(user_id, {})
    last_withdraw = user.get('last_withdraw_request', 0)

    # 🔍 Перевірка вимог
    allowed, reason = can_user_withdraw(user_id)
    if not allowed:
        bot.send_message(user_id, reason)
        return

    # ⏳ Один вивід на 7 днів
    if now - last_withdraw < 7 * 86400:
        days_left = int((7 * 86400 - (now - last_withdraw)) / 86400)
        bot.send_message(user_id, f"⏳ Ти вже подавав заявку. Зачекай ще {days_left} дн.")
        return

    bot.send_message(user_id, "💳 Введи реквізити для виводу:")
    bot.register_next_step_handler(call.message, process_withdraw_details)


def process_withdraw_details(message):
    user_id = message.from_user.id
    details = message.text.strip()
    now = int(time.time())

    user = users_data.get(user_id, {})
    pulse_token = user.get('pulse_token', 0)

    if pulse_token < 500:
        bot.send_message(user_id, "❌ У тебе недостатньо PulseToken.")
        return

    users_data[user_id]['pulse_token'] -= 500
    users_data[user_id]['last_withdraw_request'] = now
    save_data()

    try:
        user_info = bot.get_chat(user_id)
        uname = f"@{user_info.username}" if user_info.username else user_info.first_name
    except:
        uname = str(user_id)

    bot.send_message(ADMIN_ID, f"🔔 <b>Нова заявка на вивід:</b>\n\n"
                               f"👤 {uname}\n"
                               f"ID: <code>{user_id}</code>\n"
                               f"📤 500 PulseToken\n"
                               f"📇 Реквізити: <code>{details}</code>")
    bot.send_message(user_id, "✅ Заявку на вивід прийнято. Очікуй підтвердження від адміністратора.")



@bot.callback_query_handler(func=lambda call: call.data == "activate_promo")
def ask_promo_code(call):
    bot.send_message(call.message.chat.id, "🔐 Введи свій промокод у відповідь на це повідомлення:")
    bot.register_next_step_handler(call.message, process_promo_code)


def process_promo_code(message):
    user_id = message.from_user.id

    if not check_subscriptions(user_id):
        bot.send_message(user_id, "⚠️ Промокоди активуються тільки після підписки на всі канали!")
        return

    promo_input = message.text.strip().lower()
    promo_data = load_promos()
    matched_key = next((k for k in promo_data if k.lower() == promo_input), None)

    if not matched_key:
        bot.send_message(user_id, "❌ Недійсний промокод.")
        return

    promo = promo_data[matched_key]

    if 'used_by' not in promo:
        promo['used_by'] = []

    if user_id in promo['used_by']:
        bot.send_message(user_id, "⛔️ Ти вже використав цей промокод.")
        return

    if len(promo['used_by']) >= promo.get('activations', 1):
        bot.send_message(user_id, "🚫 Ліміт активацій цього промокоду вичерпано.")
        return

    value = promo['value']
    users_data[user_id]['pulse_token'] = users_data[user_id].get('pulse_token', 0) + value
    promo['used_by'].append(user_id)

    save_data()
    promo_data[matched_key] = promo
    save_promos(promo_data)

    bot.send_message(user_id, f"🎉 Промокод активовано! +{value} PulseToken")

    try:
        user_info = bot.get_chat(user_id)
        uname = f"@{user_info.username}" if user_info.username else user_info.first_name
        bot.send_message(ADMIN_ID, f"🔔 {uname} активував промокод {matched_key} (+{value} PulseToken)")
    except:
        pass

@bot.message_handler(func=lambda m: m.text == '📝 Завдання')
def task(message):
    user_id = message.from_user.id

    if user_id not in users_data:
        bot.send_message(message.chat.id, "<b>Спочатку натисни /start</b>")
        return

    if not check_subscriptions(user_id):
        bot.send_message(message.chat.id, "<b>Спершу підпишись на всі наші спонсорські канали!</b>", reply_markup=get_channels_buttons())
        return

    if current_task.strip() == "❗️Завдання ще не встановлено.":
        bot.send_message(message.chat.id, "<b>❗️На зараз немає активного завдання.</b>")
        return

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ Завдання виконано", callback_data=f"task_done_{user_id}"))

    bot.send_message(message.chat.id, f"<b>{current_task}</b>", reply_markup=markup)


# Команда для перевірки виконаних завдань вручну
@bot.message_handler(commands=['check_task'])
def check_task(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")

    parts = message.text.strip().split()
    if len(parts) != 2:
        return bot.reply_to(message, "❌ Формат: /check_task user_id")

    user_id = int(parts[1])

    if user_id not in users_data:
        return bot.reply_to(message, "❌ Користувач не знайдений.")

    last_task_done = users_data[user_id].get("last_task_done", 0)
    if last_task_done > 0:
        bot.reply_to(message, f"Завдання для користувача {user_id} виконано! Час виконання: {last_task_done}")
    else:
        bot.reply_to(message, f"Завдання для користувача {user_id} ще не виконано.")
# ⬇️ Користувач натискає "Завдання виконано" — запит надсилається адміну


# ✅ Адмін схвалює виконання
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_task_"))
def approve_task(call):
    user_id = int(call.data.split("_")[2])
    now = int(time.time())

    if now - users_data[user_id].get("last_task_done", 0) < 10800:  # 3 години
        bot.answer_callback_query(call.id, "⏳ Користувач вже виконував завдання останні 3 години.")
        return

    users_data[user_id]['pulse_token'] += current_task_reward
    users_data[user_id]['last_task_done'] = now

    # 🔢 Рахуємо кількість виконаних завдань
    users_data[user_id]['tasks_done_count'] = users_data[user_id].get('tasks_done_count', 0) + 1

    save_data()

    bot.send_message(user_id, f"✅ Твоє завдання схвалено! Ти отримав +{current_task_reward} PulseToken.")
    bot.answer_callback_query(call.id, "🎉 Нагороду нараховано!")


@bot.callback_query_handler(func=lambda call: call.data.startswith("task_done_"))
def task_done_request(call):
    user_id = call.from_user.id

    if not check_subscriptions(user_id):
        bot.answer_callback_query(call.id, "❌ Спочатку підпишись на канали.")
        return

    now = int(time.time())
    last_request = users_data[user_id].get("last_task_request", 0)

    # ❗️ Обмеження: раз на 3 години надсилати запит
    if now - last_request < 10800:
        bot.answer_callback_query(call.id, "⏳ Ти вже надсилав запит. Зачекай трохи.")
        return

    users_data[user_id]['last_task_request'] = now
    save_data()

    bot.answer_callback_query(call.id, "📨 Запит на перевірку надіслано адміну.")

    try:
        user_info = bot.get_chat(user_id)
        uname = f"@{user_info.username}" if user_info.username else user_info.first_name
    except:
        uname = str(user_id)

    # Надсилаємо адміну
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Схвалити", callback_data=f"approve_task_{user_id}"),
        telebot.types.InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_task_{user_id}")
    )

    bot.send_message(
        ADMIN_GROUP_ID,
        f"📩 <b>Новий запит на завдання</b>\n"
        f"👤 {uname}\n🆔 ID: <code>{user_id}</code>",
        reply_markup=markup
    )

# ❌ Адмін відхиляє
@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_task_"))
def reject_task(call):
    user_id = int(call.data.split("_")[2])
    bot.send_message(user_id, "❌ На жаль, твоє завдання не схвалено адміністратором.")
    bot.answer_callback_query(call.id, "⛔️ Завдання відхилено.")

@bot.message_handler(commands=['set_task'])
def set_task(message):
    if not is_admin(message):
        bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")
        return

    content = message.text[9:].strip()
    if not content:
        bot.reply_to(message, "❌ Формат: /set_task Текст завдання || кількість токенів\nНаприклад:\n/set_task Підпишись на канал @test || 40")
        return

    if '||' in content:
        parts = content.split('||')
        task_text = parts[0].strip()
        try:
            task_reward = int(parts[1].strip())
        except:
            bot.reply_to(message, "❌ Після '||' вкажи кількість токенів (число).")
            return
    else:
        task_text = content
        task_reward = 50  # за замовчуванням

    global current_task, current_task_reward
    current_task = task_text
    current_task_reward = task_reward

    with open(TASK_FILE, 'w', encoding='utf-8') as f:
        json.dump({"text": current_task, "reward": current_task_reward}, f, indent=4, ensure_ascii=False)

    bot.reply_to(message, f"✅ Завдання оновлено:\n<b>{current_task}</b>\n💰 Нагорода: {current_task_reward} PulseToken")


@bot.message_handler(commands=['send_promo'])
def ask_promo_text(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")

    chat_id = message.chat.id
    bot.send_message(chat_id, "✉️ Введи текст промо-повідомлення, яке хочеш надіслати всім:")
    bot.register_next_step_handler(message, lambda msg: send_promo_to_all(msg, chat_id))

def send_promo_to_all(message, reply_chat_id):
    if not is_admin(message):
        return

    promo_text = message.text.strip()
    count = 0

    for user_id in users_data.keys():
        try:
            bot.send_message(user_id, promo_text)
            count += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"Помилка надсилання {user_id}: {e}")

    bot.send_message(reply_chat_id, f"✅ Повідомлення надіслано {count} користувачам.")

@bot.message_handler(commands=['notify_restart'])
def notify_restart(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")
    
    # Повідомлення для всіх користувачів
    notification_text = "🚨 Бот оновлено! Для відновлення роботи натисніть /start, щоб знову активувати бота!"
    
    for user_id in users_data.keys():
        try:
            bot.send_message(user_id, notification_text)
            time.sleep(0.1)  # Для запобігання перевантаження сервера
        except Exception as e:
            print(f"Не вдалося надіслати повідомлення {user_id}: {e}")
    
    bot.reply_to(message, "✅ Повідомлення надіслано всім користувачам.")

@bot.message_handler(commands=['додати_промо'])
def add_new_promo(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")

    parts = message.text.strip().split()
    if len(parts) != 4:
        return bot.reply_to(message, "❌ Формат: /додати_промо КОД СУМА АКТИВАЦІЙ\n\nПриклад:\n/додати_промо summer-2025 50 100")

    _, code, value, limit = parts
    code = code.lower()

    try:
        value = int(value)
        limit = int(limit)
    except:
        return bot.reply_to(message, "❌ Сума і ліміт мають бути числами.")

    promos = load_promos()
    if code in promos:
        return bot.reply_to(message, "⚠️ Такий промокод вже існує.")

    promos[code] = {
        'value': value,
        'activations': limit,
        'used_by': []
    }

    save_promos(promos)
    bot.reply_to(message, f"✅ Новий промокод <code>{code}</code> додано!\n🎁 +{value} PulseToken\n🔢 Ліміт: {limit} активацій")

    count = 0
    for user_id in users_data.keys():
        try:
            bot.send_message(user_id, promo_text)
            count += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"Помилка надсилання {user_id}: {e}")

# Функція для автоматичної перевірки підписок (можна викликати раз на годину/день)

def reset_user(user_id):
    if user_id in users_data:
        users_data[user_id]['balance'] = 0
        users_data[user_id]['pulse_token'] = 0
        users_data[user_id]['referrals'] = 0
        users_data[user_id]['tickets'] = 0
        users_data[user_id]['lottery_participation'] = False
        users_data[user_id]['last_bonus'] = 0
        users_data[user_id]['last_card'] = 0
        users_data[user_id]['streak'] = 0
        save_data()

def auto_check_subscriptions():
    while True:
        print("⏱ Автоперевірка підписок...")
        now = int(time.time())

        for user_id in list(users_data.keys()):
            try:
                unsubscribed_channels = []

                for channel in sponsor_channels:
                    try:
                        chat = bot.get_chat(channel)
                        member = bot.get_chat_member(chat.id, user_id)
                        if member.status in ['left', 'kicked']:
                            unsubscribed_channels.append(channel)
                    except:
                        unsubscribed_channels.append(channel)

                if unsubscribed_channels:
                    if users_data[user_id].get('last_unsubscribed_time', 0) == 0:
                        users_data[user_id]['last_unsubscribed_time'] = now
                        print(f"[❗️] {user_id} не підписаний. Таймер пішов.")
                        try:
                            bot.send_message(user_id, "<b>⚠️ Ти не підписаний на обов’язкові канали. Якщо протягом 24 годин не підпишешся — бонуси буде скинуто.</b>")
                        except:
                            pass
                    elif now - users_data[user_id]['last_unsubscribed_time'] >= 172800:  # 48 годин
                        users_data[user_id]['last_unsubscribed_time'] = 0
                        print(f"[⚠️] {user_id} досі не підписаний після 48 годин. Без дій.")
                        try:
                            bot.send_message(user_id, "<b>⚠️ Минуло 48 годин, а ти досі не підписаний. Без підписки ти не можеш отримувати нові бонуси.</b>")
                        except:
                            pass
                else:
                    if users_data[user_id].get('last_unsubscribed_time', 0) != 0:
                        users_data[user_id]['last_unsubscribed_time'] = 0
                        print(f"[✅] {user_id} знову підписаний. Таймер обнулено.")

            except Exception as e:
                print(f"Помилка перевірки {user_id}: {e}")

        save_data()
        time.sleep(3600)  # перевірка щогодини


@bot.message_handler(commands=['перевірити_вивід'])
def check_withdraw_permission(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")

    parts = message.text.strip().split()
    if len(parts) != 2:
        return bot.reply_to(message, "❌ Формат: /перевірити_вивід user_id")

    try:
        user_id = int(parts[1])
    except:
        return bot.reply_to(message, "❌ Невірний формат user_id")

    if user_id not in users_data:
        return bot.reply_to(message, "❌ Користувач не знайдений у базі.")

    allowed, reason = can_user_withdraw(user_id)

    if allowed:
        bot.reply_to(message, f"✅ Користувач {user_id} МОЖЕ виводити.")
    else:
        bot.reply_to(message, f"❌ НЕ може виводити:\n{reason}")


@bot.message_handler(commands=['підтвердити_вивід'])
def confirm_withdrawal(message):
    if not is_admin(message):
        return

    parts = message.text.strip().split()
    if len(parts) != 2:
        bot.reply_to(message, "❌ Формат: /підтвердити_вивід user_id")
        return

    try:
        target_id = int(parts[1])
        bot.send_message(target_id, "✅ Твою заявку на вивід опрацьовано. Очікуй виплату найближчим часом!")
        bot.reply_to(message, "✅ Повідомлення відправлено користувачу.")
    except:
        bot.reply_to(message, "❌ Помилка. Можливо, неправильний ID.")


@bot.message_handler(commands=['виплачено'])
def payout_done(message):
    if not is_admin(message):
        return

    parts = message.text.strip().split()
    if len(parts) != 2:
        bot.reply_to(message, "❌ Формат: /виплачено user_id")
        return

    try:
        target_id = int(parts[1])
        bot.send_message(target_id, "💵 <b>Кошти надіслано!</b>\nДякуємо за користування Jackpot Pulse! 🎰")
        bot.reply_to(message, "✅ Користувач повідомлений про виплату.")
    except:
        bot.reply_to(message, "❌ Помилка. Можливо, неправильний ID.")

@bot.message_handler(commands=['оновити_рефералів_сьогодні'])
def ensure_referrals_today(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")

    updated = 0
    for user_id, data in users_data.items():
        if 'referrals_today' not in data:
            users_data[user_id]['referrals_today'] = 0
            updated += 1

    save_data()
    bot.reply_to(message, f"✅ Поле 'referrals_today' додано {updated} користувачам.")

@bot.message_handler(commands=['оновити_дані'])
def update_user_fields(message):
    if message.from_user.id != ADMIN_ID:
        return

    count = 0
    for user_id, data in users_data.items():
        if 'tasks_done_count' not in data:
            data['tasks_done_count'] = 0
        if 'last_withdraw_request' not in data:
            data['last_withdraw_request'] = 0
        if 'streak' not in data:
            data['streak'] = 0
        if 'lottery_participation' not in data:
            data['lottery_participation'] = False
        count += 1

    save_data()
    bot.send_message(ADMIN_ID, f"✅ Оновлено {count} користувачів.")

@bot.message_handler(commands=['оновити_топ'])
def update_top_command(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")

    update_daily_top5()
    bot.reply_to(message, "✅ Топ-5 оновлено вручну.")

@bot.message_handler(commands=['додати_канал'])
def add_channel(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")
    
    parts = message.text.strip().split()
    if len(parts) != 2:
        return bot.reply_to(message, "❌ Формат: /додати_канал @channel_username")
    
    channel = parts[1]
    if not channel.startswith('@'):
        return bot.reply_to(message, "❌ Канал має починатися з @")
    
    if channel in sponsor_channels:
        return bot.reply_to(message, "⚠️ Цей канал уже є в списку.")
    
    sponsor_channels.append(channel)
    bot.reply_to(message, f"✅ Канал {channel} додано до списку обов'язкових.")

@bot.message_handler(commands=['видалити_канал'])
def remove_channel(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")
    
    parts = message.text.strip().split()
    if len(parts) != 2:
        return bot.reply_to(message, "❌ Формат: /видалити_канал @channel_username")
    
    channel = parts[1]
    if channel not in sponsor_channels:
        return bot.reply_to(message, "❌ Цього каналу немає в списку.")
    
    sponsor_channels.remove(channel)
    bot.reply_to(message, f"🗑 Канал {channel} видалено зі списку.")

@bot.message_handler(commands=['список_каналів'])
def list_channels(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")

    if not sponsor_channels:
        return bot.reply_to(message, "❗️ Список каналів порожній.")

    text = "<b>📋 Обов'язкові канали:</b>\n" + "\n".join(sponsor_channels)
    bot.reply_to(message, text)

@bot.message_handler(commands=['скинути_рефералів'])
def reset_referrals_today(message):
    if not is_admin(message):
        return bot.reply_to(message, "⛔️ У тебе немає прав для цієї команди.")

    # Додаємо рефералів за сьогодні до загальної кількості рефералів
    for user_id in users_data:
        # Додаємо кількість рефералів за день до загальної кількості рефералів
        users_data[user_id]['referrals'] += users_data[user_id].get('referrals_today', 0)
        
        # Потім скидаємо лічильник рефералів за день
        users_data[user_id]['referrals_today'] = 0

    # Оновлення Топ-5 після скидання
    update_daily_top5()

    save_data()  # Зберігаємо зміни
    bot.reply_to(message, "✅ Реферали за день додано до загальної кількості. Топ-5 оновлено.")



# Запускаємо фоновий потік перевірки підписок
threading.Thread(target=auto_check_subscriptions, daemon=True).start()

@bot.message_handler(func=lambda message: True)
def debug_chat_id(message):
    print(f"Chat ID: {message.chat.id}")

# 🟢 Бот готовий до запуску
print("Бот запущено...")
bot.infinity_polling()









