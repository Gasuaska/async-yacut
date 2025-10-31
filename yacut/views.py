import os
from random import choices
from string import ascii_letters, digits

from flask import flash, redirect, request, render_template

from . import app, db
from .forms import URLMapForm, FilesForm
from .models import URLMap
from .file_upload import upload_files

BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:5000')
SHORT_ID_LENGTH = int(os.getenv('SHORT_ID_LENGTH', '6'))

def get_unique_short_id(str_length):
    letters_and_digits = ascii_letters + digits
    short_id = ''.join(choices(letters_and_digits, k=str_length))
    return short_id


@app.route('/', methods=('GET', 'POST'))
def index_view():
    form = URLMapForm()
    if not form.validate_on_submit():
        return render_template('index.html', form=form)
    if form.custom_id.data:
        if 'files' in form.custom_id.data:
            flash('Предложенный вариант короткой ссылки уже существует.')
            return render_template('index.html', form=form)
        short_id = form.custom_id.data
    else:
        short_id = get_unique_short_id(SHORT_ID_LENGTH)
        while URLMap.query.filter_by(short=short_id).first() is not None:
            short_id = get_unique_short_id(SHORT_ID_LENGTH)

    urls = URLMap(
        original=form.original_link.data,
        short=short_id,
    )
    db.session.add(urls)
    db.session.commit()
    short_link = f'{request.host_url.rstrip("/")}/{short_id}'
    return render_template('index.html',
                           form=form,
                           short_link=short_link,)


@app.route('/files', methods=('GET', 'POST'))
async def files_view():
    form = FilesForm()
    if not form.validate_on_submit():
        return render_template('files.html', form=form)
    if not form.files.data:
        return render_template('files.html', form=form)
    uploaded_urls = await upload_files(form.files.data)
    files_info = []
    for i, file_storage in enumerate(form.files.data):
        short_id = get_unique_short_id(SHORT_ID_LENGTH)
        while URLMap.query.filter_by(short=short_id).first() is not None:
            short_id = get_unique_short_id(SHORT_ID_LENGTH)

        urls = URLMap(
            original=uploaded_urls[i],
            short=short_id
        )
        db.session.add(urls)

        files_info.append({
            'filename': file_storage.filename,
            'short_link': f'{request.host_url.rstrip("/")}/{short_id}'

        })

    db.session.commit()
    return render_template('files.html', form=form, files_info=files_info)


@app.route('/files/<string:short_id>', methods=('GET',))
def file_view(short_id):
    url = URLMap.query.filter_by(short=short_id).first_or_404()
    return redirect(url.original)


@app.route('/<string:short_id>', methods=('GET',))
def short_link_view(short_id):
    url = URLMap.query.filter_by(short=short_id).first_or_404()
    return redirect(url.original)
