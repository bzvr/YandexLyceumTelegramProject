from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

import requests

from maps_api.request import geocoder_request, map_request
from maps_api.geocoder import get_pos, get_bbox, get_country_code, get_city, check_response
from maps_api.static import get_static_map

from news_parser.parser import parse_news

from weather.weather import get_current_weather, get_forecast_weather

from schedule_api.airports import airs
from schedule_api.schedule import get_flights

from speech_api.speech_analyze import speech_analyze
from speech_api.xml_parser import speech_parser

from headhunter_api.suggestions import specialization_suggest, keywords_suggest, region_suggest
from headhunter_api import vacancies_request, full_vacancy_request

from config import TELEGRAM_TOKEN, SPEECH_TOKEN, WEATHER_TOKEN

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


back_markup = ReplyKeyboardMarkup([['Вернуться назад']])
reply_markup1 = ReplyKeyboardMarkup([['Пропустить']])
reply_markup2 = ReplyKeyboardMarkup(
    [
        ['Показать на карте'],
        ['Последние новости'],
        ['Погода'],
        ['Вакансии'],
        ['Вернуться назад']
    ]
)
reply_markup3 = ReplyKeyboardMarkup([
    ['Поиск на карте'],
    ['Показать текущий профиль вакансий'],
    ['Настройки профиля вакансий']
])
reply_markup4 = ReplyKeyboardMarkup([
    ['Настройка специализации'],
    ['Настройка ключевых слов'],
    ['Настройка региона'],
    ['Вернуться назад']
])
keyboard1 = [['Пропустить']]
keyboard2 = [['Показать на карте'], ['Последние новости'], ['Погода'], ['Расписания'], ['Вернуться назад']]
keyboard3 = [['Вернуться назад']]
keyboard4 = [['Текущая погода'], ['Прогноз на 6 дней'], ['Вернуться назад']]
keyboard5 = [['Найти авиарейс'], ['Вернуться назад']]

inline_markup1 = InlineKeyboardMarkup(
    [[InlineKeyboardButton('Следующая новость', callback_data=1)], [InlineKeyboardButton('Назад', callback_data=3)]])

inline_markup2 = InlineKeyboardMarkup([
    [InlineKeyboardButton('Предыдущая новость', callback_data=2),
     InlineKeyboardButton('Следующая новость', callback_data=1)],
    [InlineKeyboardButton('Назад', callback_data=3)]
])

inline_markup3 = InlineKeyboardMarkup([
    [InlineKeyboardButton('Предыдущая новость', callback_data=2)],
    [InlineKeyboardButton('Назад', callback_data=3)]
])

