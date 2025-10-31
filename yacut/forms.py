from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import (
    DataRequired,
    Length,
    Optional,
    URL,
    Regexp,
    ValidationError)

from .models import URLMap

class URLMapForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=(
            DataRequired(message='Введите ссылку!'),
            URL(message='Введите корректный URL!'),
            Length(max=512),
            ),
        render_kw={'placeholder': 'Длинная ссылка'}
    )
    custom_id = StringField(
        'Ваш вариант короткой ссылки',
        validators=(Optional(),
                    Length(max=6, message='Максимум 6 символов!'),
                    Regexp('^[a-zA-Z0-9]*$',
                           message=('Для данного поля допустимо использование '
                                    'только латинских букв (верхнего и нижнего '
                                    'регистра) и цифр.')),
                    ),
        render_kw={'placeholder': 'Ваш вариант короткой ссылки'})
    
    submit = SubmitField('Создать')

    def validate_custom_id(self, field):
        if not field.data:
            return
        if URLMap.query.filter_by(short=field.data).first() is not None:
            raise ValidationError(
                'Предложенный вариант короткой ссылки уже существует.')



class FilesForm(FlaskForm):
    files = MultipleFileField()
    submit = SubmitField('Загрузить')
