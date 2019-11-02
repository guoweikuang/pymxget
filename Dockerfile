FROM alpine as builder

COPY Pipfile Pipfile.lock /build/

WORKDIR /build

RUN set -ex && \
    apk add --no-cache \
    gcc musl-dev python3-dev libffi-dev openssl-dev && \
    pip3 install pipenv && \
    pipenv lock --requirements > requirements.txt && \
    mkdir /install/ && \
    pip3 install --prefix /install/ -r requirements.txt gunicorn

FROM alpine as runtime

RUN set -ex && \
    apk add --no-cache \
    python3

COPY --from=builder /install/ /usr/

COPY mxget/ /app/mxget/

WORKDIR /app

CMD ["gunicorn", "mxget.server:init", "--bind", "0.0.0.0:8080", "--worker-class", "aiohttp.worker.GunicornWebWorker"]

EXPOSE 8080
