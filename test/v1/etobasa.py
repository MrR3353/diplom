import hashlib
import os
import pickle
from pathlib import Path
from typing import Union


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
    '''

    def __init__(self, content):
        self.content = content
        self.hash = get_sha1_hash(content)


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
                self.hash = get_sha1_hash((str(self.name) + self.blob.hash).encode('utf-8'))
        else:
            raise FileNotFoundError(f"File '{name}' does not exist.")


class Tree:
    def __init__(self, name: Path):
        self.name = name
        if os.path.exists(name) and os.path.isdir(name):
            self.children = []
            self._hash = None
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
            print('|   ' * (level - 1), '| - ' if level > 0 else '', str(node.name.name), sep='')
            if type(node) == Tree:
                for child in node.children:
                    iterate_tree(child, level + 1)

        iterate_tree(self)


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


def save(filename, obj):
        '''
        Сохраняем объект в бинарном файле
        '''
        with open(filename, 'wb') as file:
            pickle.dump(obj, file)


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
