## Use an ARM64-compatible Python image
#FROM arm64v8/python:3.9-slim-buster as builder
#
## Set the working directory
#WORKDIR /code
#
## Install Poetry
#RUN pip install poetry
#
## Copy only the dependency definition files and install dependencies
#COPY ./pyproject.toml ./poetry.lock /code/
#
## Export requirements.txt from Poetry
#RUN poetry export -f requirements.txt --output requirements.txt --without-hashes
#
## Use a fresh image for the final build
#FROM arm64v8/python:3.9-slim-buster
#
## Set the working directory
#WORKDIR /code
#
## Copy the requirements.txt from the builder image
#COPY --from=builder /code/requirements.txt /code/requirements.txt
#
## Install dependencies using requirements.txt
#RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
#
## Copy the rest of the project
#COPY ./app /code/app
#
## Run the application
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
#
FROM python:3.10-slim-buster as requirements-stage

#
WORKDIR /tmp

RUN pip install poetry

#
COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


#final stage
FROM python:3.10-slim-buster

WORKDIR /code
#
COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

#
COPY ./app /code/app

#
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]