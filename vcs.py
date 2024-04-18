import sys
from main import *


def main(args):
    if len(args) < 2:
        print("Usage: vcs <command> [arguments]")
        return

    cmd = args[1]
    if cmd == 'init':
        init()
        print(f'Создан репозиторий в {BASE_PATH}')
        return

    if not VCS_FOLDER.exists():
        print('Репозиторий еще не создан')
        return
    if cmd == 'commit':
        commit = make_commit()
        save_commit(commit)
    elif cmd == 'checkout':
        if len(args) < 3:
            print('Укажите хэш коммита к которому нужно вернуться')
            print('checkout <hash> <path>')
            return
        # создаем коммит перед возвратом к другому коммиту (иначе не найдет изменения)
        commit = make_commit(print_content=False)
        save_commit(commit)
        if len(args) < 4:
            restore_commit(args[2])
        else:
            restore_commit(args[2], args[3])
    elif cmd == 'history':
        commit_history(False)
    elif cmd == 'status':
        changes_list = status()
        for change in changes_list:
            print(*change)
    else:
        print(f'{cmd} не является командой')


if __name__ == "__main__":
    main(sys.argv)
