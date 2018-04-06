from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, DispatcherHandlerStop
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

from time import sleep

from maps_api.request import geocoder_request, map_request
from maps_api.geocoder import get_pos, get_bbox

from news_parser.parser import parse_news

from speech_analyze import speech_analyze
from xml_parser import speech_parser
from convert import convert

from config import TELEGRAM_TOKEN, SPEECH_TOKEN, CONVERT_TOKEN

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def start(bot, update):
    update.message.reply_text(
        'Введите свое имя', reply_markup=ReplyKeyboardMarkup([['Пропустить']], one_time_keyboard=False)
    )
    return ENTER_NAME


def enter_name(bot, update, user_data):
    name = update.message.text
    if name != 'Пропустить':
        user_data['username'] = name
    else:
        user_data['username'] = None

    update.message.reply_text('Введите свое местоположение')
    return ENTER_LOCATION


def enter_location(bot, update, user_data):
    location = update.message.text
    if location != 'Пропустить':
        user_data['location'] = location
    else:
        user_data['location'] = None

    update.message.reply_text('Введите какое-либо местоположение', reply_markup=ReplyKeyboardRemove())

    return IDLE


def idle(bot, update, user_data):
    response = geocoder_request(geocode=update.message.text, format='json')
    if response:
        update.message.reply_text(
            'Найдено местоположение',
            reply_markup=ReplyKeyboardMarkup(
                [
                    ['Показать на карте'],
                    ['Последние новости'],
                    ['Вернуться назад']
                ]
            )
        )

        user_data['current_response'] = response
        return LOCATION_HANDLER
    update.message.reply_text('По данному адресу ничего не найдено.')

    return IDLE


def voice_to_text(bot, update, user_data):
    voice = update.message.voice.get_file()
    response = speech_analyze(SPEECH_TOKEN, convert(CONVERT_TOKEN, voice.file_path))

    text = speech_parser(response)
    data = geocoder_request(geocode=text, format='json')
    if data:
        update.message.reply_text(
            'Найдено местоположение',
            reply_markup=ReplyKeyboardMarkup(
                [
                    ['Показать на карте'],
                    ['Последние новости'],
                    ['Вернуться назад']
                ]
            )
        )

        user_data['current_response'] = data
        return LOCATION_HANDLER
    update.message.reply_text('По данному адресу ничего не найдено.')

    return IDLE


def location_handler(bot, update, user_data):
    text = update.message.text
    if text == 'Показать на карте':
        pos = get_pos(user_data['current_response'])
        bbox = get_bbox(user_data['current_response'])
        url = map_request(
            ll='{},{}'.format(*pos),
            bbox='{},{}~{},{}'.format(*bbox),
            pt='{},{},pm2rdm'.format(*pos),
            l='map'
        )
        update.message.reply_photo(photo=url)

    elif text == 'Последние новости':
        news = parse_news(user_data['current_response'])
        if news is not None:
            for story in news:
                update.message.reply_text('*{0}*\n{1}\n[Подробнее:]({2})'.format(*story), parse_mode='markdown')
                sleep(1)
        else:
            update.message.reply_text('Новостей для этой местности не найдено')

    elif text == 'Вернуться назад':
        update.message.reply_text('Введите какое-либо местоположение', reply_markup=ReplyKeyboardRemove())
        return IDLE

    return LOCATION_HANDLER


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_error_handler(error)
    dp.add_handler(conversation_handler)

    updater.start_polling()
    updater.idle()


ENTER_NAME, ENTER_LOCATION, IDLE, LOCATION_HANDLER = range(4)


conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],

    states={
        ENTER_NAME: [MessageHandler(Filters.text, enter_name, pass_user_data=True)],
        ENTER_LOCATION: [MessageHandler(Filters.text, enter_location, pass_user_data=True)],

        IDLE: [
            MessageHandler(Filters.text, idle, pass_user_data=True),
            MessageHandler(Filters.voice, voice_to_text, pass_user_data=True)
        ],

        LOCATION_HANDLER: [MessageHandler(Filters.text, location_handler, pass_user_data=True)]
    },

    fallbacks=[CommandHandler('stop', lambda bot, update: update.message.reply_text('Леня лох'))]
)

if __name__ == '__main__':
    main()
