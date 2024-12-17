import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
import aiosqlite
import asyncio
import re

API_TOKEN = '7875835052:AAH6POunq-p1JmMRgveyN7ht5Jbm6X0Mu94'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

buttons = [
    [KeyboardButton(text="🎧 For Work"), KeyboardButton(text="📚 For Study"), KeyboardButton(text="🏋️‍♂️ For Sports")],
    [KeyboardButton(text="🚗 For Driving"), KeyboardButton(text="🎄 For New Year"), KeyboardButton(text="🎉 For Parties")],
]
keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_more_tracks_inline(music_type):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Show more tracks", callback_data=f"more_tracks:{music_type}")]
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

async def send_random_tracks(message, music_type):
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
                    if " – " in track[0]:
                        title, author = track[0].rsplit(" – ", 1)
                        response += f"**{author.strip()}** - {title.strip()} [link]({track[1]})\n"
                    else:
                        response += f"**Unknown Author** - {track[0]} [link]({track[1]})\n"
                await message.answer(response, parse_mode="Markdown", reply_markup=get_more_tracks_inline(music_type))
            else:
                await message.answer(f"Sorry, no tracks available for {music_type}.")
    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer("An error occurred while retrieving the playlist. Please try again later.")

@dp.callback_query(lambda c: c.data.startswith("more_tracks:"))
async def more_tracks_handler(callback_query: types.CallbackQuery):
    await callback_query.answer()
    music_type = callback_query.data.split(":", 1)[1]
    await send_random_tracks(callback_query.message, music_type)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())