import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
import aiosqlite
import asyncio

# Specify your bot token
API_TOKEN = '7875835052:AAH6POunq-p1JmMRgveyN7ht5Jbm6X0Mu94'

# Logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()  # Dispatcher is created separately from the bot

# Keyboard buttons with emojis
buttons = [
    [
        KeyboardButton(text="🎧 For Work"),
        KeyboardButton(text="📚 For Study"),
        KeyboardButton(text="🏋️‍♂️ For Sports"),
    ],
    [
        KeyboardButton(text="🚗 For Driving"),
        KeyboardButton(text="🎄 For New Year"),
        KeyboardButton(text="🎉 For Parties"),
    ],
]
keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Handler for the /start command
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("Hi! Choose the type of music to get your personalized playlist:", reply_markup=keyboard)

# Handler for selecting the type of music
@dp.message(lambda message: message.text in [
    "🎧 For Work",
    "📚 For Study",
    "🏋️‍♂️ For Sports",
    "🚗 For Driving",
    "🎄 For New Year",
    "🎉 For Parties"
])
async def playlist_handler(message: types.Message):
    music_type = message.text
    try:
        # Connecting to the database
        async with aiosqlite.connect("music.db") as db:
            # Querying the database
            cursor = await db.execute("SELECT Название, Ссылка FROM музыка WHERE тип = ?", (music_type,))
            tracks = await cursor.fetchall()
            await cursor.close()

            # If the playlist is found
            if tracks:
                response = f"Playlist for {music_type}:\n\n"
                for track in tracks:
                    response += f"{track[0]}: {track[1]}\n"
                await message.answer(response)
            else:
                await message.answer(f"Sorry, we currently don't have a playlist for {music_type}.")
    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer("An error occurred while retrieving the playlist. Please try again later.")

# Bot startup
async def main():
    await dp.start_polling(bot)  # Start dispatcher with the bot

if __name__ == "__main__":
    asyncio.run(main())