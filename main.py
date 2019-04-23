import sys
from flask import Flask, request
import requests
import logging
import json
from geo import get_distance_on_map, get_country, get_toponym

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(response, request.json)

    logging.info('Request: %r', response)

    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    help_words = ['помощь', 'документация']
    map_type_words = ['спутник', 'карта', 'гибрид']

    original_utterance = req['request']['original_utterance'].lower()

    # Если пользователь новый, то предоставляем ему информацию о навыке и просим представиться
    if req['session']['new']:
        res['response']['text'] = "Здравствуйте данный навык позволяет получить некоторые геоданные, " \
                                  "используя API Яндекс.Карт, а также фотографии городов. " \
                                  "Напишите 'помощь' или 'документация', " \
                                  "чтобы получить полную информацию о работе навыка. " \
                                  "Но для начала, прошу вас представиться."
        sessionStorage[user_id] = {
            'first_name': None
        }
        return
    if sessionStorage[user_id]['first_name'] is None:
        # Получаем первую именнованую сущность
        first_name = get_first_name(req)
        # Если не обнаружено - просим повторить
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        # Иначе записываем имя в словарь и обращаемся к пользователю по имени
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['text'] = 'Приятно познакомиться, ' + first_name.title() + '. Я - Алиса. Чем займемся?'
        return

    if original_utterance in help_words:
        res['response']['text'] = "Данный навык работает с API Яндекс.Карт..."
        return

    # Узнаем тип карты
    if original_utterance in map_type_words:
        for word in original_utterance:
            if word in map_type_words:
                map_type = word
    else:
        map_type = 'карта'

    # Получаем список  всех городов во фразе
    cities = get_cities(req)
    if cities:
        # Если город один, то называем страну, в которой он находится
        if len(cities) == 1:
            res['response']['text'] = 'Этот город в стране - ' + get_country(cities[0])
        # Если же во фразе два городо, то вычисляем расстояние между городами и отмечаем их на карте
        elif len(cities) == 2:
            image, distance = get_distance_on_map(cities[0], cities[1], map_type)
            res['response']['text'] = 'Расстояние между этими городами: ' + distance + ' км.'
        return


# Распознаем имя пользователя
def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


# Получаем города из сообщения пользователя
def get_cities(req):
    cities = []
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            if 'city' in entity['value'].keys():
                cities.append(entity['value']['city'])
    return cities


# Загружаем изображение на Яндекс.Диалоги
def post_image(image):
    skill_id = "f268642e-e326-4e68-8516-46ea1dfaa8e3"
    token = "AQAAAAAgSPKYAAT7o5rTzHsWUUMDm2-biDwcrFs"
    file_name = "map.png"

    try:
        with open(file_name, "wb") as file:
            file.write(image)
    except IOError as ex:
        print("Ошибка записи временного файла:", ex)
        sys.exit(2)

    url = f'https://dialogs.yandex.net/api/v1/skills/{skill_id}/images'
    files = {'file': open(file_name, 'rb')}
    headers = {'Authorization': f'OAuth {token}'}
    response = requests.get(url, files=files, headers=headers)
    image_id = response.json['image']['id']
    return image_id


def show_photo(city):
    pass
