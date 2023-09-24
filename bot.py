import os
import tempfile

import openai
from pydub import AudioSegment
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)


# Replace 'YOUR_BOT_TOKEN' with your actual bot token
TOKEN = os.getenv("BOT_API_TOKEN")


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

            audio_file = open(output_file, "rb")
            transcript = openai.Audio.transcribe("whisper-1", audio_file)

            await update.message.reply_text(transcript["text"])
    else:
        await update.message.reply_text(
            "Send me or forward me a voice message and I will transcribe it for you 💬"
        )


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

    # Add a /start command handler
    application.add_handler(
        MessageHandler(filters.COMMAND & filters.Regex(r"/start"), start)
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
