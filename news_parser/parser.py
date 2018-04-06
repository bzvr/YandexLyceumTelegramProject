from requests_html import HTMLSession
from maps_api.request import geocoder_request
from maps_api.geocoder import get_address, get_components


def get_city(data):
    address = get_address(data)

    data = geocoder_request(geocode=address, lang='en_US', format='json')
    components = get_components(data)
    if components is not None:
        for component in components[::-1]:
            if component['kind'] in ('province', 'locality'):
                return component['name']
    return None


def parse_news(data):
    session = HTMLSession()

    print('getting page')
    city = '_'.join(get_city(data).split())
    response = session.get(url.format(city))
    if response:
        print('page gotten')
        html = response.html.find(selectors[0])[1]

        stories = html.find(selectors[1])

        news = []
        for story in stories:
            link = story.find('h2 > a')[0]

            title = link.text
            href = 'https://news.yandex.ru/story' + link.attrs['href']

            text = story.find('div.story__text')[0].text
            news.append([title, text, href])
        return news
    else:
        print('error while getting page, status code: {}'.format(response.status_code))
        return None


url = 'https://news.yandex.ru/{}'

selectors = [(
    'body > div.rubber.rubber_content '
    '> div.rubber__col.rubber__col_left '
    '> div.page-content '
    '> div.page-content__cell'
), (
    'div > div.page-content__fixed '
    '> div.page-content__cell '
    '> div.page-content__col '
    '> div.page-content__cell '
    '> div.page-content__fixed '
    '> div.story'
)]
