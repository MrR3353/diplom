import sys
import textwrap

import crypto
import server_api
from commands import *
from translate import commands_dict, phrase


def print_help():
    lang = get_config('CLIENT', 'lang')
    print(f"{phrase['Пример'][lang]}: vcs <{phrase['команда'][lang]}> [{phrase['аргументы'][lang]}]")
    print(phrase['Основные команды'][lang])
    for command, description in commands_dict.items():
        print(
            f"   {command.ljust(10)} {textwrap.fill(description[lang], width=70, initial_indent=' ' * 2, subsequent_indent=' ' * 12)}")


def main(args):
    try:
        lang = get_config('CLIENT', 'lang')
    except KeyError:
        lang = 'ru'

    if len(args) < 2:
        print(f"{phrase['Укажите команду для выполнения'][lang]}\n"
              f"{phrase['Пример'][lang]}: vcs <{phrase['команда'][lang]}> [{phrase['аргументы'][lang]}]")
        return
    cmd = args[1]
    if cmd not in commands_dict:
        print(f"{cmd} {phrase['не является командой'][lang]}\n"
              f"{phrase['Чтобы получить справку, введите'][lang]}:\n"
              f"{phrase['Пример'][lang]}: vcs help [{phrase['аргументы'][lang]}]")
        return

    if cmd == 'help':
        print_help()
        return
    elif cmd == 'tree':
        if len(args) > 2:
            if args[2] == '-noignore':
                iter_folder(print_content=True, create_tree=False, gitignore=False)
                return
        iter_folder(print_content=True, create_tree=False)
        return
    elif cmd == 'init':
        if VCS_FOLDER.exists():
            print(f"{phrase['Репозиторий уже создан в'][lang]} {BASE_PATH}\n"
                  f"{phrase['Чтобы создать новый, сначала удалите старый'][lang]}:\n"
                  f"{phrase['Пример'][lang]}: vcs remove [{phrase['аргументы'][lang]}]")
            return
        init()
        print(f"{phrase['Создан репозиторий в'][lang]} {BASE_PATH}")
        return

    if not VCS_FOLDER.exists():
        print(f"{phrase['Репозиторий еще не создан'][lang]}")
        return

    if cmd == 'remove':
        remove_repo()
        print(f"{phrase['Репозиторий удален'][lang]}")
        return
    elif cmd == 'commit':
        commit = make_commit()
        save_commit(commit)
        return
    elif cmd == 'rollback':
        if len(args) < 3:
            print(f"{phrase['Укажите хэш коммита к которому нужно вернуться'][lang]}:\n"
                  f"{phrase['Пример'][lang]}: vcs rollback <{phrase['хэш'][lang]}> <{phrase['путь'][lang]}>")
            return
        # создаем коммит перед возвратом к другому коммиту (иначе не найдет изменения)
        commit = make_commit(print_content=False)
        save_commit(commit)
        if len(args) < 4:
            restore_commit(args[2])
        else:
            restore_commit(args[2], args[3])
        return
    elif cmd == 'hist':
        commit_history(False)
        return
    elif cmd == 'status':
        changes_list = status()
        for change in changes_list:
            print(*change)
        return
    elif cmd == 'lang':
        if len(args) < 3:
            print(f"{phrase['Укажите используемый язык'][lang]}:\n"
                  f"{phrase['Пример'][lang]}: vcs lang [ru/en]")
            return
        if args[2] in ('ru', 'en'):
            change_config('CLIENT', 'lang', args[2])
        else:
            print(f"{phrase['Указан неверный язык'][lang]}: {args[2]}\n"
                  f"{phrase['Пример'][lang]}: vcs lang [ru/en]")
        return
    elif cmd == 'crypt':
        key = crypto.generate_key()
        crypto.encrypt_folder(key, encrypt=True)
        # crypto.encrypt_folder(key, encrypt=True, path=DATA_FOLDER)
        print(f"{phrase['Репозиторий зашифрован, ключ'][lang]} = {key.decode()}")
        return
    elif cmd == 'decrypt':
        if len(args) > 2:
            key = args[2]
        else:
            try:
                key = crypto.load_key()
            except FileNotFoundError:
                print(f"{phrase['Нужно указать ключ шифрования или добавить файл с ключом key'][lang]}\n"
                      f"{phrase['Пример'][lang]}: vcs decrypt <key>")
                return
        crypto.encrypt_folder(key, encrypt=False)
        # crypto.encrypt_folder(key, encrypt=False, path=DATA_FOLDER)
        print(f"{phrase['Репозиторий расшифрован'][lang]}")
        return
    elif cmd == 'push':
        username = get_config('CLIENT', 'username')
        repository_name = get_config('CLIENT', 'repository_name')
        token = get_config('CLIENT', 'token')
        server_api.send_files(f'http://127.0.0.1:8000/{username}/{repository_name}/upload', token)
        return


if __name__ == "__main__":
    main(sys.argv)

# TODO: возможно не стоит хранить информацию о папке проекта (как и в git) и хранить только внутренние файлы (ХЗ)
'''
+ хранение данных файлов и папок в бинарных файлах
+ игнорирование того что в .gitignore
+ сравнение коммитов по хэшам
+ сравнение текстовых файлов посимвольно
+ не сохранять информацию, совпадающую с предыдущим коммитом save_commit
хранить блобы, файлы и деревья как отдельные бинарные файлы, с названием хэша
в файле хранить хэш блоба
в дереве хранить хэши файлов и деревьев
в коммите хранить хэши дерева
+ восстановление проекта из коммита (нужно ли изменять HEAD?) нужно ли удалять все файлы?
+ история коммитов git hist

+ просмотр изменений относительно последнего коммита git status (сравниваем текущий коммит и последний)
+ сделать бесконечный цикл и управление командами
+ сделать через команды в терминале

+ выбор языка (рус/англ)
+ шифрование/дешифрование репозитория по ключу
- Автокоммит через определённое время (при наличии изменений)
+- просмотр изменений между коммитами
- просмотр изменений между версиями файла

- Локальный сайт вместо GUI приложения. Поднимается локально сайт, в котором можно выполнять действия с репозиторием, как в консоли  
- сделать устновщик, который будет устанавливать все необходимые библиотеки и добавлять путь к vcs.bat в переменные среды
- текстовые файлы обрабатывать отдельно при изменении - использовать модули changes/filechanges и хранить только изменения
- подсказки по командам (для новичков)
- хранить в коммите бинарные данные (чтобы не было текста)
- добавление отслеживаемых файлов (сейчас отслеживаются все кроме игнорируемых) git add. Нужно ли???


+ создать сервер для vcs
- связать сервер с клиентом
- сделать git push
1) Выбор сервера для хранения (или бэкапа) репозитория (яндекс диск, гугл диск, маил ру)
2) Торговая площадка, для возможности   продавать свой репозиторий/библиотеку/приложение.
3) Временная навигация.  Просмотр истории изменений с помощью интерфейса  шкалы времени/календаря
'''
