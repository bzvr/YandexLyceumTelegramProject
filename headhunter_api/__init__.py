import requests


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


def full_vacancy_request(id, **kwargs):
    url = 'https://api.hh.ru/vacancies/{}'.format(id)

    response = requests.get(url, kwargs)

    if not response:
        raise RuntimeError(
            'Ошибка при выполнении запроса:\n{}\n'
            'Статус запроса: {}'.format(
                response.url, response.status_code
            )
        )

    return response.json()
