import copy
import os
import shutil
import time
from pathlib import Path
from gitignore_parser import parse_gitignore

from fs_objects import File, Tree, Commit, load
from config import VCS_FOLDER, BASE_PATH, GITIGNORE, DATA_FOLDER, HEAD_PATH


def init():
    '''
    Инициализирует репозиторий, создает необходимые папки
    Аналог git init
    '''
    os.makedirs(VCS_FOLDER, exist_ok=True)
    os.makedirs(DATA_FOLDER, exist_ok=True)


def make_commit(path=BASE_PATH, gitignore=True, print_content=True):
    '''
    Создает новый коммит.
    Аналог git commit
    :param path: путь к проекту
    :param gitignore: игнорировать ли файлы из .gitignore?
    :param print_content: выводить ли дерево проекта?
    :return: новый коммит
    '''
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
        Проверяет находится ли obj в .gitignore
        :param obj: Путь к объекту файловой системы
        :param obj_tab: уровень вложенности объекта
        :param gitignore_stack: список файлов gitignore и их уровней вложенности
        :return:
        '''
        if obj.name == VCS_FOLDER.name:
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
        :return: возвращает дерево проекта
        '''
        stack = [(path, 0)]  # путь к файлу и уровень вложенности
        gitingore_stack = []  # файлы gitingore и их уровень вложенности
        if path == os.getcwd():  # добавляем переход наверх для дерева проекта
            path = Path(os.path.join('..', stack[0][0].name))

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
                    print('|   ' * (tab - 1), '+ - ' if tab > 0 else '', current_path.name, sep='')

                if copy:
                    # Получаем относительный путь от базового пути
                    relative_path = current_path.relative_to(BASE_PATH)
                    new_path = os.path.join(VCS_FOLDER, str(relative_path))
                    # папку проекта игнорируем и пропускаем файлы которые уже есть
                    if current_path.name != BASE_PATH.name and not os.path.exists(new_path):
                        if not current_path.is_dir():
                            shutil.copy2(current_path, new_path)
                        else:
                            os.mkdir(new_path)

                # создаем дерево проекта
                # relative_path = current_path.relative_to(BASE_PATH)
                if current_path.name != Path(path).name:  # корневую папку игнорируем
                    if not current_path.is_dir():
                        file = File(current_path)
                        # file = File(relative_path)
                        tree_stack[-1][0].add_child(file)  # добавляем файл в дерево
                    else:
                        tree = Tree(current_path)
                        # tree = Tree(relative_path)
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
    '''
    Сохраняет коммит и обновляет HEAD
    '''
    head = Path(os.path.join(VCS_FOLDER, 'HEAD'))
    if not head.exists():  # создаем HEAD, записываем туда хэш коммита
        with open(head, 'w') as file:
            file.write(new_commit.hash)
        # сохраняем коммит
        new_commit.save(DATA_FOLDER)
        print(f'Сохранен коммит {new_commit.hash}')
    else:
        with open(head, 'r') as file:
            prev_commit_hash = file.read()
        # загружаем предыдущий коммит
        prev_commit = load(os.path.join(DATA_FOLDER, prev_commit_hash))
        # указываем у нового коммита в качестве родителя пред предыдущий коммит, чтобы родители не учитывались при сравнении
        new_commit = Commit(new_commit.tree, prev_commit.parent_hash)
        if prev_commit_hash != new_commit.hash:
            # TODO - это не поменяет хэш коммита, так как хеш создается в конструкторе
            # new_commit.parent_hash = prev_commit_hash
            # TODO: переписать код, чтобы не создавать коммит 3 раза
            # указываем у нового коммита в качестве родителя предыдущий
            new_commit = Commit(new_commit.tree, prev_commit_hash)
            # сохраняем коммит
            new_commit.save(DATA_FOLDER)
            print(f'Сохранен коммит {new_commit.hash}')
            # обновляем HEAD
            with open(head, 'w') as file:
                file.write(new_commit.hash)
        else:
            # новый коммит = предыдущий коммит
            print(f'Коммит не создан. Нет изменений')
            pass


