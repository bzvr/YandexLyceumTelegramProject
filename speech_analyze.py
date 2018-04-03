import requests
from uuid import uuid4


def speech_analyze(apikey, data):
    uuid = str(uuid4()).replace('-', '')
    url = 'https://asr.yandex.net/asr_xml?key=' + apikey + '&uuid=' + uuid + '&topic=queries&lang=ru-RU'
    headers = {"Content-Type": 'audio/x-wav'}
    tmp = requests.post(url, headers=headers, data=data)

    return tmp
