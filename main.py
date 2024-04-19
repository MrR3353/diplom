import sys
from commands import *


def main(args):
    if len(args) < 2:
        print("Usage: vcs <command> [arguments]")
        return

    cmd = args[1]
    if cmd == 'init':
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
    elif cmd == 'history':
        commit_history(False)
        return
    elif cmd == 'status':
        changes_list = status()
        for change in changes_list:
            print(*change)
        return
    elif cmd == 'tree':
        if len(args) > 2:
            if args[2] == '-noignore':
                iter_folder(print_content=True, create_tree=False, gitignore=False)
                return
        iter_folder(print_content=True, create_tree=False)
        return
    else:
        print(f'{cmd} не является командой vcs')


if __name__ == "__main__":
    main(sys.argv)