inline_markup4 = InlineKeyboardMarkup([
    [InlineKeyboardButton('Карта', callback_data='map')],
    [InlineKeyboardButton('Спутник', callback_data='sat')],
    [InlineKeyboardButton('Гибрид', callback_data='sat,skl')],
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

    user_data['vacancy'] = {
        'region_name': None,
        'region_id': None,
        'specialization_name': None,
        'specialization_id': None,
        'keywords': None
    }

    update.message.reply_text('Введите свое местоположение')
    return ENTER_LOCATION


def enter_location(bot, update, user_data):
    location = update.message.text

    if location != 'Пропустить':
        user_data['location'] = location

        suggests = region_suggest(location)
        user_data['region_suggests'] = suggests

        if len(suggests) != 0:
            location_keyboard = [['Пропустить']]
            for suggestion in suggests:
                location_keyboard.append([suggestion])

            update.message.reply_text(
                'Найдено несколько регионов, соответствующих введенному.\n'
                'Выберите один из них.',
                reply_markup=ReplyKeyboardMarkup(location_keyboard)
            )

            return LOCATION_APPLY

        update.message.reply_text(
            'Данная местнось не найдена в базе регионов.'
        )

    else:
        user_data['location'] = None

    name = ', {}'.format(user_data['username']) if user_data['username'] is not None else ''
    update.message.reply_text('Добро пожаловать{}!'.format(name), reply_markup=reply_markup3)

    return MAIN_MENU


def location_apply(bot, update, user_data):
    text = update.message.text

    if text in user_data['region_suggests']:
        user_data['location'] = text
        user_data['vacancy']['region_name'] = text
        user_data['vacancy']['region_id'] = user_data['region_suggests'][text]
        update.message.reply_text(
            'Регион успешно установлен!'
        )

    elif text != 'Пропустить':
        update.message.reply_text(
            'Введенный текст не является ни одним из перечисленных регионов.\n'
            'Попробуйте ввести название региона ещё раз.'
        )
        return LOCATION_APPLY

    name = ', {}'.format(user_data['username']) if user_data['username'] is not None else ''
    update.message.reply_text('Добро пожаловать{}!'.format(name), reply_markup=reply_markup3)
    return MAIN_MENU


def main_menu(bot, update, user_data):
    text = update.message.text

    if text == 'Поиск на карте':
        update.message.reply_text(
            'Введите местность, информацию о которой Вы хотите узнать',
            reply_markup=back_markup
        )
        return SEARCH_HANDLER

    elif text == 'Показать текущий профиль вакансий':
        region = user_data['vacancy']['region_name']
        if region is None:
            if user_data['location'] is None:
                region = 'Не указано'
            else:
                region = 'Указанный регион не найден в базе данных HeadHunter'

        spec = user_data['vacancy']['specialization_name']
        if spec is None: spec = 'Не указано'

        keywords = user_data['vacancy']['keywords']
        if keywords is None: keywords = 'Не указано'

        update.message.reply_text(
            'Регион: {}\n'
            'Специализация: {}\n'
            'Ключевые слова: {}\n'.format(
                region, spec, keywords
            )
        )

    elif text == 'Настройки профиля вакансий':
        update.message.reply_text(
            'Выберите параметры, которые Вы хотите настроить',
            reply_markup=reply_markup4
        )
        return PROFILE_CONFIG

    return MAIN_MENU


def profile_config(bot, update, user_data):
    text = update.message.text

    if text == 'Настройка специализации':
        update.message.reply_text(
            'Введите название специализации.\n'
            'Бот попробует найти схожие специализации в базе данных HeadHunter.',
            reply_markup=back_markup
        )
        return SPECIALIZATION_CONFIG

    elif text == 'Настройка ключевых слов':
        update.message.reply_text(
            'Введите ключевые слова, которые будут использоваться при поиске вакансий',
            reply_markup=back_markup
        )
        return KEYWORDS_CONFIG

    elif text == 'Настройка региона':
        update.message.reply_text('Введите свое местоположение', reply_markup=reply_markup1)
        return ENTER_LOCATION

    elif text == 'Вернуться назад':
        update.message.reply_text('Что Вы хотите сделать?', reply_markup=reply_markup3)
        return MAIN_MENU

    return PROFILE_CONFIG


def specialization_config(bot, update, user_data):
    text = update.message.text
    suggests = specialization_suggest(text)

    if text == 'Вернуться назад':
        update.message.reply_text(
            'Возвращаемся в меню настроек',
            reply_markup=reply_markup4
        )
        return PROFILE_CONFIG

    if len(suggests) != 0:
        user_data['spec_suggests'] = suggests

        spec_keyboard = [['Вернуться назад']]
        for suggestion in suggests:
            spec_keyboard.append([suggestion])

        update.message.reply_text(
            'Бот нашел несколько схожих специализаций. Выберите одну из них',
            reply_markup=ReplyKeyboardMarkup(spec_keyboard)
        )

        return SPECIALIZATION_APPLY

    else:
        update.message.reply_text(
            'Не нашлось специализаций, схожих с введенной.\n'
            'Попробуйте ввести специализацию еще раз.'
        )
        return SPECIALIZATION_CONFIG


def specialization_apply(bot, update, user_data):
    text = update.message.text

    if text in user_data['spec_suggests']:
        user_data['vacancy']['specialization_name'] = text
        user_data['vacancy']['specialization_id'] = user_data['spec_suggests'][text]
        update.message.reply_text(
            'Специализация успешно установлена! Возвращаемся в меню настроек',
            reply_markup=reply_markup4
        )
        return PROFILE_CONFIG

    elif text == 'Вернуться назад':
        update.message.reply_text(
            'Возвращаемся в меню настроек',
            reply_markup=reply_markup4
        )
        return PROFILE_CONFIG

    else:
        update.message.reply_text(
            'Введенный текст не является ни одной из перечисленных специализаций.\n'
            'Попробуйте ввести название специализации ещё раз.'
        )

    return SPECIALIZATION_APPLY


def keywords_config(bot, update, user_data):
    text = update.message.text
    suggests = keywords_suggest(text)

    if text == 'Вернуться назад':
        update.message.reply_text(
            'Возвращаемся в меню настроек',
            reply_markup=reply_markup4
        )
        return PROFILE_CONFIG

    if len(suggests) != 0:
        user_data['keywords_suggests'] = suggests

        keywords_keyboard = [['Вернуться назад']]
        for suggestion in suggests:
            keywords_keyboard.append([suggestion])

        update.message.reply_text(
            'Бот нашел несколько схожих ключевых слов. Выберите одно из них',
            reply_markup=ReplyKeyboardMarkup(keywords_keyboard)
        )

        return KEYWORDS_APPLY

    else:
        user_data['vacancy']['keywords'] = text
        update.message.reply_text(
            'Ключевые слова успешно установлены! Возвращаемся в меню настроек',
            reply_markup=reply_markup4
        )

    return PROFILE_CONFIG


def keywords_apply(bot, update, user_data):
    text = update.message.text

    if text in user_data['keywords_suggests']:
        user_data['vacancy']['keywords'] = text
        update.message.reply_text(
            'Ключевые слова успешно установлены! Возвращаемся в меню настроек',
            reply_markup=reply_markup4
        )
        return PROFILE_CONFIG

    elif text == 'Вернуться назад':
        update.message.reply_text(
            'Возвращаемся в меню настроек',
            reply_markup=reply_markup4
        )
        return PROFILE_CONFIG

    else:
        update.message.reply_text(
            'Введенный текст не является ни одним из перечисленных ключевых слов.\n'
            'Попробуйте ввести ключевые слова ещё раз.'
        )

    return KEYWORDS_APPLY


def search_handler(bot, update, user_data):
    text = update.message.text

    if text == 'Вернуться назад':
        update.message.reply_text(
            'Возвражаемся в главное меню',
            reply_markup=reply_markup3
        )
        return MAIN_MENU

    response = geocoder_request(geocode=text, format='json')

    if check_response(response):
        update.message.reply_text(
            'Найдено местоположение',
            reply_markup=reply_markup2
        )

        user_data['current_response'] = response
        return LOCATION_HANDLER
    update.message.reply_text('По данному адресу ничего не найдено.')

    return SEARCH_HANDLER


def voice_to_text(bot, update, user_data):
    voice = update.message.voice.get_file()
    file = requests.get(voice.file_path).content
    response = speech_analyze(SPEECH_TOKEN, file)

    text = speech_parser(response)
    data = geocoder_request(geocode=text, format='json')

    if check_response(data):
        update.message.reply_text(
            'Найдено местоположение',
            reply_markup=reply_markup2
        )
        update.message.reply_text('Выберите одну из возможных функций для данного местоположения:',
                                  reply_markup=reply_markup2)

        user_data['current_response'] = data
        return LOCATION_HANDLER

    update.message.reply_text('По данному адресу ничего не найдено.')

    return SEARCH_HANDLER


def location_handler(bot, update, user_data):
    text = update.message.text

    if text == 'Показать на карте':
        res = "[​​​​​​​​​​​]({}){}".format(get_static_map(user_data),
                                           'Карта для города ' + get_city(user_data['current_response'], 'ru-RU'))
        update.message.reply_text(res, parse_mode='markdown', reply_markup=inline_markup4)

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
            return NEWS_HANDLER

        else:
            update.message.reply_text('Новостей для этой местности не найдено')

    elif text == 'Погода':
        update.message.reply_text(
            'Что вы хотите узнать о погоде в городе {}?'.format(get_city(user_data['current_response'], 'ru-RU')),
            reply_markup=ReplyKeyboardMarkup(keyboard4))
        return WEATHER_HANDLER

    elif text == 'Расписания':
        update.message.reply_text(
            'Выберите один из вариантов поиска:',
            reply_markup=ReplyKeyboardMarkup(keyboard5))
        return RASP_HANDLER

        city, code = get_city(user_data['current_response'], 'ru-RU'), get_country_code(user_data['current_response'])
        update.message.reply_text(get_current_weather(city, code, WEATHER_TOKEN))

    elif text == 'Вакансии':
        try:
            data = geocoder_request(geocode=get_city(user_data['current_response']), format='json')
            city = get_city(data, 'ru_RU')
            region = list(region_suggest(city).items())[0][1]

            user_data['vacancies_response'] = vacancies_request(area=region)['items']
            user_data['vacancies_index'] = 0
            user_data['vacancies_image'] = 'location'

            update.message.reply_text('Найдено несколько вакансий', reply_markup=ReplyKeyboardRemove())
            update.message.reply_text(
                form_vacancy_reply(user_data),
                parse_mode='markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('Следующая вакансия', callback_data=1)],
                    [InlineKeyboardButton('Местоположение', callback_data=4)],
                    [InlineKeyboardButton('Назад', callback_data=3)]
                ])
            )

            return VACANCIES_HANDLER

        except Exception as e:
            print(e)

    elif text == 'Вернуться назад':
        update.message.reply_text('Введите какое-либо местоположение', reply_markup=ReplyKeyboardRemove())
        return SEARCH_HANDLER

    return LOCATION_HANDLER


