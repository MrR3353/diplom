import hashlib
import os
import pickle
from pathlib import Path
from typing import Union

from config import DATA_FOLDER

'''
Классы описывающие объекты файловой системы
'''


def get_sha1_hash(data: bytes) -> str:
    # Создаем объект хэша SHA-1
    sha1_hash = hashlib.sha1()
    # Обновляем объект хэша с данными
    sha1_hash.update(data)
    # Получаем вычисленный хэш в шестнадцатеричном формате
    hex_digest = sha1_hash.hexdigest()
    return hex_digest


class Blob:
    '''
    Класс для хранения двоичных данных файлов
    Блобов может быть меньше чем файлов, если в проекте есть файлы с одинаковым содержимым
    В этом случае их хэш будет одинаков, и файл блоба будет общий
    '''

    def __init__(self, content):
        self.content = content
        self.hash = get_sha1_hash(content)

    def save(self, path):
        '''
        Сохраняем объект в бинарном файле
        '''

        if self.hash in os.listdir(DATA_FOLDER):
            # такой объект уже есть в предыдущих коммитах, не сохраняем
            return

        # сохраняем объект
        with open(os.path.join(path, self.hash), 'wb') as file:
            pickle.dump(self, file)


class File:
    '''
    Класс для хранения данных о файле
    '''

    def __init__(self, name: Path):
        self.name = name
        if os.path.exists(name) and os.path.isfile(name):
            with open(self.name, mode='rb') as file:
                file_content = file.read()
            self.blob = Blob(file_content)
            self.name = self.name.name
            self.hash = get_sha1_hash((str(self.name) + self.blob.hash).encode('utf-8'))
        else:
            raise FileNotFoundError(f"File '{name}' does not exist.")

    def save(self, path):
        '''
        Сохраняем файл в бинарном файле, заменяя блоб его хэшем
        Блоб сохраняем как отдельный файл
        '''

        if self.hash in os.listdir(DATA_FOLDER):
            # такой объект уже есть в предыдущих коммитах, не сохраняем
            return

        # сохраняем объект
        self.blob.save(path)
        self.blob = self.blob.hash
        with open(os.path.join(path, self.hash), 'wb') as file:
            pickle.dump(self, file)

    def load(self):
        '''
        Загружаем блоб из файловой системы
        :return:
        '''
        blob_path = os.path.join(DATA_FOLDER, self.blob)
        if not os.path.exists(blob_path):
            raise Exception(f'Нет такого элемента {self.blob}')
        self.blob = load(blob_path)


class Tree:
    def __init__(self, name: Path):
        self.name = name
        if os.path.exists(name) and os.path.isdir(name):
            self.children = []
            self._hash = None
            self.name = self.name.name
        else:
            raise FileNotFoundError(f"Directory '{name}' does not exist.")

    def add_child(self, child: Union[File, 'Tree']):
        self.children.append(child)

    @property
    def hash(self):
        data = str(self.name)
        for child in self.children:
            data += child.hash
        return get_sha1_hash(data.encode('utf-8'))

    def print_tree(self):
        def iterate_tree(node, level=0):
            print('|   ' * (level - 1), '| - ' if level > 0 else '', str(node.name), sep='')
            if type(node) == Tree:
                for child in node.children:
                    iterate_tree(child, level + 1)

        iterate_tree(self)

    def get_filenames(self, node=None, level=0, prev_path=''):
        if node is None:
            node = self
        if isinstance(node, Tree):
            prev_path = os.path.join(prev_path, node.name)
            for child in node.children:
                yield from self.get_filenames(child, level + 1, prev_path)
        elif isinstance(node, File):
            yield os.path.join(prev_path, node.name)

    def save(self, path):
        '''
        Сохраняем дерево в бинарном файле, элементы дерева заменяем хэшами
        и сохраняем как отдельные файлы.
        Сохраняем только если такого хэша еще не было в пред коммитах

        :param path: путь к папке куда сохранять
        :return:
        '''
        hash = self.hash  # хэш меняется после изменения self.children

        if hash in os.listdir(DATA_FOLDER):
            # такой объект уже есть в предыдущих коммитах, не сохраняем
            return

        # сохраняем дерево
        for i in range(len(self.children)):
            child_hash = self.children[i].hash
            self.children[i].save(path)
            self.children[i] = child_hash
        with open(os.path.join(path, hash), 'wb') as file:
            pickle.dump(self, file)

    def load(self):
        '''
        Загружаем компоненты дерева из файловой системы (деревья, файлы и тд)
        :return:
        '''
        for i in range(len(self.children)):
            child_path = os.path.join(DATA_FOLDER, self.children[i])
            if not os.path.exists(child_path):
                raise Exception(f'Нет такого элемента {self.children[i]}')
            self.children[i] = load(child_path)
            self.children[i].load()


class Commit:
    def __init__(self, tree: Tree, parent_hash: str = None):
        self.tree = tree
        self.parent_hash = parent_hash
        if self.parent_hash is None:
            self.hash = get_sha1_hash(self.tree.hash.encode('utf-8'))
        else:
            self.hash = get_sha1_hash((self.tree.hash + self.parent_hash).encode('utf-8'))
        # self.author
        # self.message
        # self.time

    def save(self, path):
        '''
        Сохраняем объект в бинарном файле, заменяем дерево хэшем,
        дерево сохраняем отдельным файлом
        '''
        tree_hash = self.tree.hash
        self.tree.save(path)
        self.tree = tree_hash
        with open(os.path.join(path, self.hash), 'wb') as file:
            pickle.dump(self, file)

    def load(self):
        '''
        Загружаем компоненты коммита из файловой системы (деревья, файлы и тд)
        :return:
        '''
        # Ищем дерево
        tree_path = os.path.join(DATA_FOLDER, self.tree)
        if not os.path.exists(tree_path):
            raise Exception(f'Нет такого дерева {self.tree}')

        self.tree = load(tree_path)
        self.tree.load()


def load(filename):
    '''
    Загружаем объект из бинарного файла
    '''
    with open(filename, 'rb') as f:
        loaded_obj = pickle.load(f)
        return loaded_obj


if __name__ == '__main__':
    tree = Tree('test')
    print(tree.hash)
    file = File('test6.py')
    print(file.hash)
    tree.add_child(file)
    print(tree.hash)
    tree.add_child(file)
    print(tree.hash)
