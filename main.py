import sys
from commands import *

commands_dict = {
    'help': 'Информация о командах',
    'init': 'Создание репозитория',
    'remove': 'Удаление репозитория',
    'commit': 'Создание коммита',
    'checkout': 'Откат к коммиту',
    'hist': 'История коммитов',
    'status': 'Статус репозитория (отображает изменения)',
    'tree': 'Вывод файлов репозитория',
}


def print_help():
    print("Usage: vcs <command> [arguments]")
    print('Основные команды:')
    for command, description in commands_dict.items():
        print(
            f"   {command.ljust(10)} {textwrap.fill(description, width=70, initial_indent=' ' * 2, subsequent_indent=' ' * 12)}")


def main(args):
    if len(args) < 2:
        print(f'Укажите команду для выполнения\n'
              f'  vcs <command> [arguments]')
        return
    cmd = args[1]
    if cmd not in commands_dict:
        print(f'{cmd} не является командой vcs\n'
              f'Чтобы получить справку, введите:\n'
              f'  vcs help [arguments]')
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
            print(f'Репозиторий уже создан в {BASE_PATH}\n'
                  f'Чтобы создать новый, сначала удалите старый:\n'
                  f'Usage: vcs remove [arguments]')
            return
        init()
        print(f'Создан репозиторий в {BASE_PATH}')
        return

    if not VCS_FOLDER.exists():
        print('Репозиторий еще не создан')
        return

    if cmd == 'remove':
        remove_repo()
        print('Репозиторий удален')
        return
    elif cmd == 'commit':
        commit = make_commit()
        save_commit(commit)
        return
    elif cmd == 'checkout':
        if len(args) < 3:
            print(f'Укажите хэш коммита к которому нужно вернуться:\n'
                  f'Usage: checkout <hash> <path>')
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


if __name__ == "__main__":
    main(sys.argv)


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
+ история коммитов git log

+ просмотр изменений относительно последнего коммита git status (сравниваем текущий коммит и последний)
+ сделать бесконечный цикл и управление командами
+ сделать через команды в терминале
- сделать устновщик, который будет устанавливать все необходимые библиотеки и добавлять путь к vcs.bat в переменные среды

- добавление отслеживаемых файлов (сейчас отслеживаются все кроме игнорируемых) git add. Нужно ли???
- текстовые файлы обрабатывать отдельно при изменении - использовать модули changes/filechanges и хранить только изменения
- хранить в коммите бинарные данные (чтобы не было текста)


- создать сервер для vcs
- связать сервер с яндекс диском
- сделать git push
'''