def scrolling_vacancy(bot, update, user_data):
    query = update.callback_query
    try:
        if query.data == '1':
            if user_data['vacancies_index'] != len(user_data['vacancies_response']) - 1:
                user_data['vacancies_index'] += 1

        elif query.data == '2':
            if user_data['vacancies_index'] != 0:
                user_data['vacancies_index'] -= 1

        elif query.data == '3':
            bot.deleteMessage(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id
            )

            bot.send_message(
                query.message.chat_id,
                'Выберите одну из возможных функций для данного местоположения:',
                reply_markup=reply_markup2
            )

            return LOCATION_HANDLER

        elif query.data == '4':
            user_data['vacancies_image'] = 'location'

        elif query.data == '5':
            user_data['vacancies_image'] = 'logo'

        keyboard = [
            [],
            [],
            [InlineKeyboardButton('Назад', callback_data=3)]
        ]

        if user_data['vacancies_index'] != 0:
            keyboard[0].append(InlineKeyboardButton(
                'Предыдущая вакансия', callback_data=2
            ))

        if user_data['vacancies_index'] != len(user_data['vacancies_response']) - 1:
            keyboard[0].append(InlineKeyboardButton(
                'Следующая вакансия', callback_data=1
            ))

        if user_data['vacancies_image'] == 'location':
            keyboard[1].append(InlineKeyboardButton('Логотип', callback_data=5))
        else:
            keyboard[1].append(InlineKeyboardButton('Местоположение', callback_data=4))

        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=form_vacancy_reply(user_data, user_data['vacancies_image'] == 'location'),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='markdown'
        )

        return VACANCIES_HANDLER
    except Exception as e:
        print(e)
        raise


