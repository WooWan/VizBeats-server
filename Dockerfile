FROM python:3.10-slim-buster as base


FROM base as requirements

#
WORKDIR /tmp


RUN pip install poetry

#
COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --without dev


#base stage
FROM base as deps

WORKDIR /code

#
COPY --from=requirements /tmp/requirements.txt /code/requirements.txt

#
RUN apt-get update && apt-get install -y git \
    && pip install --no-cache-dir --upgrade -r /code/requirements.txt \
    &&  rm -rf /var/lib/apt/lists/*

#
FROM base as runner

WORKDIR /code

RUN apt-get update && apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=deps /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=deps /usr/local/bin /usr/local/bin

#
COPY ./app /code/app

#
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]