import logging
import random
import asyncio
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
import aiosqlite

API_TOKEN = '7875835052:AAH6POunq-p1JmMRgveyN7ht5Jbm6X0Mu94'

logging.basicConfig(level=logging.INFO)


class MusicBot:
    def __init__(self, api_token):
        self.bot = Bot(token=api_token)
        self.dp = Dispatcher()
        self.keyboard = self.create_keyboard()
        self.register_handlers()

    def create_keyboard(self):
        buttons = [
            [KeyboardButton(text="🎧 For Work"), KeyboardButton(text="📚 For Study"), KeyboardButton(text="🏋️‍♂️ For Sports")],
            [KeyboardButton(text="🚗 For Driving"), KeyboardButton(text="🎄 For New Year"), KeyboardButton(text="🎉 For Parties")],
        ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    def create_inline_keyboard(self, music_type):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Show more tracks", callback_data=f"more_tracks:{music_type}")]
        ])

    @staticmethod
    def clean_text(text):
        return re.sub(r'^[^\w\s]+', '', text).strip()

    async def start_handler(self, message: types.Message):
        await message.answer("Hi! Choose the type of music to get your personalized playlist:", reply_markup=self.keyboard)

    async def playlist_handler(self, message: types.Message):
        music_type = self.clean_text(message.text)
        await self.send_random_tracks(message, music_type)

    async def send_random_tracks(self, message, music_type):
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
                    await message.answer(response, parse_mode="Markdown", reply_markup=self.create_inline_keyboard(music_type))
                else:
                    await message.answer(f"Sorry, no tracks available for {music_type}.")
        except Exception as e:
            logging.error(f"Error: {e}")
            await message.answer("An error occurred while retrieving the playlist. Please try again later.")

    async def more_tracks_handler(self, callback_query: types.CallbackQuery):
        await callback_query.answer()
        music_type = callback_query.data.split(":", 1)[1]
        await self.send_random_tracks(callback_query.message, music_type)

    def register_handlers(self):
        self.dp.message(CommandStart())(self.start_handler)
        self.dp.message(lambda message: message.text in [
            "🎧 For Work", "📚 For Study", "🏋️‍♂️ For Sports", "🚗 For Driving", "🎄 For New Year", "🎉 For Parties"
        ])(self.playlist_handler)
        self.dp.callback_query(lambda c: c.data.startswith("more_tracks:"))(self.more_tracks_handler)

    async def run(self):
        await self.dp.start_polling(self.bot)


if __name__ == "__main__":
    music_bot = MusicBot(API_TOKEN)
    asyncio.run(music_bot.run())