def load_commit(commit_hash):
    '''
    Загружаем коммит из файлов
    '''
    path = os.path.join(DATA_FOLDER, commit_hash)
    if not os.path.exists(path):
        raise Exception(f'Нет коммита {commit_hash}')
    commit = load(path)
    commit.load()
    return commit


def restore_commit(commit_hash, path=BASE_PATH):
    '''
    Восстанавливает файлы из коммита
    :param path: куда восстановить коммит
    '''
    # переходим на уровень вверх если корневая папка (иначе имя проекта будет дублироваться)
    if path == BASE_PATH:
        path = path.parent
    # удаляем все файлы которых в коммите не было, и те которые были изменены
    changes_list = status(path, new_commit_hash=commit_hash)
    for change in changes_list:
        if change[0] in '-?':
            p = os.path.join(path, change[1])
            try:
                if os.path.isfile(p):
                    os.remove(p)
                elif os.path.isdir(p):
                    shutil.rmtree(p)
                else:
                    print('Не найдено для удаления:', p)
            except FileNotFoundError as e:
                print(e)
    for change in changes_list:
        print(*change)

    commit = load_commit(commit_hash)
    try:
        os.mkdir(os.path.join(path, commit.tree.name))
    except FileExistsError as e:
        pass
    # добавляем папку проекта к пути
    tree_stack = [commit.tree.name]

    # проходимся по дереву коммита и восстанавливаем файлы и папки
    def walk_tree(tree, tree_stack):
        for child in tree.children:
            if isinstance(child, File):
                with open(os.path.join(path, *tree_stack, child.name), 'wb') as f:
                    f.write(child.blob.content)
            elif isinstance(child, Tree):
                try:
                    os.mkdir(os.path.join(path, *tree_stack, child.name))
                except FileExistsError as e:
                    pass
                tree_stack.append(child.name)
                walk_tree(child, tree_stack)
                tree_stack.pop()

    walk_tree(commit.tree, tree_stack)

    # обновляем хэш коммита в HEAD
    with open(HEAD_PATH, 'w') as file:
        file.write(commit_hash)


def commit_history(briefly=True):
    '''
    История коммитов
    :param briefly: в кратком виде?
    TODO: выводит только коммиты предыдущие для текущего (теряются другие коммиты после отката пред. коммита назад)
    '''
    if not HEAD_PATH.exists():
        print('История коммитов пуста')
    else:
        commits = []
        # добавляем последний коммит
        with open(HEAD_PATH, 'r') as file:
            last_commit_hash = file.read()
        commit = load(os.path.join(DATA_FOLDER, last_commit_hash))
        commits.append(commit.hash)

        # проходимся по всем предыдущим коммитам
        while commit.parent_hash is not None:
            commit = load(os.path.join(DATA_FOLDER, commit.parent_hash))
            commits.append(commit.hash)

        # берем в убыв порядке и оставляем только 4 символа хэша
        commits.reverse()
        if briefly:
            commits = [commit[:6] for commit in commits]
        print('История коммитов:', *commits, sep='\n')