def form_vacancy_reply(user_data, add_location_image=False):
    vacancy_id = user_data['vacancies_response'][user_data['vacancies_index']]['id']
    vacancy = full_vacancy_request(vacancy_id)

    title = vacancy['name']
    experience = vacancy['experience']['name']
    address = vacancy['address']
    if address is not None:
        address = address['city'] + ', ' + address['street'] + ' ' + address['building']
    else:
        address = 'Адрес не указан'

    vacancy_url = vacancy['alternate_url']

    if add_location_image:
        if vacancy['address'] is not None:
            pos = vacancy['address']['lng'], vacancy['address']['lat']
            image_url = map_request(
                ll='{},{}'.format(*pos),
                pt='{},{},pm2rdm'.format(*pos),
                l='map'
            )
        else:
            if vacancy['employer']['logo_urls'] is not None:
                image_url = vacancy['employer']['logo_urls']['original']
            else:
                image_url = ''
    else:
        if vacancy['employer']['logo_urls'] is not None:
            image_url = vacancy['employer']['logo_urls']['original']
        else:
            image_url = ''

    return (
        '*{title}*\n'
        '{experience}\n'
        '{address}\n'
        '[​​​​​​​​​​​]({image_url})'  # EMPTY STRING IN BRACKETS
        '[Подробнее:]({url})\n'
    ).format(
        title=title, experience=experience,
        address=address, url=vacancy_url,
        image_url=image_url
    )


