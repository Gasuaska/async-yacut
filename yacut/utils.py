import os
import aiohttp
import aiofiles
import tempfile
import asyncio
from string import ascii_letters, digits
from urllib.parse import urlparse
from http import HTTPStatus

from random import choices

from . import db

API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
DISK_TOKEN = os.environ.get('DISK_TOKEN')
AUTH_HEADERS = {'Authorization': f'OAuth {DISK_TOKEN}'}
REQUEST_UPLOAD_URL = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_LINK_URL = f'{API_HOST}{API_VERSION}/disk/resources/download'
PUBLISH_URL = f'{API_HOST}{API_VERSION}/disk/resources/publish'


def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])


def save_url_map(url_map_obj):
    db.session.add(url_map_obj)
    db.session.commit()


def get_unique_short_id(str_length):
    letters_and_digits = ascii_letters + digits
    short_id = ''.join(choices(letters_and_digits, k=str_length))
    return short_id



async def upload_file(file_storage):
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=os.path.splitext(file_storage.filename)[1]
    ) as tmp_file:
        file_storage.save(tmp_file.name)
        temp_path = tmp_file.name
        filename = file_storage.filename

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=REQUEST_UPLOAD_URL,
            headers=AUTH_HEADERS,
            params={'path': f'app:/{filename}', 'overwrite': 'true'}
        ) as response_get:
            response_data = await response_get.json()
            upload_url = response_data.get('href')
            if not upload_url:
                raise RuntimeError(
                    f'Не удалось получить URL для загрузки: {response_data}'
                )

        async with aiofiles.open(temp_path, 'rb') as file:
            file_data = await file.read()
        async with session.put(upload_url, data=file_data) as response_put:
            if response_put.status not in (HTTPStatus.OK, HTTPStatus.CREATED):
                raise RuntimeError(
                    f'Ошибка загрузки: {await response_put.text()}'
                )

        async with session.get(
            url=DOWNLOAD_LINK_URL,
            headers=AUTH_HEADERS,
            params={'path': f'app:/{filename}'}
        ) as response_dl:
            data = await response_dl.json()
            public_url = data.get('href')
            if not public_url:
                raise RuntimeError(f'Не удалось получить public_url: {data}')

    os.remove(temp_path)
    return public_url


async def upload_files(files_list):
    tasks = [upload_file(file) for file in files_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
