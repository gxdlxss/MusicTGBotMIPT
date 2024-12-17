import asyncio
import logging
import random
import re

import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

API_TOKEN = '7875835052:AAH6POunq-p1JmMRgveyN7ht5Jbm6X0Mu94'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

buttons = [
    [KeyboardButton(text="🎧 For Work"), KeyboardButton(text="📚 For Study"), KeyboardButton(text="🏋️‍♂️ For Sports")],
    [KeyboardButton(text="🚗 For Driving"), KeyboardButton(text="🎄 For New Year"), KeyboardButton(text="🎉 For Parties")],
]
keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_more_tracks_inline():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Show more tracks", callback_data="more_tracks")]
    ])

def clean_text(text):
    return re.sub(r'^[^\w\s]+', '', text).strip()

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("Hi! Choose the type of music to get your personalized playlist:", reply_markup=keyboard)

@dp.message(lambda message: message.text in [
    "🎧 For Work", "📚 For Study", "🏋️‍♂️ For Sports", "🚗 For Driving", "🎄 For New Year", "🎉 For Parties"
])
async def playlist_handler(message: types.Message):
    music_type = clean_text(message.text)
    await send_random_tracks(message, music_type)

async def send_random_tracks(message, music_type, callback_query=None):
    try:
        async with aiosqlite.connect("music.db") as db:
            cursor = await db.execute("SELECT Name, Link FROM music WHERE Type = ?", (music_type,))
            tracks = await cursor.fetchall()
            await cursor.close()

            if tracks:
                random.shuffle(tracks)
                selected_tracks = tracks[:random.randint(2, 4)]
                response = f"Playlist for {music_type}:\n\n"
                for track in selected_tracks:
                    title, author = track[0].rsplit(' - ', 1)
                    response += f"**{author}** - {title} [link]({track[1]})\n"
                await message.answer(response, parse_mode="Markdown", reply_markup=get_more_tracks_inline())
            else:
                await message.answer(f"Sorry, no tracks available for {music_type}.")
    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer("An error occurred while retrieving the playlist. Please try again later.")

@dp.callback_query(lambda c: c.data == "more_tracks")
async def more_tracks_handler(callback_query: types.CallbackQuery):
    await callback_query.answer()
    user_choice = callback_query.message.text.split("\n")[0].replace("Playlist for ", "").strip()
    await send_random_tracks(callback_query.message, user_choice, callback_query)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())