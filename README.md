# osu!acc

osu!acc is a web application for the rhythm game [osu!](https://osu.ppy.sh/home). It aims to provide a more in-depth and comprehensive analysis of how accurate a player is.

## Dependencies

To install the dependencies used in this project,

```
pip install -r requirements.txt
```

## Secret settings

Sensitive fields are to be isolated in a separate file, `settings_secret.py`. Create your own by copying from `secret_settings.py.template` and filling in your own values. A secret key generator for Django can be found [here](https://www.miniwebtool.com/django-secret-key-generator/).

## Hosting locally

To host this project locally, run

```
python manage.py runserver
```

and go to `localhost:8000` in your web browser.
