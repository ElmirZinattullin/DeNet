import requests

if __name__ == '__main__':
    res = requests.get("https://yandex.ru")
    print(res.text)