def scrolling_news(bot, update, user_data):
    query = update.callback_query
    d = {0: inline_markup1, user_data['length'] - 1: inline_markup3}
    if query.data == '1':
        user_data['index'] = min(user_data['length'], user_data['index'] + 1)

    elif query.data == '2':
        user_data['index'] = max(0, user_data['index'] - 1)

    elif query.data == '3':
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


def choosing_map_type(bot, update, user_data):
    query = update.callback_query
    bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id,
                          text="[​​​​​​​​​​​]({}){}".format(get_static_map(user_data, query.data),
                                                            'Карта для города ' + get_city(
                                                                user_data['current_response'], 'ru-RU')),
                          parse_mode='markdown', reply_markup=inline_markup4)


def enter_the_map(bot, update):
    text = update.message.text
    if text == 'Вернуться назад':
        return LOCATION_HANDLER


def weather(bot, update, user_data):
    text = update.message.text

    if text == 'Текущая погода':
        city, code = get_city(user_data['current_response']), get_country_code(user_data['current_response'])
        update.message.reply_text(
            get_current_weather(city, code, WEATHER_TOKEN, get_city(user_data['current_response'], 'ru-RU')))

    elif text == 'Прогноз на 6 дней':
        city, code = get_city(user_data['current_response']), get_country_code(user_data['current_response'])
        update.message.reply_text(
            get_forecast_weather(city, code, WEATHER_TOKEN, get_city(user_data['current_response'], 'ru-RU')))

    elif text == 'Вернуться назад':
        update.message.reply_text('Выберите одну из возможных функций для данного местоположения:',
                                  reply_markup=ReplyKeyboardMarkup(keyboard2))

        return LOCATION_HANDLER


def schedule(bot, update, user_data):
    text = update.message.text

    if text == 'Найти авиарейс':
        city = get_city(user_data['current_response'], 'ru_RU')
        airports = airs.get(city, 0)
        if airports:
            airport_question(update, city)
            return SET_SECOND_CITY_HANDLER
        else:
            update.message.reply_text(
                'В заданном городе аэропорта не найдено')

    elif text == 'Вернуться назад':
        update.message.reply_text('Выберите одну из возможных функций для данного местоположения:',
                                  reply_markup=ReplyKeyboardMarkup(keyboard2))

        return LOCATION_HANDLER


def set_second_city(bot, update, user_data):
    text = update.message.text
    if text == 'Вернуться назад':
        update.message.reply_text(
            'Выберите один из вариантов поиска:',
            reply_markup=ReplyKeyboardMarkup(keyboard5))
        return RASP_HANDLER
    else:
        user_data['airport1'] = text.split(', ')[-1]
        update.message.reply_text('Введите город пункта назначения:', reply_markup=ReplyKeyboardMarkup(keyboard3))
        return SET_SECOND_AIRPORT_HANDLER


def set_second_airport(bot, update, user_data):
    text = update.message.text
    if text == 'Вернуться назад':
        city = get_city(user_data['current_response'], 'ru_RU')
        airport_question(update, city)
        return SET_SECOND_CITY_HANDLER
    else:
        response = geocoder_request(geocode=text, format='json')
        if check_response(response):
            user_data['city2'] = get_city(response, 'ru_RU')
            airports = airs.get(user_data['city2'], 0)
            update.message.reply_text('Выберите аэропорт прибытия:',
                                      reply_markup=ReplyKeyboardMarkup(
                                          [[elem[1] + ', ' + elem[0]] for elem in airports] + [['Вернуться назад']]))
            return FIND_FLIGHTS_HANDLER
        update.message.reply_text('Введеный город не найден. Проверьте написание.')


