# multi stage to build tube archivist
# build python wheel, download and extract ffmpeg, copy into final image

FROM --platform=$BUILDPLATFORM node:22.12.0-alpine AS npm-builder
COPY frontend/package.json frontend/package-lock.json /
RUN npm i

FROM --platform=$BUILDPLATFORM node:22.12.0-alpine AS node-builder

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
RUN pip install --user -r requirements.txt

# build ffmpeg
FROM python:3.13.11-slim-trixie AS ffmpeg-builder

ARG TARGETPLATFORM

COPY docker_assets/ffmpeg_download.py ffmpeg_download.py
RUN python ffmpeg_download.py $TARGETPLATFORM

FROM python:3.13.11-slim-trixie AS s6-overlay
ARG S6_OVERLAY_VERSION=3.2.2.0
ENV S6_BEHAVIOUR_IF_STAGE2_FAILS=2

ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp/s6-noarch.tar.xz

FROM s6-overlay AS s6-overlay-amd64
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-x86_64.tar.xz /tmp/s6.tar.xz

FROM s6-overlay AS s6-overlay-arm64
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-aarch64.tar.xz /tmp/s6.tar.xz

# build final image
FROM s6-overlay-${TARGETARCH} AS tubearchivist

ARG INSTALL_DEBUG
ARG TARGETPLATFORM

ENV PYTHONUNBUFFERED=1

COPY --from=denoland/deno:bin /deno /usr/local/bin/deno

# copy build requirements
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# copy ffmpeg
COPY --from=ffmpeg-builder ./ffmpeg/ffmpeg /usr/bin/ffmpeg
COPY --from=ffmpeg-builder ./ffprobe/ffprobe /usr/bin/ffprobe

# install distro packages needed
RUN apt-get clean && apt-get -y update && apt-get -y install --no-install-recommends \
    nginx \
    atomicparsley \
    xz-utils \
    s6 \
    cron \
    curl && rm -rf /var/lib/apt/lists/*

# install debug tools for testing environment
RUN if [ "$INSTALL_DEBUG" ] ; then \
    apt-get -y update && apt-get -y install --no-install-recommends \
    vim htop bmon net-tools iputils-ping procps lsof \
    && pip install --user ipython pytest pytest-django \
    ; fi

# s6-overlay
RUN ls -l /tmp; tar -C / -Jxpf /tmp/s6-noarch.tar.xz
RUN tar -C / -Jxpf /tmp/s6.tar.xz
RUN rm /tmp/*
COPY ./s6-overlay /etc/s6-overlay

# make folders
RUN mkdir /cache /youtube /app

# copy config files
COPY docker_assets/nginx.conf /etc/nginx/sites-available/default
RUN sed -i 's/^user www\-data\;$/user root\;/' /etc/nginx/nginx.conf

# copy application into container
COPY ./backend /app
COPY ./docker_assets/backend_start.py /app
COPY ./docker_assets/*.sh /app
COPY --chmod=600 ./docker_assets/cron.d/* /etc/cron.d

COPY --from=node-builder ./frontend/dist /app/static

# volumes
VOLUME /cache
VOLUME /youtube

# start
WORKDIR /app
EXPOSE 8000

CMD ["/app/backend.sh"]

ENTRYPOINT ["/init"]
