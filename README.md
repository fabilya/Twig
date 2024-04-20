# "Twig" - social network for everyone

## Table of content

- [Description](#description)
- [Technologies](#technologies)
- [Dev-mode](#running-a-project-in-dev-mode)
- [Authors](#authors)

### Description

<b>Twig</b> - social network for bloggers or just people, where you can create
an
account,
make posts, upload photos, describe your life moments etc.

### Technologies

- Python 3.9
- Django 2.2
- Django REST framework 3.12.4
- Mixer 7.1.2
- Pillow 9.0.1
- Requests 2.26.0
- Sorl-thumbnail 12.7.0
- Pillow 9.0.1
- Docker
- Github Actions

### Running a project in dev-mode

* Clone the repository and go to it on the command line:

```GitBash
git clone git@github.com:fabilya/twig.git
cd twig
```

* Create a virtual environment:

```Bash
python -m venv venv
```

* Activate virtual environment

<details><summary>Linux/macOS</summary>

```Bash
source venv/bin/activate
```

</details>

<details><summary>Windows</summary>

```Bash
source venv/scripts/activate
```

</details>

* Install dependencies from file requirements.txt:

```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

* Apply migrations:

```
python twig/manage.py makemigrations
python twig/manage.py migrate
```

* Create a superuser:

`python twig/manage.py createsuperuser`

* In the folder with the project, where the settings.py file is, add the .env
  file where we register our parameters:

```dotenv
SECRET_KEY='<YOUR_SECRET_KEY>'
ALLOWED_HOSTS='127.0.0.1, localhost'
DEBUG=True
```

* Start the project:

* `python twig/manage.py runserver localhost:80`

### Authors:

[Ilya Fabiyanskiy](https://github.com/fabilya)



