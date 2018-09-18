from schedule_api.airports import airs
from os import environ
# from config import RASP_TOKEN
RASP_TOKEN = environ['schedule']

import requests


def get_flights(_from, _to):
    try:
        res = requests.get("https://api.rasp.yandex.net/v3.0/search/?",
                           params={'from': _from, 'to': _to, 'format': 'json', 'lang': 'ru_RU', 'system': 'iata',
                                   'transport_types': 'plane',
                                   'apikey': RASP_TOKEN})
        data = res.json()
        flights = []

        for segment in data['segments']:
            arrival_time, departure_time = segment['arrival'][:-3], segment['departure'][:-3]
            flight_direction, flight_number = segment['thread']['title'], segment['thread']['number']
            company_name, company_url, company_logo = segment['thread']['carrier']['title'], \
                                                      segment['thread']['carrier']['url'], 'https:' + \
                                                      str(segment['thread']['carrier']['logo'])
            company_contacts = segment['thread']['carrier']['contacts'].replace('<br>', '')
            days = segment['days']

            flight = 'Рейс {} по направлению {}\n\nВылет (местное время пункта вылета): {}\nПрилет (местное время пункта ' \
                     'прилета): {}\nДни: {}\nАвиакомания: {}\nКонтакты: {}\nСайт компании: {}'.format(
                flight_number, flight_direction, arrival_time, departure_time, days if days else 'Нет информации',
                company_name, company_contacts if company_contacts else 'Нет информации',
                company_url if company_url else 'Нет информации'
            )
            flights.append(flight)

        return flights
    except Exception as e:
        print(e)
