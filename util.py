import requests
from bs4 import BeautifulSoup
import os
import re
import json


def clean_txt(txt):
    txt = re.sub(r'\u200b', r'', txt)
    txt = re.sub(r'[\s]+', ' ', txt)
    return txt.strip()


def get_vinted_items_from_url(url):
    response = requests.get(url)

    soup = BeautifulSoup(response.text, features="html.parser")
    items = soup.findAll("div", {"class": "is-visible item-box__container"})
    items = items[::-1]  # revert order to show oldest first
    for item in items:
        yield VintedItem.load_from_item_box__container(item)


def get_lbc_items_from_url(url):
    session = requests.session()
    headers = {
        # 'User-Agent': '*',
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36 OPR/64.0.3417.47",
        "Accept-Language": "fr-FR,en;q=0.5",
    }
    session.headers.update(headers)

    r = session.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    items = soup.find_all("li", {"class": "_3DFQ-"})
    for item in items:
        yield LBCItem.load_from_page(item)


class LBCItem:
    def __init__(self, price, name, url):
        self.price = price
        self.name = name
        self.url = url

    @classmethod
    def load_from_page(cls, item):
        name = clean_txt(item.find_all("span", {"itemprop": "name"})[0].text)
        try:
            price = clean_txt(item.find_all("span", {"itemprop": "priceCurrency"})[0].text)
        except:
            price = None
        url = 'https://www.leboncoin.fr' + item.find_all("a", {"class": "clearfix trackable"})[0].attrs['href']

        return cls(
            price=price, name=name, url=url
        )

    def to_html(self):
        html = ''
        for key, val in self.__dict__.items():
            if val is not None:
                if val.startswith('http'):
                    html += f'<a href="{val}">link</a>' + '\n'
                else:
                    html += val + '\n'
        return html


class AppConfig:
    def __init__(self, telegram_token, telegram_chat_id, vinted_urls=None, lbc_urls=None):
        if vinted_urls is None:
            vinted_urls = list()
        if lbc_urls is None:
            lbc_urls = list()
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.vinted_urls = vinted_urls
        self.lbc_urls = lbc_urls

    @classmethod
    def load_from_disk(cls, path):
        with open(path, 'r') as file:
            config = json.load(file)
        return cls(
            telegram_token=config.get("telegram_token"),
            telegram_chat_id=config.get("telegram_chat_id"),
            vinted_urls=config.get("vinted_urls"),
            lbc_urls=config.get("lbc_urls")
        )


class VintedItem:
    def __init__(self, price, size, url, desc=None, brand=None):
        self.brand = brand
        self.price = price
        self.size = size
        self.url = url
        self.desc = desc

    @classmethod
    def load_from_item_box__container(cls, item):
        try:
            brand = item.findAll('a', {"class": "item-box__brand"})[0].text
        except:
            brand = None
        item_box_details = item.findAll("div", {"class": "item-box__details"})[0]
        price = item_box_details.findAll("div", {"class": "item-box__title"})[0].text.strip()
        size = item_box_details.findAll("div", {"class": "item-box__subtitle"})[0].text.strip()
        url = f'https://www.vinted.fr{item.findAll("a", {"class": "media__image-wrapper js-item-link"})[0].attrs["href"]}'
        # desc = clean_txt(item.findAll("div", {"class": "media-caption__body"})[0].text)
        return cls(brand=brand, price=price, size=size, url=url)

    def to_html(self):
        html = ''
        for key, val in self.__dict__.items():
            if val is not None:
                if val.startswith('http'):
                    html += f'<a href="{val}">link</a>' + '\n'
                else:
                    html += val + '\n'
        return html


class CacheHandler:
    def __init__(self, path=os.path.join(os.environ["HOME"], '.cache', 'shga.cache')):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        if os.path.exists(path):
            with open(path, 'r') as file:
                self.items = [str(line.strip()) for line in file.readlines()]
        else:
            self.items = list()

    def save(self):
        with open(self.path, 'w') as file:
            for item in self.items:
                file.write(item + '\n')

    def add(self, item):
        self.items.append(str(item))

    def __contains__(self, item):
        return item in self.items
