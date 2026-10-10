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
FROM python:3.13.11-slim-trixie AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libldap2-dev libsasl2-dev libssl-dev git

# install requirements
COPY ./backend/requirements.txt /requirements.txt
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-cache-dir -r /requirements.txt

# build ffmpeg
FROM python:3.13.11-slim-trixie AS ffmpeg-builder

ARG TARGETPLATFORM

COPY docker_assets/ffmpeg_download.py ffmpeg_download.py
RUN python ffmpeg_download.py $TARGETPLATFORM

# build final image
FROM python:3.13.11-slim-trixie AS tubearchivist

ENV PYTHONUNBUFFERED=1

COPY --from=denoland/deno:bin /deno /usr/local/bin/deno

# copy build requirements
COPY --from=builder /opt/venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV HOME=/tmp

# copy ffmpeg
COPY --from=ffmpeg-builder ./ffmpeg/ffmpeg /usr/bin/ffmpeg
COPY --from=ffmpeg-builder ./ffprobe/ffprobe /usr/bin/ffprobe

# install distro packages needed
RUN apt-get clean && apt-get -y update && apt-get -y install --no-install-recommends \
    atomicparsley \
    tini \
    curl && rm -rf /var/lib/apt/lists/*

# make folders
RUN mkdir /cache /youtube /app

# copy application into container
COPY ./backend /app
COPY ./docker_assets/run.sh /app
COPY ./docker_assets/backend_start.py /app
COPY ./docker_assets/beat_auto_spawn.sh /app

COPY --from=node-builder ./frontend/dist /app/static

RUN python /app/manage.py collectstatic --noinput -c

# volumes
VOLUME /cache
VOLUME /youtube

# start
WORKDIR /app
EXPOSE 8000

RUN chmod +x ./run.sh

ENTRYPOINT ["/bin/tini", "--"]
CMD ["./run.sh"]
