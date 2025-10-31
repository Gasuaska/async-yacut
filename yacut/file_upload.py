import os
import aiohttp
import aiofiles
import tempfile
import asyncio

API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
DISK_TOKEN = os.environ.get('DISK_TOKEN')
AUTH_HEADERS = {'Authorization': f'OAuth {DISK_TOKEN}'}
REQUEST_UPLOAD_URL = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_LINK_URL = f'{API_HOST}{API_VERSION}/disk/resources'
PUBLISH_URL = f'{API_HOST}{API_VERSION}/disk/resources/publish'


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
            data = await response_get.json()
            upload_url = data.get('href')
            if not upload_url:
                raise RuntimeError(
                    f'Не удалось получить URL для загрузки: {data}')

        async with aiofiles.open(temp_path, 'rb') as file:
            file_data = await file.read()
        async with session.put(upload_url, data=file_data) as response_put:
            if response_put.status not in (200, 201):
                raise RuntimeError(
                    f'Ошибка загрузки: {await response_put.text()}')

        async with session.put(
            url=PUBLISH_URL,
            headers=AUTH_HEADERS,
            params={'path': f'app:/{filename}'}:
            pass

        async with session.get(
            f'{API_HOST}{API_VERSION}/disk/resources',
            headers=AUTH_HEADERS,
            params={'path': f'app:/{filename}'}
        ) as response_info:
            data = await response_info.json()
            public_url = data.get('public_url')
            if not public_url:
                raise RuntimeError(f'Не удалось получить public_url: {data}')
    os.remove(temp_path)
    return public_url


async def upload_files(files_list):
    tasks = [upload_file(file) for file in files_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
