import sys
from flask import Flask, request
from random import choice
import requests
from requests import post
import logging
import json
from geo import get_distance_on_map, get_country, search_organization, get_traffic, show_on_map

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

    nothing_message = [
        "В вашем сообщении не было указано ничего того, что я умею. Может попробуйте еще раз? Если нужна помощь, то напишите 'помощь' или 'документация'",
        "Извините, вы что спросили? Может попробуйте еще раз? Если нужна помощь, то напишите 'помощь' или 'документация'",
        "Возможно вам нужна помощь? Напишите 'помощь' или 'документация'", "Хмм... забавно",
        "Может уже приступим к картам?"]
    # Ключевые слова
    help_words = ['помощь', 'документация']
    map_type_words = ['спутник', 'карта', 'гибрид']
    search_org_words = ['найди организацию', 'где находится организация']
    traffic_words = ['трафик', 'пробки']
    original_utterance = req['request']['original_utterance'].lower()

    # Если пользователь новый, то предоставляем ему информацию о навыке и просим представиться
    if req['session']['new']:
        res['response']['text'] = "Здравствуйте, данный навык позволяет получить некоторые геоданные, " \
                                  "используя API Яндекс.Карт, а также фотографии городов. " \
                                  "Напишите 'помощь' или 'документация', " \
                                  "чтобы получить полную информацию о работе навыка. " \
                                  "Но для начала, прошу вас представиться."
        sessionStorage[user_id] = {
            'first_name': None,
            'image_id': []
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
        res['response']['text'] = "Здравствуйте, " + sessionStorage[user_id][
            'first_name'].title() + " , вас приветствует навык 'pass'. " \
                            "Данный навык работает с API Яндекс.Карт. " \
                            "\n\nПо умолчаниию тип карты, возвращаемой навыком, 'карта', но если в вашем сообщении " \
                            "содержатся слова: 'карта', 'гибрид', 'спутник' - " \
                            "то навык это учтет и вернет карту соответствующего типа" \
                            "\n\nВведите 'найди организацию' или 'где находится организация', " \
                            "а затем название организации, разделив слова  помощью ' - ' или ': '. " \
                            "\nПример: 'Найди организацию - Аптека'" \
                            "\n\nЕсли в вашем сообщении содержится город и слова: 'пробка(и)', 'трафик', " \
                            "то навык вернет карту, показыващую трафик в данном городе." \
                            "\n\nЕсли в вашем сообщении содержится один город, " \
                            "то навык вернет карту с городом и расскажет о стране, в которой находится город." \
                            "\n\nЕсли в сообщении содержится два города, " \
                            "то навык вернет карту с городами и дистанцию между ними" \
                            "\n\nЕсли же в сообщении содержится несколько топонимов, то навык просто вернет карту, " \
                            "на которой отмечены данные топонимы."

        return

    # Узнаем тип карты
    map_type = 'карта'
    for word in req['request']['nlu']['tokens']:
        if word in map_type_words:
            map_type = word

    # Получаем список  всех городов во фразе
    cities = get_cities(req)
    if cities:
        # Если город один, то называем страну, в которой он находится
        if len(cities) == 1:
            try:
                # Получаем карту города и загружаем её на Яндекс.Диалоги
                image, country = get_country(cities[0], map_type)
                image_id = post_image(image)
                sessionStorage['image_id'].append(image_id)

                res['response']['text'] = 'Этот город в стране - ' + country
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Этот город в стране - ' + country
                res['response']['card']['image_id'] = image_id
            except Exception as e:
                res['response']['text'] = ':/ Что-то пошло не так. Ошибка: ' + e
            finally:
                return

        # Если же во фразе два города, то вычисляем расстояние между городами и отмечаем их на карте
        elif len(cities) == 2:
            try:
                # Получаем карту с городами и расстояние между ними,
                # загружаем фрагмент карты на Яндекс.Диалоги и получаем id изображения
                image, distance = get_distance_on_map(cities[0], cities[1], map_type)
                image_id = post_image(image)
                sessionStorage['image_id'].append(image_id)

                # Ответ в виде изображения карты с двумя городами
                res['response']['text'] = 'Расстояние между этими городами: ' + str(distance) + ' км.'
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Расстояние между этими городами: ' + str(distance) + ' км.'
                res['response']['card']['image_id'] = image_id
            except Exception as e:
                res['response']['text'] = ':/ Что-то пошло не так. Ошибка: ' + str(e)
            finally:
                return

    if len(cities) == 1:
        for word in req['request']['nlu']['tokens']:
            if word in traffic_words:
                try:
                    image = get_traffic(word, map_type)
                    image_id = post_image(image)
                    sessionStorage['image_id'].append(image_id)

                    # Ответ в виде карты города с трафиком
                    res['response']['text'] = 'Трафик в городе' + cities[0]
                    res['response']['card'] = {}
                    res['response']['card']['type'] = 'BigImage'
                    res['response']['card']['image_id'] = image_id
                    res['response']['card']['title'] = 'Трафик в городе' + cities[0]
                except Exception as e:
                    res['response']['text'] = ':/ Что-то пошло не так. Ошибка: ' + e
                finally:
                    return

    # Проверяем вхождение ключевого поискового слова в фразу
    splitting = False
    if ' - ' in original_utterance:
        splitter = ' - '
        splitting = True
    elif ': ' in original_utterance:
        splitter = ': '
        splitting = True
    if splitting:
        split_phrase = original_utterance.split(splitter)
        if split_phrase[0] in search_org_words:
            try:
                image, org_info = search_organization(split_phrase[-1], map_type)
                image_id = post_image(image)
                sessionStorage['image_id'].append(image_id)

                # Формируем список категорий, чтобы отобразить их в виде списка
                categories = [' Категории']
                for category in org_info['categories']:
                    categories.append(category)
                # Текст ответа
                text = 'Название организации: {}\nАдрес: {}\nURL: {}\n{}\n' \
                       'Часы работы организации: {}\n'.format(org_info['name'], org_info['address'],
                                                              org_info['url'], '\n '.join(categories),
                                                              org_info['hours'])

                # Ответ в виде изображения карты с отмеченной организацией
                res['response']['text'] = text
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['image_id'] = image_id
                res['response']['card']['title'] = text
            except Exception as e:
                res['response']['text'] = ':/ Ошибка в запросе. Попробуйте указать организацию точнее. Ошибка: ' + e
            finally:
                return

    toponyms = get_all_toponyms(req)
    if toponyms:
        try:
            image = show_on_map(toponyms, map_type)
            image_id = post_image(image)
            sessionStorage['image_id'].append(image_id)

            res['response']['text'] = 'Карта со всеми топонимами, указанными в вашем сообщении'
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['image_id'] = image_id
            res['response']['card']['title'] = 'Карта со всеми топонимами, указанными в вашем сообщении'
        except Exception as e:
            res['response']['text'] = ':/ Что-то пошло не так. Ошибка: ' + e
        finally:
            return
    else:
        res['response']['text'] = choice(nothing_message)


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


# Получаем топонимы из сообщения пользователя
def get_all_toponyms(req):
    toponyms = []
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            toponyms = entity['value'].values()
            break
    return toponyms


# Загружаем изображение на Яндекс.Диалоги
def post_image(files):
    skill_id = "f268642e-e326-4e68-8516-46ea1dfaa8e3"
    token = "AQAAAAAgSPKYAAT7o5rTzHsWUUMDm2-biDwcrFs"

    url = f'https://dialogs.yandex.net/api/v1/skills/{skill_id}/images'
    headers = {'Authorization': f'OAuth {token}'}
    response = post(url, files=files, headers=headers).json()
    return response['image']['id']


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
