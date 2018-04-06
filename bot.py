from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

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

reply_markup1 = ReplyKeyboardMarkup([['Пропустить']])
reply_markup2 = ReplyKeyboardMarkup(
    [
        ['Показать на карте'],
        ['Последние новости'],
        ['Вернуться назад']
    ])

inline_markup1 = InlineKeyboardMarkup(
    [[InlineKeyboardButton('Следующая новость', callback_data=1)], [InlineKeyboardButton('Назад', callback_data=3)]])

inline_markup2 = InlineKeyboardMarkup([[InlineKeyboardButton('Следующая новость', callback_data=1)],
                                       [InlineKeyboardButton('Предыдущая новость', callback_data=2)],
                                       [InlineKeyboardButton('Назад', callback_data=3)]])

inline_markup3 = InlineKeyboardMarkup(
    [[InlineKeyboardButton('Предыдущая новость', callback_data=2)], [InlineKeyboardButton('Назад', callback_data=3)]
     ])


def start(bot, update):
    update.message.reply_text(
        'Введите свое имя', reply_markup=reply_markup1, one_time_keyboard=False)

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
            reply_markup=reply_markup2
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
            reply_markup=reply_markup2
        )
        update.message.reply_text('Выберите одну из возможных функций для данного местоположения:',
                                  reply_markup=reply_markup2)

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
            user_data['news'] = news
            user_data['index'] = 0
            user_data['length'] = len(news)
            update.message.reply_text('Найдено новостей для данного местоположения: {}'.format(len(news)),
                                      reply_markup=ReplyKeyboardRemove())
            update.message.reply_text('*{0}*\n{1}\n[Подробнее:]({2})'.format(*news[0]), parse_mode='markdown',
                                      reply_markup=inline_markup1)
            sleep(1)
        else:
            update.message.reply_text('Новостей для этой местности не найдено')

    elif text == 'Вернуться назад':
        update.message.reply_text('Введите какое-либо местоположение', reply_markup=ReplyKeyboardRemove())
        return IDLE

    return LOCATION_HANDLER


def scrolling_news(bot, update, user_data):
    query = update.callback_query
    d = {0: inline_markup1, user_data['length'] - 1: inline_markup3}
    if query.data == '1':
        user_data['index'] = min(user_data['length'], user_data['index'] + 1)
    elif query.data == '2':
        user_data['index'] = max(0, user_data['index'] - 1)
    else:
        bot.deleteMessage(chat_id=query.message.chat_id,
                          message_id=query.message.message_id)
        bot.send_message(query.message.chat_id, 'Выберите одну из возможных функций для данного местоположения:',
                         reply_markup=reply_markup2)

        return LOCATION_HANDLER
    try:
        bot.edit_message_text(text='*{0}*\n{1}\n[Подробнее:]({2})'.format(*user_data['news'][user_data['index']]),
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id, parse_mode='markdown',
                              reply_markup=d[user_data['index']] if user_data['index'] in d else inline_markup2)
    except IndexError:
        if user_data['index'] < 0:
            user_data['index'] = 0
        else:
            user_data['index'] = user_data['length'] - 1


def stop(bot, update):
    update.message.reply_text('Бля конец')
    return ConversationHandler.END


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

        LOCATION_HANDLER: [MessageHandler(Filters.text, location_handler, pass_user_data=True),
                           CallbackQueryHandler(scrolling_news, pass_user_data=True)]
    },

    fallbacks=[CommandHandler('stop', stop)]
)

if __name__ == '__main__':
    main()
