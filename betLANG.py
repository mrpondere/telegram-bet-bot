import json
import os

texts = {}
lang = 'en'
path = os.path.dirname(os.path.abspath(__file__))


with open(path + '/lang.json') as json_data:
    texts = json.load(json_data)


def change_lang(lan='en'):
    global lang
    if texts.get(lan):
        lang = lan
    else:
        print 'Language not translated yet.'
    return lang


def gettext(string):
    if texts.get(lang) and texts[lang].get(string):
        return texts[lang][string]
    return string
