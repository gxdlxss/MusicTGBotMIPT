import logging
import random
import asyncio
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aiosqlite

API_TOKEN = '7875835052:AAH6POunq-p1JmMRgveyN7ht5Jbm6X0Mu94'

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Config:
    BUTTONS = [
        [KeyboardButton(text="🎧 For Work"), KeyboardButton(text="📚 For Study"), KeyboardButton(text="🏋️‍♂️ For Sports")],
        [KeyboardButton(text="🚗 For Driving"), KeyboardButton(text="🎄 For New Year"), KeyboardButton(text="🎉 For Parties")],
        [KeyboardButton(text="📩 Contact Support")],
    ]
    START_MESSAGE = "Hi! Choose the type of music to get your personalized playlist:"
    NO_TRACKS_MESSAGE = "Sorry, no tracks available for {music_type}."
    ERROR_MESSAGE = "An error occurred while retrieving the playlist. Please try again later."
    SUPPORT_IDS = [123456789, 987654321]


class SupportStates(StatesGroup):
    waiting_for_message = State()


class MusicDatabase:
    def __init__(self, db_path):
        self.db_path = db_path

    async def get_tracks_by_type(self, music_type):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT Name, Link FROM music WHERE Type = ?", (music_type,))
            tracks = await cursor.fetchall()
            await cursor.close()
        return tracks


class MusicBot:
    def __init__(self, api_token, db_path):
        self.bot = Bot(token=api_token)
        self.dp = Dispatcher()
        self.config = Config()
        self.db = MusicDatabase(db_path)
        self.keyboard = self.create_keyboard()
        self.register_handlers()

    def create_keyboard(self):
        return ReplyKeyboardMarkup(keyboard=self.config.BUTTONS, resize_keyboard=True)

    def create_inline_keyboard(self, music_type):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Show more tracks", callback_data=f"more_tracks:{music_type}")]
        ])

    @staticmethod
    def clean_text(text):
        return re.sub(r'^[^\w\s]+', '', text).strip()

    @staticmethod
    def escape_markdown(text):
        escape_chars = r"_*[]()~`>#+-=|{}.!\\"
        return re.sub(f"[{re.escape(escape_chars)}]", r"\\\g<0>", text)

    async def log_user_info(self, user: types.User, action: str):
        logging.info(f"User {user.id} ({user.username or 'No username'}) performed action: {action}")

    async def start_handler(self, message: types.Message):
        await self.log_user_info(message.from_user, "started the bot")
        await message.answer(self.config.START_MESSAGE, reply_markup=self.keyboard)

    async def playlist_handler(self, message: types.Message):
        music_type = self.clean_text(message.text)
        await self.log_user_info(message.from_user, f"selected playlist type: {music_type}")
        await self.send_random_tracks(message, music_type)

    async def send_random_tracks(self, message, music_type):
        try:
            tracks = await self.db.get_tracks_by_type(music_type)
            if tracks:
                random.shuffle(tracks)
                selected_tracks = tracks[:random.randint(2, 4)]
                response = f"Playlist for {music_type}:\n\n"
                for track in selected_tracks:
                    if " – " in track[0]:
                        title, author = track[0].rsplit(" – ", 1)
                        response += f"**{self.escape_markdown(author.strip())}** - {self.escape_markdown(title.strip())} [link]({track[1]})\n"
                    else:
                        response += f"**Unknown Author** - {self.escape_markdown(track[0])} [link]({track[1]})\n"
                await message.answer(response, parse_mode="Markdown", reply_markup=self.create_inline_keyboard(music_type))
            else:
                await message.answer(self.config.NO_TRACKS_MESSAGE.format(music_type=music_type))
        except Exception as e:
            logging.error(f"Error for user {message.from_user.id} while retrieving tracks for {music_type}: {e}")
            await message.answer(self.config.ERROR_MESSAGE)

    async def more_tracks_handler(self, callback_query: types.CallbackQuery):
        await self.log_user_info(callback_query.from_user, "requested more tracks")
        music_type = callback_query.data.split(":", 1)[1]
        await callback_query.answer()
        await self.send_random_tracks(callback_query.message, music_type)

    async def contact_support_handler(self, message: types.Message, state: FSMContext):
        await self.log_user_info(message.from_user, "requested contact support")
        await message.answer("Please enter your message for support:")
        await state.set_state(SupportStates.waiting_for_message)

    async def handle_support_message(self, message: types.Message, state: FSMContext):
        user_message = message.text
        user = message.from_user
        await self.log_user_info(user, f"sent a support message: {user_message}")

        for support_id in self.config.SUPPORT_IDS:
            try:
                await self.bot.send_message(
                    support_id,
                    f"Support request from {user.username or 'No username'} (ID: {user.id}):\n\n{user_message}"
                )
            except Exception as e:
                logging.error(f"Failed to send message to support ID {support_id}: {e}")

        await message.answer("Your message has been sent to our support team. They will contact you soon.")
        await state.clear()

    def register_handlers(self):
        self.dp.message(CommandStart())(self.start_handler)
        self.dp.message(lambda message: message.text in [
            "🎧 For Work", "📚 For Study", "🏋️‍♂️ For Sports", "🚗 For Driving", "🎄 For New Year", "🎉 For Parties"
        ])(self.playlist_handler)
        self.dp.message(lambda message: message.text == "📩 Contact Support")(self.contact_support_handler)
        self.dp.message(StateFilter(SupportStates.waiting_for_message))(self.handle_support_message)
        self.dp.callback_query(lambda c: c.data.startswith("more_tracks:"))(self.more_tracks_handler)

    async def run(self):
        logging.info("Bot is starting...")
        await self.dp.start_polling(self.bot)


if __name__ == "__main__":
    music_bot = MusicBot(API_TOKEN, "music.db")
    asyncio.run(music_bot.run())