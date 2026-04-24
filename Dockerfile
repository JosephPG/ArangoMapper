#### DEPENDENCIES

FROM python:3.14.3-slim-bookworm as dependencies
WORKDIR /app
COPY ./pyproject.toml ./config.py ./
RUN pip install poetry && poetry self add poetry-plugin-export \
    && poetry export -f requirements.txt --output requirements.txt --with dev,test


### BASE

FROM python:3.14.3-slim-bookworm as base
WORKDIR /app
COPY --from=dependencies /app/requirements.txt /app/config.py /app/pyproject.toml ./
RUN apt update && apt upgrade -y && apt install -y --no-install-recommends \
    && pip install -r requirements.txt --no-cache-dir \
    && apt-get autoremove -y && apt-get clean -y \

### TESTING

FROM base as testing
COPY ./tests ./tests
COPY ./app/ app/
CMD ["bash"]