import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
from pathlib import Path

from cryptography.fernet import Fernet

from config import BASE_PATH, VCS_FOLDER


def generate_key():
    # Генерируем случайный ключ
    key = Fernet.generate_key()
    with open(os.path.join(VCS_FOLDER, 'key'), "wb") as key_file:
        key_file.write(key)
    return key


def load_key():
    # Загружаем ключ из файла
    return open(os.path.join(VCS_FOLDER, 'key'), "rb").read()


def encrypt_file(path, key):
    fernet = Fernet(key)

    with open(path, "rb") as file:
        file_data = file.read()
    os.remove(path)

    # Шифруем содержимое файла
    encrypted_data = fernet.encrypt(file_data)
    # Шифруем имя файла
    encrypted_filename = encrypt_message(path.name, key[:16])

    with open(os.path.join(path.parent, encrypted_filename), "wb") as file:
        file.write(encrypted_data)


def decrypt_file(path, key):
    fernet = Fernet(key)

    with open(path, "rb") as file:
        encrypted_data = file.read()
    os.remove(path)

    # Расшифровываем данные
    decrypted_data = fernet.decrypt(encrypted_data)
    decrypted_filename = decrypt_message(path.name, key[:16])

    with open(os.path.join(path.parent, decrypted_filename), "wb") as file:
        file.write(decrypted_data)


def encrypt_message(message, key):
    # Генерируем случайный вектор инициализации
    iv = os.urandom(16)  # 128 бит = 16 байт

    # Создаем шифратор с использованием ключа и вектора инициализации
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Шифруем сообщение
    ciphertext = encryptor.update(message.encode()) + encryptor.finalize()

    encrypted_message = iv + ciphertext
    return base64.urlsafe_b64encode(encrypted_message).decode()


def decrypt_message(ciphertext, key):
    ciphertext = base64.urlsafe_b64decode(ciphertext)

    # Извлекаем вектор инициализации из шифротекста
    iv = ciphertext[:16]  # 128 бит = 16 байт

    # Создаем дешифратор с использованием ключа и вектора инициализации
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    # Дешифруем сообщение
    decrypted_message = decryptor.update(ciphertext[16:]) + decryptor.finalize()

    return decrypted_message.decode()


def encrypt_folder(key, encrypt: bool, path=BASE_PATH, print_content=True):
    stack = [(path, 0)]  # путь к файлу и уровень вложенности

    while stack:
        current_path, tab = stack.pop()  # берем файл и его уровень вложенности

        if print_content:
            print('|   ' * (tab - 1), '+ - ' if tab > 0 else '', current_path.name, sep='')

        if current_path.is_dir():
            if current_path == VCS_FOLDER:  # skip vcs folder
                continue

            if current_path != path:   # корневую папку не шифруем
                old_current_path = current_path
                if encrypt:
                    # шифруем имя файла. для шифра нужен ключ 16 байт или другая степень 2ки
                    new_folder_name = encrypt_message(current_path.name, key[:16])
                else:
                    new_folder_name = decrypt_message(current_path.name, key[:16])
                current_path = Path(os.path.join(current_path.parent, new_folder_name))
                os.rename(old_current_path, current_path)
            subfolders = reversed(list(current_path.iterdir()))
            for obj in subfolders:
                stack.append((obj, tab + 1))
        else:
            pass
            if encrypt:
                encrypt_file(current_path, key)
            else:
                decrypt_file(current_path, key)


if __name__ == '__main__':

    # key = generate_key()
    key = load_key()
    print(key)

    # encrypt_folder(key, encrypt=True, path=Path('lol/2'))
    encrypt_folder(key, encrypt=False, path=Path('lol/sLtHsRHbMwd7tDDq_eEKdxM='))