import os

from flask import flash, redirect, render_template, url_for

from . import app, db
from .forms import URLMapForm, FilesForm
from .models import URLMap
from .constants import GENERATED_LINK_LENGTH
from .utils import upload_files, get_unique_short_id, save_url_map

BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:5000')


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
        short_id = get_unique_short_id(GENERATED_LINK_LENGTH)
        while URLMap.query.filter_by(short=short_id).first() is not None:
            short_id = get_unique_short_id(GENERATED_LINK_LENGTH)

    urls = URLMap(
        original=form.original_link.data,
        short=short_id,
    )
    save_url_map(urls)
    short_link = url_for(
        'short_link_view', short_id=urls.short, _external=True)
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
    for file_index, file_storage in enumerate(form.files.data):
        short_id = get_unique_short_id(GENERATED_LINK_LENGTH)
        while URLMap.query.filter_by(short=short_id).first() is not None:
            short_id = get_unique_short_id(GENERATED_LINK_LENGTH)

        urls = URLMap(
            original=uploaded_urls[file_index],
            short=short_id
        )
        db.session.add(urls)

        files_info.append({
            'filename': file_storage.filename,
            'short_link': url_for(
                'file_view', short_id=urls.short, _external=True)

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
