
FROM python:3.10-slim-buster as requirements-stage

#
WORKDIR /tmp


RUN pip install poetry

#
COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


#base stage
FROM python:3.10-slim-buster as base-stage

WORKDIR /code

#
COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt

#
RUN apt-get update && apt-get install -y git
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


#
FROM python:3.10-slim-buster

WORKDIR /code

COPY --from=base-stage /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=base-stage /usr/local/bin/ /usr/local/bin/

#
COPY ./app /code/app

#
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]