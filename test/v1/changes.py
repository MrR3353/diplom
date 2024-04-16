import difflib


def get_difference(original_text: str, modified_text: str) -> str:
    '''
    Возвращает изменения добавленные в original_text для получения modified_text
    (Для визуализации изменений)
    '''
    differ = difflib.Differ()
    diff = differ.compare(original_text.splitlines(keepends=True), modified_text.splitlines(keepends=True))
    return ''.join(diff)


def get_changes_list(original_text: str, modified_text: str) -> list:
    matcher = difflib.SequenceMatcher(None, original_text, modified_text)
    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue
        elif tag == 'replace':
            changes.append((tag, i1, i2, j1, j2, modified_text[j1:j2]))
        elif tag == 'delete':
            changes.append((tag, i1, i2, j1, j2, original_text[i1:i2]))
        elif tag == 'insert':
            changes.append((tag, i1, i2, j1, j2, modified_text[j1:j2]))
    return changes


def get_changes_list_str(original_text: str, modified_text: str) -> list[str]:
    changes = get_changes_list(original_text, modified_text)
    changes_list = []
    for tag, i1, i2, j1, j2, text in changes:
        # Удваиваю кол-во слэшей, чтобы избавиться от символов новой строки (экранировать их)
        # print(repr(text))
        new_text = r''
        for char in text:
            if char == '\\':
                new_text += char * 2
            elif char == '\n':
                new_text += '\\n'
            else:
                new_text += char
        # print(repr(new_text))
        changes_list.append(f"{tag}: [{i1}:{i2}] -> [{j1}:{j2}] <{new_text}>\n")
        # print(f"{tag}: [{i1}:{i2}] -> [{j1}:{j2}] <{new_text}>")
    return changes_list


def save_changes_to_file(changes: list, filename: str) -> None:
    with open(filename, 'w') as file:
        for tag, i1, i2, j1, j2, text in changes:
            # Удваиваю кол-во слэшей, чтобы избавиться от символов новой строки (экранировать их)
            # print(repr(text))
            new_text = r''
            for char in text:
                if char == '\\':
                    new_text += char * 2
                elif char == '\n':
                    new_text += '\\n'
                else:
                    new_text += char
            # print(repr(new_text))
            file.write(f"{tag}: [{i1}:{i2}] -> [{j1}:{j2}] <{new_text}>\n")
            # print(f"{tag}: [{i1}:{i2}] -> [{j1}:{j2}] <{new_text}>")


def apply_changes(original_text: str, changes: list) -> str:
    '''
    Применяет изменения к тексту, возвращая модифицированный текст
    '''
    for line in changes:
        line = line[:-1]  # убираем правый >
        text = line[line.find('<') + 1: -1]  # получаем текст изменения
        text += '.'  # добавляем точку для цикла while, чтобы не получить Index out of range
        source_text = ''  # исходный текст изменения
        i = 0
        # Уменьшаю кол-во слэшей вдвое
        while i < len(text) - 1:
            if text[i] + text[i + 1] == '\\\\':
                source_text += '\\'
                i += 1
            elif text[i] + text[i + 1] == '\\n':
                source_text += '\n'
                i += 1
            else:
                source_text += text[i]
            i += 1
        # new_text = text.replace('\\\\', '\\')
        text = source_text
        line = line[:line.find('<')].split()
        command = line[0][:-1]
        i1, i2 = map(int, line[1][1:-1].split(':'))
        j1, j2 = map(int, line[3][1:-1].split(':'))

        if command == 'insert':
            original_text = original_text[:j1] + text + original_text[j1:]
        elif command == 'delete':
            original_text = original_text[:j1] + original_text[j1 + (i2 - i1):]
        elif command == 'replace':
            original_text = original_text[:j1] + text + original_text[j1 + (i2 - i1):]
    return original_text


# def apply_changes(original_text: str, changes_filename: str) -> str:
#     '''
#     Применяет изменения к тексту, возвращая модифицированный текст
#     '''
#     with open(changes_filename, 'r') as file:
#         lines = file.readlines()
#         for line in lines:
#             line = line[:-1]  # убираем правый >
#             text = line[line.find('<') + 1: -1]  # получаем текст изменения
#             text += '.'  # добавляем точку для цикла while, чтобы не получить Index out of range
#             source_text = ''  # исходный текст изменения
#             i = 0
#             # Уменьшаю кол-во слэшей вдвое
#             while i < len(text) - 1:
#                 if text[i] + text[i + 1] == '\\\\':
#                     source_text += '\\'
#                     i += 1
#                 elif text[i] + text[i + 1] == '\\n':
#                     source_text += '\n'
#                     i += 1
#                 else:
#                     source_text += text[i]
#                 i += 1
#             # new_text = text.replace('\\\\', '\\')
#             text = source_text
#             line = line[:line.find('<')].split()
#             command = line[0][:-1]
#             i1, i2 = map(int, line[1][1:-1].split(':'))
#             j1, j2 = map(int, line[3][1:-1].split(':'))
#
#             if command == 'insert':
#                 original_text = original_text[:j1] + text + original_text[j1:]
#             elif command == 'delete':
#                 original_text = original_text[:j1] + original_text[j1 + (i2 - i1):]
#             elif command == 'replace':
#                 original_text = original_text[:j1] + text + original_text[j1 + (i2 - i1):]
#         return original_text


if __name__ == '__main__':
    # Пример использования
    #     original_text = r"""a
    # b
    # c"""
    #     modified_text = r"""a\n
    # bd\\n
    # ca"
    # # insert: [4:4] -> [4:6]: d"""
    #     original_text = r"""a
    # b
    # c"""
    #     modified_text = r"""a\\n
    # b\n
    #
    # c\\\\n"""
    #     original_text = r''''''
    #     modified_text = r"""a\\n
    # b\n
    #
    # c\\\\n"""
    #     original_text = r'''A abbC'''
    #     modified_text = r'''A azC'''
    original_text = open('test6.py', encoding='utf-8').read()
    modified_text = open('test7.py', encoding='utf-8').read()
    changes = get_changes_list(original_text, modified_text)
    save_changes_to_file(changes, 'changes.txt')
    original_text = open('test7.py', encoding='utf-8').read()
    modified_text = open('test8.py', encoding='utf-8').read()
    changes1 = get_changes_list(original_text, modified_text)
    save_changes_to_file(changes1, 'changes2.txt')
    print('- ' * 25)
    original_text = open('test6.py', encoding='utf-8').read()
    original_text = apply_changes(original_text, 'changes.txt')
    original_text = apply_changes(original_text, 'changes2.txt')
    print(original_text)
