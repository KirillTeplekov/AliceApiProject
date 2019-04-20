import sys
import requests
from math import sin, cos, sqrt, atan2, radians

static_api_server = "http://static-maps.yandex.ru/1.x/"
geocoder_api_server = "https://geocode-maps.yandex.ru/1.x/"


def get_toponym(toponym):
    global geocoder_api_server

    params = {
        'geocode': toponym,
        'format': 'json'
    }

    # Запрос к геокодеру
    response = requests.get(geocoder_api_server, params)
    # Преобразуем ответ в json-объект
    json_response = response.json()
    # Получаем первый топоним из ответа геокодера.
    toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]

    return toponym


def get_distance_on_map(city1, city2, map_type="map"):
    global static_api_server

    city1 = get_toponym(city1)
    city2 = get_toponym(city2)
    # Получаем координаты городов
    city1_longitude, city1_lattitude = city1["Point"]["pos"].split(" ")
    city2_longitude, city2_lattitude = city2["Point"]["pos"].split(" ")

    # Собираем параметры для запроса к StaticMapsAPI:
    map_params = {
        "l": map_type,
        "pt": ",".join([city1_longitude, city1_lattitude]) + ",pm2rdl1~" + ",".join(
            [city2_longitude, city2_lattitude]) + ",pm2rdl2",
        "pl": "c:911e42AA," + ",".join([city1_longitude, city1_lattitude, city2_longitude, city2_lattitude])
    }

    response = requests.get(static_api_server, params=map_params)
    image = response.content
    distance = get_distance([float(x) for x in [city1_longitude, city1_lattitude]],
                            [float(x) for x in [city2_longitude, city2_lattitude]])
    return distance, image


def get_distance(p1, p2):
    R = 6373.0

    lon1 = radians(p1[0])
    lat1 = radians(p1[1])
    lon2 = radians(p2[0])
    lat2 = radians(p2[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance


def get_country(city):
    url = "https://geocode-maps.yandex.ru/1.x/"

    params = {
        'geocode': city,
        'format': 'json'
    }

    response = requests.get(url, params)
    json = response.json()

    return \
        json['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
            'GeocoderMetaData'][
            'AddressDetails']['Country']['CountryName']
