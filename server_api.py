import os.path
import requests

import commands
from config import BASE_PATH


def send_file(filepath, url, token):
    # Открытие файла в режиме чтения двоичных данных
    with open(filepath, 'rb') as f:
        files = {'file': f}
        # data = {'token': token, 'path': os.path.relpath(filepath, BASE_PATH.parent)}
        data = {'token': token, 'path': os.path.relpath(filepath, BASE_PATH)}
        # Отправка POST-запроса с файлом и данными формы
        response = requests.post(url, files=files, data=data)

    # Проверка ответа сервера
    if response.status_code == 200:
        print('Success:', response.json())
    else:
        print('Failed:', response.status_code, response.text)


def send_files(url, token, path=BASE_PATH):
    tree = commands.iter_folder(path=BASE_PATH, print_content=False)
    filenames = list(tree.get_filenames())
    for filename in filenames:
        full_path = os.path.join(BASE_PATH.parent, filename)
        send_file(full_path, url, token)
