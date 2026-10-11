# multi stage to build tube archivist
# build python wheel, download and extract ffmpeg, copy into final image

FROM node:24.14.1-alpine AS npm-builder
COPY frontend/package.json frontend/package-lock.json /
RUN npm i

FROM node:24.14.1-alpine AS node-builder

# RUN npm config set registry https://registry.npmjs.org/

COPY --from=npm-builder ./node_modules /frontend/node_modules
COPY ./frontend /frontend
WORKDIR /frontend

RUN npm run build:deploy

WORKDIR /

# First stage to build python wheel
FROM python:3.14.7-slim-trixie AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        git \
        libldap2-dev \
        libsasl2-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# install requirements
COPY ./backend/requirements.txt /requirements.txt
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN python -m venv "$VIRTUAL_ENV" \
    && pip install --no-cache-dir -r /requirements.txt

# build ffmpeg
FROM python:3.14.7-slim-trixie AS ffmpeg-builder

ARG TARGETPLATFORM

COPY docker_assets/ffmpeg_download.py ffmpeg_download.py
RUN python ffmpeg_download.py $TARGETPLATFORM

# build final image
FROM python:3.14.7-slim-trixie AS tubearchivist

ENV PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    HOME=/tmp

COPY --from=denoland/deno:bin /deno /usr/local/bin/deno

# copy build requirements
COPY --from=builder /opt/venv /opt/venv

# copy ffmpeg
COPY --from=ffmpeg-builder \
    ./ffmpeg/ffmpeg \
    ./ffprobe/ffprobe \
    /usr/bin/

# install distro packages needed
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        atomicparsley \
        tini \
        curl \
    && mkdir -p /cache /youtube \
    && rm -rf /var/lib/apt/lists/*

# copy application into container
COPY ./backend /app
COPY --chmod=755 \
    ./docker_assets/run.sh \
    ./docker_assets/backend_start.py \
    ./docker_assets/beat_auto_spawn.sh \
    /app/

COPY --from=node-builder ./frontend/dist /app/static

RUN python /app/manage.py collectstatic --noinput -c

# volumes
VOLUME ["/cache", "/youtube"]

# start
WORKDIR /app
EXPOSE 8000

ENTRYPOINT ["/bin/tini", "--"]
CMD ["./run.sh"]
