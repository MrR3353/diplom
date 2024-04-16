import pickle
from typing import Union

import changes


class File:
    '''
    Класс для хранения данных о файле
    '''
    def __init__(self, name: str):
        self.name = name

    def read(self) -> str:
        with open(self.name, encoding='utf-8') as file:
            return file.read()

    def readlines(self) -> list[str]:
        with open(self.name, encoding='utf-8') as file:
            return file.readlines()


class FileChanges:
    '''
    Класс для хранения данных об изменении файла
    '''
    def __init__(self, changes_list: list[str], apply_to: Union[File, 'FileChanges']):
        self.changes_list = changes_list
        self.apply_to = apply_to    # к чему применять изменения
        # добавляем _1 к имени ориг файла
        if type(self.apply_to) == File:
            self.name = self.apply_to.name + '_1'
        # либо увеличиваем число в имени на 1
        elif type(self.apply_to) == FileChanges:
            name = self.apply_to.name.split('_')
            name[-1] = str(int(name[-1]) + 1)
            self.name = '_'.join(name)

    def apply(self) -> str:
        '''
        Применяем изменения, возвращается модифицированный текст
        '''
        if type(self.apply_to) == File:
            return changes.apply_changes(self.apply_to.read(), self.changes_list)
        elif type(self.apply_to) == FileChanges:
            # Если изменения ссылаются на изменения то применяем их
            text = self.apply_to.apply()
            return changes.apply_changes(text, self.changes_list)

    def save(self):
        '''
        Сохраняем объект в бинарном файле
        '''
        with open(self.name, 'wb') as file:
            pickle.dump(self, file)


def load_obj(filename):
    '''
    Загружаем объект из бинарного файла
    '''
    with open(filename, 'rb') as f:
        loaded_obj = pickle.load(f)
        return loaded_obj


if __name__ == '__main__':
    file = File('pohui.py')
    changes_list = changes.get_changes_list_str('', file.read())
    file_changes = FileChanges(changes_list, file)
    file_changes.save()

    # file = File('../test6.py')
    # file2 = File('../test7.py')
    # file3 = File('../test8.py')
    #
    # changes_list = changes.get_changes_list_str(file.read(), file2.read())
    # file_changes = FileChanges(changes_list, file)
    # file_changes.save()
    #
    # a = load_obj('../test6.py_1')
    #
    # changes_list2 = changes.get_changes_list_str(a.apply(), file3.read())
    # file_changes2 = FileChanges(changes_list2, a)
    # file_changes2.save()
    #
    # b = load_obj('../test6.py_2')
    # print(b.apply())
