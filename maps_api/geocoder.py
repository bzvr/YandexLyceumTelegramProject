from maps_api.request import geocoder_request


def get_components(data):
    try:
        for i in ['response', 'GeoObjectCollection', 'featureMember',
                  0, 'GeoObject', 'metaDataProperty', 'GeocoderMetaData',
                  'Address', 'Components']:
            data = data[i]
        return data
    except (IndexError, KeyError):
        return None


def get_city(geocode, lang='ru_RU'):
    data = geocoder_request(geocode=geocode, lang=lang, format='json')
    components = get_components(data)
    if components is not None:
        for component in components[::-1]:
            if component['kind'] in ('province', 'locality'):
                return component['name']
    return None


def get_address(data):
    try:
        for i in ['response', 'GeoObjectCollection', 'featureMember', 0,
                  'GeoObject', 'metaDataProperty', 'GeocoderMetaData', 'text']:
            data = data[i]
        return data
    except (IndexError, KeyError):
        return None


def get_pos(data):
    pos = data
    for i in ['response', 'GeoObjectCollection', 'featureMember',
              0, 'GeoObject', 'Point', 'pos']:
        pos = pos[i]
    return list(map(float, pos.split()))


def get_bbox(data):
    envelope = data
    for i in ['response', 'GeoObjectCollection', 'featureMember',
              0, 'GeoObject', 'boundedBy', 'Envelope']:
        envelope = envelope[i]

    return list(map(float, envelope['lowerCorner'].split())) + list(map(float, envelope['upperCorner'].split()))