def status(path=BASE_PATH, old_commit_hash=None, new_commit_hash=None):
    '''
    Возвращает список кортежей изменений между old_commit_hash и new_commit_hash.
    ('+', <filename>)  добавление файла
    ('-', <filename>) удаление файла
    ('?', <filename>) изменение файла
    ('?', <filename>, '>', > <new_filename>) переименование файла
    :param path: путь по которому проверяется статус
    :param old_commit_hash: из какого коммита нужно сделать new_commit_hash
    :param new_commit_hash: коммит в который должны перейти
    '''
    changes_list = []

    if new_commit_hash is None:    # создаем новый коммит
        new_commit = make_commit(path, print_content=False)
    else:
        new_commit = load(os.path.join(DATA_FOLDER, new_commit_hash))
        new_commit.load()

    if old_commit_hash is None:    # берем последний коммит
        if not VCS_FOLDER.exists():
            print('Репозиторий еще не создан')
            return changes_list
        elif not HEAD_PATH.exists():
            print('Коммитов еще не было')
            return changes_list
        else:
            with open(HEAD_PATH, 'r') as file:
                last_commit_hash = file.read()
            prev_commit = load(os.path.join(DATA_FOLDER, last_commit_hash))
            prev_commit.load()
    else:
        # prev_commit = make_commit(path, print_content=False)
        prev_commit = load(os.path.join(DATA_FOLDER, old_commit_hash))
        prev_commit.load()

    # сравниваем prev_commit и new_commit
    # делаю у коммитов одинаковых родителей, чтобы если нет изменений, совпадали хэши
    new_commit = Commit(new_commit.tree, prev_commit.parent_hash)
    if new_commit.hash == prev_commit.hash:
        print('Изменений нет')
        return changes_list
    else:
        # дерево проекта отличается
        prev_tree = prev_commit.tree
        new_tree = new_commit.tree
        prev_child_hash = ''.join([child.hash for child in prev_tree.children])
        new_child_hash = ''.join([child.hash for child in new_tree.children])
        if prev_child_hash == new_child_hash:
            changes_list.append(('?', prev_tree.name, '>', new_tree.name))
        else:
            if prev_tree.name != new_tree.name:
                changes_list.append(('?', prev_tree.name, '>', new_tree.name))

            def walk_tree(new_tree, prev_tree, find_deleted=False):
                for new_child in new_tree.children:
                    if type(new_child) == Tree:
                        new_child_hash = ''.join([child.hash for child in new_child.children])
                    else:
                        new_child_hash = new_child.blob.hash

                    found = content_changed = False
                    for prev_child in prev_tree.children:
                        if new_child.name == prev_child.name:
                            if new_child.hash == prev_child.hash:
                                found = True
                                content_changed = False
                                # удаляем найденный объект, чтобы он не использовался при поиске
                                prev_tree.children.remove(prev_child)
                            else:
                                found = True
                                content_changed = True
                            break
                        else:
                            if type(prev_child) == Tree:
                                prev_child_hash = ''.join([child.hash for child in prev_child.children])
                            else:
                                prev_child_hash = prev_child.blob.hash

                            if new_child_hash == prev_child_hash:
                                if not find_deleted:
                                    changes_list.append(('?', os.path.join(*tree_stack, prev_child.name), '>', os.path.join(*tree_stack, new_child.name)))
                                found = True
                                content_changed = False
                                prev_tree.children.remove(prev_child)
                                break

                    # предыдущая версия была найдена
                    if found and content_changed:
                        # папка изменилась
                        if type(new_child) == Tree:
                            tree_stack.append(new_child.name)
                            walk_tree(new_child, prev_child, find_deleted)
                            tree_stack.pop()
                            prev_tree.children.remove(prev_child)
                        # файл изменился
                        else:
                            if not find_deleted:
                                changes_list.append(('?', os.path.join(*tree_stack, new_child.name)))
                            prev_tree.children.remove(prev_child)
                    elif not found:
                        if not find_deleted:
                            if type(new_child) == Tree:
                                changes_list.append(('+', os.path.join(*tree_stack, new_child.name)))
                            else:
                                changes_list.append(('+', os.path.join(*tree_stack, new_child.name)))
                        else:
                            if type(new_child) == Tree:
                                changes_list.append(('-', os.path.join(*tree_stack, new_child.name)))
                            else:
                                changes_list.append(('-', os.path.join(*tree_stack, new_child.name)))

            tree_stack = [new_tree.name]
            prev_tree_copy = copy.deepcopy(prev_tree)
            walk_tree(new_tree, prev_tree_copy)
            walk_tree(prev_tree, new_tree, find_deleted=True)
            # TODO: объект перемещен. Также если объкт переименован и немного изменен, будет создаваться новый файл
            #  и удаляться старый, хотя по сути это переименование
            return changes_list


def remove_repo():
    shutil.rmtree(VCS_FOLDER)


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
