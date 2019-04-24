import sys
import requests
from math import sin, cos, sqrt, atan2, radians

# URL StaticAPI
static_api_server = "http://static-maps.yandex.ru/1.x/"
# URL GeocoderAPI
geocoder_api_server = "https://geocode-maps.yandex.ru/1.x/"
# URL поиска по организациям
search_organization_server = 'https://search-maps.yandex.ru/v1/'
# Ключ для поиска по организациям
search_api_key = 'dda3ddba-c9ea-4ead-9010-f43fbc15c6e3'
# Словарь типов карты
map_type_dict = {'карта': 'map', 'спутник': 'sat', 'гибрид': 'sat,skl'}


# Получение топонима
def get_toponym(toponym):
    global geocoder_api_server

    params = {
        'geocode': toponym,
        'format': 'json'
    }

    response = requests.get(geocoder_api_server, params)
    # Преобразование ответа в json-объект
    json_response = response.json()
    # Получение первого топонима из ответа геокодера.
    toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]

    return toponym


# Получение расстояния между двумя городами, а также карты, где они отмечены и соединены линией
def get_distance_on_map(city1, city2, map_type):
    # Получение типа карты
    global map_type_dict
    map_type = map_type_dict[map_type]

    global static_api_server

    # Получение топонимов городов
    city1 = get_toponym(city1)
    city2 = get_toponym(city2)
    # Получение координатов городов
    city1_longitude, city1_latitude = city1["Point"]["pos"].split(" ")
    city2_longitude, city2_latitude = city2["Point"]["pos"].split(" ")

    map_params = {
        "l": map_type,
        "pt": ",".join([city1_longitude, city1_latitude]) + ",pm2rdl1~" + ",".join(
            [city2_longitude, city2_latitude]) + ",pm2rdl2",
        "pl": "c:911e42AA," + ",".join([city1_longitude, city1_latitude, city2_longitude, city2_latitude])
    }

    response = requests.get(static_api_server, params=map_params)
    files = {'file': response.content}
    distance = get_distance([float(x) for x in [city1_longitude, city1_latitude]],
                            [float(x) for x in [city2_longitude, city2_latitude]])
    return files, distance


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


def get_country(city, map_type):
    global geocoder_api_server
    global static_api_server

    # Получение типа карты
    global map_type_dict
    map_type = map_type_dict[map_type]

    city = get_toponym(city)

    country = city['metaDataProperty']['GeocoderMetaData']['AddressDetails']['Country']['CountryName']

    map_params = {
        "l": map_type,
        "pt": ",".join(city["Point"]["pos"]) + ",pm2rdl1~"
    }

    response = requests.get(static_api_server, params=map_params)
    files = {'file': response.content}
    return files, country


def search_organization(organization, map_type):
    global static_api_server
    global search_organization_server
    global search_api_key

    # Получение типа карты
    global map_type_dict
    map_type = map_type_dict[map_type]

    # Словарь с данными об организации
    org_info = {}

    search_params = {
        "apikey": search_api_key,
        "text": organization,
        "lang": "ru_RU",
        "type": "biz"
    }

    response = requests.get(search_organization_server, params=search_params)
    json_response = response.json()

    # Получаем первую найденную организацию.
    organization = json_response["features"][0]

    # Название организации.
    org_info["org_name"] = organization["properties"]["CompanyMetaData"]["name"]
    # Адрес организации.
    org_info["org_address"] = organization["properties"]["CompanyMetaData"]["address"]
    # URL организации
    org_info["url"] = organization["properties"]["CompanyMetaData"]["url"]
    # Категории организации
    org_info['categories'] = []
    if organization["properties"]["CompanyMetaData"]["Categories"]:
        for i in range(len(organization["properties"]["CompanyMetaData"]["Categories"])):
            org_info['categories'].append(
                str(i) + '. ' + organization["properties"]["CompanyMetaData"]["Categories"]['name'])
    else:
        org_info['categories'].append('Пусто')
    # Время работы
    org_info['hours'] = organization["properties"]["CompanyMetaData"]["Hours"]["text"]

    # Получаем координаты ответа.
    point = organization["geometry"]["coordinates"]
    org_point = "{0},{1}".format(point[0], point[1])
    delta = "0.005"

    map_params = {
        "spn": ",".join([delta, delta]),
        "l": map_type,
        "pt": "{0},work".format(org_point)
    }

    response = requests.get(static_api_server, params=map_params)
    files = {'file': response.content}
    return files, org_info


def get_traffic(city, map_type):
    global static_api_server

    # Получение типа карты
    global map_type_dict
    map_type = map_type_dict[map_type]

    # Получение топонима города
    city = get_toponym(city)
    # Получение координатов городов
    points = city["Point"]["pos"].split()

    map_params = {
        "l": map_type + 'trf,skl',
        "ll": ",".join(points)
    }

    response = requests.get(static_api_server, params=map_params)
    files = {'file': response.content}
    return files


def show_on_map(toponyms, map_type):
    global static_api_server

    # Получение типа карты
    global map_type_dict
    map_type = map_type_dict[map_type]

    toponyms_points = []
    for toponym in toponyms:
        toponyms_points.append(','.join(get_toponym(toponym)["Point"]["pos"].split()))

    # Формируем метки
    pt = '~'.join(',flag'.join(toponyms_points))
    map_params = {
        "l": map_type,
        "pt": ''
    }

    response = requests.get(static_api_server, params=map_params)
    files = {'file': response.content}
    return files
