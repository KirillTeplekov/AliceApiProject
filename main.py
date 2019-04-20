import sys
from flask import Flask, request
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

    cities = get_cities(req)

    if req['session']['new']:
        res['response']['text'] = "Здравствуйте данный навык позволяет получить некоторые геоданные, " \
                                  "используя API Яндекс.Карт, а также фотографии городов. " \
                                  "Напишите 'помощь', чтобы получить полную информацию о работе навыка. " \
                                  "Но для начала, прошу вас представиться."
        sessionStorage[user_id] = {
            'first_name': None
        }

    elif sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['text'] = 'Приятно познакомиться, ' + first_name.title() + '. Я - Алиса. Чем займемся?'

    elif req['request']['original_utterance'] in help_words:
        res['response']['text'] = "Данный навык работает с API Яндекс.Карт."

    elif req['request']['original_utterance']:
        pass

    elif cities:
        if len(cities) == 0:
            res['response']['text'] = 'Ты не написал название не одного города!'
        elif len(cities) == 1:
            res['response']['text'] = 'Этот город в стране - ' + get_country(cities[0])
        elif len(cities) == 2:
            image, distance = get_distance_on_map(cities[0], cities[1], map_type)
            res['response']['text'] = 'Расстояние между этими городами: ' + distance + ' км.'
        else:
            pass
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


def post_image(image):
    map_file = "map.png"
    try:
        with open(map_file, "wb") as file:
            file.write(image)
    except IOError as ex:
        print("Ошибка записи временного файла:", ex)
        sys.exit(2)
    url = f'https://dialogs.yandex.net/api/v1/skills/{skill_id}/images'
    files = {'file': open(map_file, 'rb')}
    headers = {'Authorization': f'OAuth {token}'}
    s = post(url, files=files, headers=headers)


def show_photo(city):
    pass
