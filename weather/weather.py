import requests


def get_city_id(city, countrycode, token):
    locality = ','.join([city, countrycode])

    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/find",
                           params={'q': locality, 'type': 'like', 'units': 'metric', 'APPID': token})
        data = res.json()

        return data['list'][0]['id']

    except Exception as e:
        return -1


def get_current_weather(city, countrycode, token):
    city_id = get_city_id(city, countrycode, token)
    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/weather",
                           params={'id': city_id, 'units': 'metric', 'lang': 'ru', 'APPID': token})
        data = res.json()

        return 'Текущая погода в городе {}:\n\n-{} {}\n-Температура воздуха: {}°С\n-Влажность воздуха: {}%\n-Скорость ' \
               'ветра: {} м/с'.format(city, data['weather'][0]['description'].capitalize(), data['weather'][0]['icon'],
                                      data['main']['temp'], data['main']['humidity'], data['wind']['speed'])
    except Exception as e:
        print("Exception (find):", e)
        return 'Ошибка запроса! ПОгоды для данного города не найдено:('
        pass

