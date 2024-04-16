import os
import shutil
import time
from pathlib import Path
from gitignore_parser import parse_gitignore
from etobasa import File, Tree, Commit, load
from config import VCS_FOLDER, BASE_PATH, GITIGNORE, COMMITS_FOLDER


def init():
    # git init

    os.makedirs(VCS_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(VCS_FOLDER, COMMITS_FOLDER), exist_ok=True)


def commit():
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
        root_tree = Tree(Path(os.path.join('..', stack[0][0].name)))  # дерево проекта
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

    tree = iter_folder(BASE_PATH, gitignore=True, print_content=True)
    return Commit(tree)


def save_commit(new_commit):
    # TODO: не сохранять информацию, совпадающую с предыдущим коммитом
    # проверять хэши деревьев, файлов и блобов

    head = Path(os.path.join(VCS_FOLDER, 'HEAD'))
    if not head.exists():  # создаем HEAD, записываем туда хэш коммита
        with open(head, 'w') as file:
            file.write(new_commit.hash)
        # сохраняем коммит
        os.mkdir(os.path.join(VCS_FOLDER, COMMITS_FOLDER, new_commit.hash[:4]))
        new_commit.save(os.path.join(VCS_FOLDER, COMMITS_FOLDER, new_commit.hash[:4]))
    else:
        with open(head, 'r') as file:
            prev_commit_hash = file.read()
        # загружаем предыдущий коммит
        prev_commit = load(os.path.join(VCS_FOLDER, COMMITS_FOLDER, prev_commit_hash[:4], prev_commit_hash))
        # указываем у нового коммита в качестве родителя пред предыдущий коммит, чтобы родители не учитывались при сравнении
        new_commit = Commit(new_commit.tree, prev_commit.parent_hash)
        if prev_commit_hash != new_commit.hash:
            # TODO - это не поменяет хэш коммита, так как хеш создается в конструкторе
            # new_commit.parent_hash = prev_commit_hash
            # TODO: переписать код, чтобы не создавать коммит 3 раза
            # указываем у нового коммита в качестве родителя предыдущий
            new_commit = Commit(new_commit.tree, prev_commit_hash)
            # сохраняем коммит
            os.mkdir(os.path.join(VCS_FOLDER, COMMITS_FOLDER, new_commit.hash[:4]))
            new_commit.save(os.path.join(VCS_FOLDER, COMMITS_FOLDER, new_commit.hash[:4]))
            # обновляем HEAD
            with open(head, 'w') as file:
                file.write(new_commit.hash)
        else:
            # новый коммит = предыдущий коммит
            pass


# def apply_commit(commit_hash):
#     # загружаем коммит
#     commit = load(os.path.join(VCS_FOLDER, 'commits', commit_hash[:4], commit_hash))
#


if __name__ == '__main__':
    # init()
    start = time.time()
    init()
    new_commit = commit()
    save_commit(new_commit)
    print(time.time() - start)

'''
- не сохранять информацию, совпадающую с предыдущим коммитом save_commit
хранить блобы, файлы и деревья как отдельные бинарные файлы, с названием хэша
в файле хранить хэш блоба
в дереве хранить хэши файлов и деревьев
в коммите хранить хэши дерева

- Сделать функцию для восстановления проекта из коммита
- сделать функцию для возвращения к определенному коммиту
- текстовые файлы обрабатывать отдельно при изменении - использовать модуль changes и хранить только изменения
- сделать git status для просмотра изменений относительно последнего коммита
- сделать git add
- хранить в коммите бинарные данные (чтобы не было текста)
- раздробить файл коммита на несколько маленьких ?

- создать сервер для vcs
- связать сервер с яндекс диском
- сделать git push
'''
