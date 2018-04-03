from config import TELEGRAM_TOKEN, SPEECH_TOKEN, CONVERT_TOKEN
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, DispatcherHandlerStop
from speech_analyze import speech_analyze
from xml_parser import parser
from convert import convert
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def voice_to_text(bot, update):
    voice = update.message.voice.get_file()
    response = speech_analyze(SPEECH_TOKEN, convert(CONVERT_TOKEN, voice.file_path))
    update.message.reply_text(parser(response))


def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_error_handler(error)
    dp.add_handler(MessageHandler(Filters.voice, voice_to_text))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
    # 'https://api.telegram.org/file/bot544264100:AAEi5G9JrJz6SwTmnwlavORdXl9dizy8x1A/voice/file_2.oga'}