def find_flights(bot, update, user_data):
    text = update.message.text
    if text == 'Вернуться назад':
        city = get_city(user_data['current_response'], 'ru_RU')
        airport_question(update, city)
        return SET_SECOND_CITY_HANDLER
    else:
        airport2 = text.split(', ')[-1]
        flights = get_flights(user_data['airport1'], airport2)
        if not flights:
            update.message.reply_text('Рейсов между указанными ранее аэропортами не найдено!')
            city = get_city(user_data['current_response'], 'ru_RU')
            airport_question(update, city)
            return SET_SECOND_CITY_HANDLER
        update.message.reply_text(flights[0], reply_markup=ReplyKeyboardMarkup(keyboard3))


def airport_question(update, city):
    airports = airs.get(city, 0)
    update.message.reply_text('Из какого аэропорта города {} вы хотите найти рейс?'.format(city),
                              reply_markup=ReplyKeyboardMarkup(
                                  [[elem[1] + ', ' + elem[0]] for elem in airports] + [['Вернуться назад']]))


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


(
    ENTER_NAME, ENTER_LOCATION, SEARCH_HANDLER, LOCATION_HANDLER,
    LOCATION_APPLY, MAIN_MENU, PROFILE_CONFIG, SPECIALIZATION_CONFIG,
    SPECIALIZATION_APPLY, KEYWORDS_CONFIG, KEYWORDS_APPLY,
    VACANCIES_HANDLER, NEWS_HANDLER, WEATHER_HANDLER, RASP_HANDLER,
    SET_SECOND_CITY_HANDLER, SET_SECOND_AIRPORT_HANDLER,
    FIND_FLIGHTS_HANDLER
) = range(18)

conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],

    states={
        ENTER_NAME: [MessageHandler(Filters.text, enter_name, pass_user_data=True)],
        ENTER_LOCATION: [MessageHandler(Filters.text, enter_location, pass_user_data=True)],
        LOCATION_APPLY: [MessageHandler(Filters.text, location_apply, pass_user_data=True)],

        MAIN_MENU: [MessageHandler(Filters.text, main_menu, pass_user_data=True)],

        PROFILE_CONFIG: [MessageHandler(Filters.text, profile_config, pass_user_data=True)],

        SPECIALIZATION_CONFIG: [MessageHandler(Filters.text, specialization_config, pass_user_data=True)],
        SPECIALIZATION_APPLY: [MessageHandler(Filters.text, specialization_apply, pass_user_data=True)],

        KEYWORDS_CONFIG: [MessageHandler(Filters.text, keywords_config, pass_user_data=True)],
        KEYWORDS_APPLY: [MessageHandler(Filters.text, keywords_apply, pass_user_data=True)],

        SEARCH_HANDLER: [
            MessageHandler(Filters.text, search_handler, pass_user_data=True),
            MessageHandler(Filters.voice, voice_to_text, pass_user_data=True)
        ],

        LOCATION_HANDLER: [
            MessageHandler(Filters.text, location_handler, pass_user_data=True),
            CallbackQueryHandler(choosing_map_type, pass_user_data=True),
        ],

        NEWS_HANDLER: [
            CallbackQueryHandler(scrolling_news, pass_user_data=True)
        ],

        VACANCIES_HANDLER: [
            CallbackQueryHandler(scrolling_vacancy, pass_user_data=True)
        ],

        WEATHER_HANDLER: [
            MessageHandler(Filters.text, weather, pass_user_data=True)
        ],

        RASP_HANDLER: [
            MessageHandler(Filters.text, schedule, pass_user_data=True)
        ],

        SET_SECOND_CITY_HANDLER: [
            MessageHandler(Filters.text, set_second_city, pass_user_data=True)
        ],

        SET_SECOND_AIRPORT_HANDLER: [
            MessageHandler(Filters.text, set_second_airport, pass_user_data=True)
        ],

        FIND_FLIGHTS_HANDLER: [
            MessageHandler(Filters.text, find_flights, pass_user_data=True)
        ]
    },

    fallbacks=[CommandHandler('stop', stop)]
)

if __name__ == '__main__':
    main()
