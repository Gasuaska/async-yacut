import os
import re

from flask import jsonify, request

from . import app, db
from .models import URLMap
from .views import get_unique_short_id
from .error_handlers import InvalidAPIUsage

SHORT_ID_LENGTH = int(os.getenv('SHORT_ID_LENGTH', '6'))
BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:5000')


@app.route('/api/id/', methods=('POST',))
def add_url():
    if not request.is_json:
        raise InvalidAPIUsage('Отсутствует тело запроса', 400)
    data = request.get_json(silent=True)
    if not data:
        raise InvalidAPIUsage('Отсутствует тело запроса', 400)
    if 'url' not in data:
        raise InvalidAPIUsage('"url" является обязательным полем!', 400)

    custom_id = data.get('custom_id')
    if custom_id:
        if not re.fullmatch(r'[A-Za-z0-9]+', custom_id):
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки', 400
            )
        if len(custom_id) > 16:
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки', 400
            )
        if URLMap.query.filter_by(short=custom_id).first():
            raise InvalidAPIUsage(
                'Предложенный вариант короткой ссылки уже существует.', 400
            )
    else:
        custom_id = get_unique_short_id(SHORT_ID_LENGTH)
        while URLMap.query.filter_by(short=custom_id).first() is not None:
            custom_id = get_unique_short_id(SHORT_ID_LENGTH)

    url = URLMap(original=data['url'], short=custom_id)
    db.session.add(url)
    db.session.commit()

    return jsonify({
        'url': url.original,
        'short_link': f'{request.host_url}{url.short}'
    }), 201


@app.route('/api/id/<string:short_id>/', methods=('GET',))
def get_url(short_id):
    url = URLMap.query.filter_by(short=short_id).first()
    if url is not None:
        return jsonify({'url': url.original}), 200
    raise InvalidAPIUsage('Указанный id не найден', 404)
