import requests


def specialization_suggest(text):
    return {
        suggest['text']: suggest['id'] for suggest in requests.get(
            'https://api.hh.ru/suggests/fields_of_study', {
                'text': text, 'locale': 'RU'
            }
        ).json()['items']
    }


def keywords_suggest(text):
    return [
        suggest['text'] for suggest in requests.get(
            'https://api.hh.ru/suggests/vacancy_search_keyword', {
                'text': text
            }
        ).json()['items']
    ]


def region_suggest(text):
    return {
        suggest['text']: suggest['id'] for suggest in requests.get(
            'https://api.hh.ru/suggests/areas', {
                'text': text, 'locale': 'RU'
            }
        ).json()['items']
    }
