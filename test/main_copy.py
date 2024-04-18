import os
import shutil
import time
from pathlib import Path
from gitignore_parser import parse_gitignore
import fs_objects

VCS_FOLDER = '.vcs'
GITIGNORE = '.gitignore'
BASE_PATH = os.getcwd()


def init():
    # git init
    os.mkdir('vcs')


def add():
    # git add
    print(os.listdir(os.getcwd()))

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

    def is_obj_in_gitignore(obj, obj_tab, gitignore_stack):
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

    def iter_folder(path, gitignore=True, tracking_changes=True, copy=False):
        '''
        Проходится по файловой системе и выполняет печать или копирование
        :param path: путь к папке
        :param gitignore: нужно ли игнорировать файлы
        :param copy: нужно ли копировать файлы
        :return:
        '''
        stack = [(Path(path), 0)]  # путь к файлу и уровеь вложенности
        prev_tab = 0  # предыдущий уровень вложенности
        gitingore_stack = []  # файлы gitingore и их уровень вложенности

        while stack:
            current_path, tab = stack.pop()

            if gitignore:
                # удаляем файл из стека, когда перебрали все файлы в области этого .gitignore
                if tab < prev_tab and len(gitingore_stack) > 0:
                    gitingore_stack.pop()
                gitignore_path = Path.joinpath(current_path.parent_hash, GITIGNORE)
                if gitignore_path.exists() and (gitignore_path, tab) not in gitingore_stack:
                    gitingore_stack.append((gitignore_path, tab))

            if not is_obj_in_gitignore(current_path, tab, gitingore_stack):
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
                # if tracking_changes:
                #     relative_path = current_path.relative_to(BASE_PATH)
                #     if current_path.name != Path(BASE_PATH).name:  # папку проекта игнорируем
                #         if not current_path.is_dir():
                #             hui.Blob(current_path.name)
                #         else:
                #             hui.Tree(current_path.name)


                if current_path.is_dir():
                    subfolders = reversed(list(current_path.iterdir()))
                    for obj in subfolders:
                        stack.append((obj, tab + 1))
            prev_tab = tab

    iter_folder(BASE_PATH)
    # iter_folder(os.path.join(BASE_PATH, 'test'))


if __name__ == '__main__':
    start = time.time()
    add()
    print(time.time() - start)
