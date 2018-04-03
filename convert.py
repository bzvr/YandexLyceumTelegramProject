import cloudconvert
import requests


def convert(token, file):
    api = cloudconvert.Api(token)
    process = api.convert({
        'inputformat': 'oga',
        'outputformat': 'wav',
        'input': 'download',
        'file': file
    })
    process.wait()
    data = process.data
    return requests.get('http:' + data['output']['url']).content
