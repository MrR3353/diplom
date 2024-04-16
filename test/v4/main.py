import os
import shutil
import time
from pathlib import Path
from gitignore_parser import parse_gitignore

import etobasa
from etobasa import File, Tree, Commit, load
from config import VCS_FOLDER, BASE_PATH, GITIGNORE, DATA_FOLDER


def init():
    # git init
    os.makedirs(VCS_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(VCS_FOLDER, DATA_FOLDER), exist_ok=True)


def make_commit(path=BASE_PATH, gitignore=True, print_content=True):
    # git commit
    def print_folder(path):
        '''
        Выводит файловую структуру path
        '''
        stack = [(Path(path), -1)]
        while stack:
            current_path, tab = stack.pop()
            print('|   ' * tab, '| - ' if tab >= 0 else '', current_path.name, sep='')
            if current_path.is_dir():
                subfolders = reversed(list(current_path.iterdir()))
                for obj in subfolders:
                    stack.append((obj, tab + 1))

    def obj_in_gitignore(obj, obj_tab, gitignore_stack):
        '''
        Проверяет игнорировать ли obj
        :param obj: Путь к объекту файловой системы
        :param obj_tab: уровень вложенности объекта
        :param gitignore_stack: список файлов gitignore и их уровней вложенности
        :return:
        '''
        if obj.name == VCS_FOLDER:
            return True
        for gitignore_path, tab in gitignore_stack:
            if tab <= obj_tab:
                matches = parse_gitignore(gitignore_path)
                if matches(obj):
                    return True
        return False

    def iter_folder(path, gitignore=True, print_content=True, copy=False):
        '''
        Проходится по файлам и папкам проекта и создает коммит (снимок) проекта
        :param path: путь к папке
        :param gitignore: нужно ли игнорировать файлы
        :param print_content: печатать ли содержимое проекта
        :param copy: нужно ли копировать файлы целиком
        :return:
        '''
        stack = [(Path(path), 0)]  # путь к файлу и уровень вложенности
        gitingore_stack = []  # файлы gitingore и их уровень вложенности
        if path == os.getcwd():  # добавляем переход наверх для дерева проекта
            path = os.path.join('..', stack[0][0].name)

        root_tree = Tree(path)  # корневое дерево
        tree_stack = [(root_tree, 0)]  # стек деревьев (папок) и их уровней вложенности

        while stack:
            current_path, tab = stack.pop()  # берем файл и его уровень вложенности
            while len(tree_stack) > 0 and tree_stack[-1][1] > tab:
                tree_stack.pop()  # удаляем папки, файлы которых уже перебрали из стека

            if gitignore:
                # удаляем файл gitignore из стека, когда перебрали все файлы в его уровне вложенности
                while len(gitingore_stack) > 0 and gitingore_stack[-1][1] > tab:
                    gitingore_stack.pop()

                gitignore_path = Path.joinpath(current_path.parent, GITIGNORE)
                if gitignore_path.exists() and (gitignore_path, tab) not in gitingore_stack:
                    gitingore_stack.append((gitignore_path, tab))

            if not obj_in_gitignore(current_path, tab, gitingore_stack):
                if print_content:
                    print('|   ' * (tab - 1), '| - ' if tab > 0 else '', current_path.name, sep='')

                if copy:
                    # Получаем относительный путь от базового пути
                    relative_path = current_path.relative_to(BASE_PATH)
                    new_path = os.path.join(BASE_PATH, VCS_FOLDER, str(relative_path))
                    # папку проекта игнорируем и пропускаем файлы которые уже есть
                    if current_path.name != Path(BASE_PATH).name and not os.path.exists(new_path):
                        if not current_path.is_dir():
                            shutil.copy2(current_path, new_path)
                        else:
                            os.mkdir(new_path)

                # создаем дерево проекта
                relative_path = current_path.relative_to(BASE_PATH)
                if current_path.name != Path(BASE_PATH).name:  # папку проекта игнорируем
                    if not current_path.is_dir():
                        file = File(relative_path)
                        tree_stack[-1][0].add_child(file)  # добавляем файл в дерево
                    else:
                        tree = Tree(relative_path)
                        tree_stack[-1][0].add_child(tree)  # добавляем дерево в дерево
                        tree_stack.append((tree, tab + 1))

                # если объект - папка, то добавляем его содержимое в стек
                if current_path.is_dir():
                    subfolders = reversed(list(current_path.iterdir()))
                    for obj in subfolders:
                        stack.append((obj, tab + 1))

        return root_tree

    tree = iter_folder(path=path, gitignore=gitignore, print_content=print_content)
    return Commit(tree)


