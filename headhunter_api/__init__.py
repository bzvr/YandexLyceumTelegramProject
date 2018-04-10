import requests
from maps_api.geocoder import get_city
from json import load


def vacancies_request(**kwargs):
    url = 'https://api.hh.ru/vacancies'

    response = requests.get(url, kwargs)

    if not response:
        raise RuntimeError(
            'Ошибка при выполнении запроса:\n{}\n'
            'Статус запроса: {}'.format(
                response.url, response.status_code
            )
        )

    return response.json()


def vacancies_city(data, **kwargs):
    city_name = get_city(data, 'ru_RU')
    city_id = cities_id[city_name]
    kwargs.update({'id': city_id})
    return vacancies_request(**kwargs)


with open('headhunter_api/cities.json') as f:
    cities_id = load(f)
