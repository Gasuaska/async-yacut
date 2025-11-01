import os
import re
from http import HTTPStatus
from urllib.parse import urlparse

from flask import jsonify, request, url_for

from . import app
from .models import URLMap
from .utils import get_unique_short_id, save_url_map, is_valid_url
from .error_handlers import InvalidAPIUsage
from .constants import SHORT_LINK_MAX_LENGTH, GENERATED_LINK_LENGTH

BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:5000')


@app.route('/api/id/', methods=('POST',))
def add_url():
    if not request.is_json:
        raise InvalidAPIUsage(
            'Отсутствует тело запроса', HTTPStatus.BAD_REQUEST)
    request_data = request.get_json(silent=True)
    if not request_data:
        raise InvalidAPIUsage(
            'Отсутствует тело запроса', HTTPStatus.BAD_REQUEST)
    if 'url' not in request_data:
        raise InvalidAPIUsage(
            '"url" является обязательным полем!', HTTPStatus.BAD_REQUEST)

    custom_id = request_data.get('custom_id')
    if not custom_id:
        custom_id = get_unique_short_id(GENERATED_LINK_LENGTH)
        while URLMap.query.filter_by(short=custom_id).first() is not None:
            custom_id = get_unique_short_id(GENERATED_LINK_LENGTH)
    else:
        if not re.fullmatch(r'[A-Za-z0-9]+', custom_id):
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки',
                HTTPStatus.BAD_REQUEST
            )
        if len(custom_id) > SHORT_LINK_MAX_LENGTH:
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки',
                HTTPStatus.BAD_REQUEST
            )
        if URLMap.query.filter_by(short=custom_id).first():
            raise InvalidAPIUsage(
                'Предложенный вариант короткой ссылки уже существует.',
                HTTPStatus.BAD_REQUEST
            )
        if not is_valid_url(request_data['url']):
            raise InvalidAPIUsage(
                'Некорректный URL', HTTPStatus.BAD_REQUEST
            )

    url = URLMap(original=request_data['url'], short=custom_id)
    save_url_map(url)

    return jsonify({
        'url': url.original,
        'short_link': url_for(
            'short_link_view', short_id=url.short, _external=True)
    }), HTTPStatus.CREATED


@app.route('/api/id/<string:short_id>/', methods=('GET',))
def get_url(short_id):
    url = URLMap.query.filter_by(short=short_id).first()
    if url is not None:
        return jsonify({'url': url.original})
    raise InvalidAPIUsage('Указанный id не найден', HTTPStatus.NOT_FOUND)
