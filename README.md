# Foodganizer

## How to setup project

### Clone the repo
```bash
git clone https://github.com/Ichicoro/Foodganizer
```

### Install dependencies

### TL;DR
```bash
# Install python 3.9 or greater

# Install Poetry
pip install poetry

# Install the dependencies
poetry install

# Apply migrations
poetry run python manage.py migrate
```

#### Explanation
This project uses [Python](https://www.python.org/) >=3.9.

You also need to install Poetry by running `pip install poetry`.

You'll then need to install the project's dependencies by running `poetry install`.

It's important to run `poetry run python manage.py migrate`

### Run the project
```bash
poetry run python manage.py runserver 0.0.0.0:8000
```

You'll be able to access the project at [`http://localhost:8000`](http://localhost:8000).

### Run the tests

To run the tests, run `poetry run python manage.py test website`.
