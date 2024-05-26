import datetime
import os.path
import sys

import requests
import zipfile
import io
import os

import commands
from config import BASE_PATH
from translate import phrase


def print_progress_bar(iteration, total, start_time, prefix='', suffix='', decimals=1, length=30, fill='█'):
    """
    Call in a loop to create a progress bar in the console with a timer.

    :param iteration: Current iteration (Int)
    :param total: Total iterations (Int)
    :param start_time: Start time of the process (Datetime)
    :param prefix: Prefix string (Str)
    :param suffix: Suffix string (Str)
    :param decimals: Positive number of decimals in percent complete (Int)
    :param length: Character length of bar (Int)
    :param fill: Bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)

    # Calculate elapsed time
    elapsed_time = datetime.datetime.now() - start_time
    elapsed_seconds = elapsed_time.total_seconds()

    # Calculate estimated total time and remaining time
    if iteration > 0:
        estimated_total_time = elapsed_seconds * total / iteration
        remaining_time = estimated_total_time - elapsed_seconds
    else:
        remaining_time = 0

    elapsed_str = str(datetime.timedelta(seconds=int(elapsed_seconds)))
    remaining_str = str(datetime.timedelta(seconds=int(remaining_time)))

    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix} Elapsed: {elapsed_str} Remaining: {remaining_str}')
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')


def send_file(filepath, url, token):
    # Открытие файла в режиме чтения двоичных данных
    with open(filepath, 'rb') as f:
        files = {'file': f}
        # data = {'token': token, 'path': os.path.relpath(filepath, BASE_PATH.parent)}
        data = {'token': token, 'path': os.path.relpath(filepath, BASE_PATH)}
        # Отправка POST-запроса с файлом и данными формы
        response = requests.post(url, files=files, data=data)

    if response.status_code != 200:
        raise Exception(f'Failed: {response.status_code} {response.text}')


def send_files(url, token, path=BASE_PATH):
    tree = commands.iter_folder(path=BASE_PATH, print_content=False)
    filenames = list(tree.get_filenames())
    total_tasks = len(filenames)
    start_time = datetime.datetime.now()
    for i in range(total_tasks):
        full_path = os.path.join(BASE_PATH.parent, filenames[i])
        try:
            send_file(full_path, url, token)
        except Exception as e:
            print(e)
            return
        print_progress_bar(i + 1, total_tasks, start_time, prefix='Progress:', suffix='Complete', length=40)


def download_and_extract_zip(username, repository_name, token=None, folder_path=None):
    url = f'http://127.0.0.1:8000/{username}/{repository_name}/download'
    params = {
        # 'token': token,
        # 'path': folder_path
    }
    os.makedirs(repository_name, exist_ok=True)
    response = requests.get(url, params=params)
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(repository_name)
        print(f"{phrase['Клонировано в'][commands.lang]} {os.path.join(BASE_PATH, repository_name)}")
    else:
        print(f"Failed to download the zip file. Status code: {response.status_code}")
        print(response.json())

