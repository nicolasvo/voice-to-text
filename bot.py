import os
import tempfile

from groq import Groq
from pydub import AudioSegment
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

import translators as ts


TOKEN = os.getenv("BOT_API_TOKEN")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I convert speech to text. Send me or forward me a voice message and I will transcribe it for you 💬"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Check if the message is a voice message
    if update.message.voice or update.message.video_note or update.message.video:
        # Get the voice message file ID
        if update.message.voice:
            message_type = "voice"
            file_id = update.message.voice.file_id
        elif update.message.video_note:
            message_type = "video"
            file_id = update.message.video_note.file_id
        else:
            message_type = "video"
            file_id = update.message.video.file_id

        # Get the voice message file
        media_message = await context.bot.get_file(file_id)

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate a unique filename
            input_file = os.path.join(
                temp_dir,
                f"{message_type}_message_{update.message.message_id}.ogg"
                if message_type == "voice"
                else f"{message_type}_message_{update.message.message_id}.mp4",
            )

            # Download the voice message to the temporary file
            await media_message.download_to_drive(input_file)

            if message_type == "voice":
                audio = AudioSegment.from_ogg(input_file)
            else:
                video = AudioSegment.from_file(input_file, format="mp4")
                audio = video.set_channels(1)  # Convert to mono audio (optional)

            output_file = os.path.join(
                temp_dir, f"{message_type}_message_{update.message.message_id}.mp3"
            )
            audio.export(output_file, format="mp3")
            print(
                f"Conversion complete. {input_file} has been converted to {output_file}."
            )

            try:
                with open(output_file, "rb") as audio_file:
                    transcript = groq_client.audio.transcriptions.create(
                        file=(os.path.basename(output_file), audio_file.read()),
                        model="whisper-large-v3-turbo",
                    )
                message = transcript.text
                # keyboard = [
                #     [
                #         InlineKeyboardButton("Translate to 🇬🇧", callback_data="en"),
                #     ]
                # ]
                # reply_markup = InlineKeyboardMarkup(keyboard)
                reply_markup = None
            except Exception as e:
                message = str(e)
                reply_markup = None

            await update.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            "Send me or forward me a voice message and I will transcribe it for you 💬"
        )


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.edit_message_reply_markup(reply_markup=None)
    await query.answer()
    try:
        message = ts.translate_text(query.message.text)
    except Exception as e:
        message = f"Sorry, an error occurred when translating 🥲\n{e}"
    await query.message.reply_text(message)


def main():
    application = Application.builder().token(TOKEN).build()

    # Add command handler
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Add voice message handler
    application.add_handler(
        MessageHandler(
            filters.VOICE | filters.VIDEO_NOTE | filters.VIDEO, handle_message
        )
    )

    application.add_handler(CallbackQueryHandler(translate))

    # Add a /start command handler
    application.add_handler(
        MessageHandler(filters.COMMAND & filters.Regex(r"/start"), start)
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