def save_commit(new_commit):
    head = Path(os.path.join(VCS_FOLDER, 'HEAD'))
    if not head.exists():  # создаем HEAD, записываем туда хэш коммита
        with open(head, 'w') as file:
            file.write(new_commit.hash)
        # сохраняем коммит
        new_commit.save(os.path.join(VCS_FOLDER, DATA_FOLDER))
        print(f'Сохранен коммит {new_commit.hash}')
    else:
        with open(head, 'r') as file:
            prev_commit_hash = file.read()
        # загружаем предыдущий коммит
        prev_commit = load(os.path.join(VCS_FOLDER, DATA_FOLDER, prev_commit_hash))
        # указываем у нового коммита в качестве родителя пред предыдущий коммит, чтобы родители не учитывались при сравнении
        new_commit = Commit(new_commit.tree, prev_commit.parent_hash)
        if prev_commit_hash != new_commit.hash:
            # TODO - это не поменяет хэш коммита, так как хеш создается в конструкторе
            # new_commit.parent_hash = prev_commit_hash
            # TODO: переписать код, чтобы не создавать коммит 3 раза
            # указываем у нового коммита в качестве родителя предыдущий
            new_commit = Commit(new_commit.tree, prev_commit_hash)
            # сохраняем коммит
            new_commit.save(os.path.join(VCS_FOLDER, DATA_FOLDER))
            print(f'Сохранен коммит {new_commit.hash}')
            # обновляем HEAD
            with open(head, 'w') as file:
                file.write(new_commit.hash)
        else:
            # новый коммит = предыдущий коммит
            print(f'Коммит не создан. Нет изменений')
            pass


def load_commit(commit_hash):
    # загружаем коммит
    path = os.path.join(VCS_FOLDER, DATA_FOLDER, commit_hash)
    if not os.path.exists(path):
        raise Exception(f'Нет коммита {commit_hash}')
    commit = load(path)
    commit.load()
    return commit


def restore_commit(commit_hash, path):
    commit = load_commit(commit_hash)
    # берем только имя проекта, потому что полный путь содержит переход на уровень вверх
    os.mkdir(os.path.join(path, commit.tree.name.name))
    # добавляем папку проекта к пути
    path = os.path.join(path, commit.tree.name.name)

    def walk_tree(tree):
        for child in tree.children:
            if isinstance(child, File):
                with open(os.path.join(path, child.name), 'wb') as f:
                    f.write(child.blob.content)
            elif isinstance(child, Tree):
                os.mkdir(os.path.join(path, child.name))
                walk_tree(child)

    walk_tree(commit.tree)


def commit_history(briefly=True):
    head = Path(os.path.join(VCS_FOLDER, 'HEAD'))
    if not head.exists():
        print('История коммитов пуста')
    else:
        commits = []
        # добавляем последний коммит
        with open(head, 'r') as file:
            last_commit_hash = file.read()
        commit = load(os.path.join(VCS_FOLDER, DATA_FOLDER, last_commit_hash))
        commits.append(commit.hash)

        # проходимся по всем предыдущим коммитам
        while commit.parent_hash is not None:
            commit = load(os.path.join(VCS_FOLDER, DATA_FOLDER, commit.parent_hash))
            commits.append(commit.hash)

        # берем в убыв порядке и оставляем только 4 символа хэша
        commits.reverse()
        if briefly:
            commits = [commit[:4] for commit in commits]
        print(*commits, sep=' -> ')


def status():
    new_commit = make_commit(os.path.join(os.getcwd(), 'folder', '11'))
    # new_commit = make_commit(print_content=False)
    head = Path(os.path.join(VCS_FOLDER, 'HEAD'))
    if not head.exists():
        # это первый коммит
        pass
    else:
        with open(head, 'r') as file:
            last_commit_hash = file.read()
        prev_commit = load(os.path.join(VCS_FOLDER, DATA_FOLDER, last_commit_hash))
        prev_commit.load()
        # сравниваем prev_commit и new_commit
        new_commit = Commit(new_commit.tree, prev_commit.parent_hash)

        if new_commit.hash == prev_commit.hash:
            print('Изменений нет')
            return
        else:
            # дерево проекта отличается
            prev_tree = prev_commit.tree
            new_tree = new_commit.tree
            prev_child_hash = ''.join([child.hash for child in prev_tree.children])
            new_child_hash = ''.join([child.hash for child in new_tree.children])
            if prev_child_hash == new_child_hash:
                print(f'Папка {prev_tree.name} переименована в {new_tree.name}')
            else:
                print('отличается содержимое')
                print(prev_child_hash)
                print(new_child_hash)
                print(prev_tree.name)
                print(new_tree.name)
                print(prev_tree.children[0].name)
                print(new_tree.children[0].name)
                print(prev_tree.children[0].children[0].name)
                print(new_tree.children[0].children[0].name)
                pass



if __name__ == '__main__':
    start = time.time()
    init()
    # new_commit = make_commit()
    # save_commit(new_commit)
    status()
    # commit = load_commit('78303533757299d15c3b0accf8412ee2f43466ef')
    # commit.tree.print_tree()
    # os.mkdir('.vcs/restore')
    # restore_commit('c40c4000814c516d7ad9ed9465cf3335cbe2a1c0', '.vcs/restore')
    # commit_history(briefly=False)
    print(time.time() - start)

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
+- восстановление проекта из коммита (нужно ли изменять HEAD?) нужно ли удалять все файлы?
+ история коммитов git log

- просмотр изменений относительно последнего коммита git status
сравниваем текущий коммит и последний
- сделать бесконечный цикл и управление командами
- сделать через команды в терминале

- добавление отслеживаемых файлов (сейчас отслеживаются все кроме .gitignore) git add. Нужно ли???
- текстовые файлы обрабатывать отдельно при изменении - использовать модуль changes и хранить только изменения
- хранить в коммите бинарные данные (чтобы не было текста)


- создать сервер для vcs
- связать сервер с яндекс диском
- сделать git push
'''
