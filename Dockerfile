# multi stage to build tube archivist
# build python wheel, download and extract ffmpeg, copy into final image

FROM node:lts-alpine AS node-builder

# RUN npm config set registry https://registry.npmjs.org/

COPY ./frontend /frontend

WORKDIR /frontend

RUN npm i
RUN npm run build:deploy

# First stage to build python wheel
FROM python:3.11.8-slim-bookworm AS builder

RUN set -e; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      git \
      libldap2-dev \
      libsasl2-dev \
      libssl-dev \
    ; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* ;

# install requirements
COPY ./backend/requirements.txt /requirements.txt

RUN pip install --user -r requirements.txt

# build ffmpeg
FROM python:3.11.8-slim-bookworm AS ffmpeg-builder

ARG TARGETPLATFORM

COPY docker_assets/ffmpeg_download.py ffmpeg_download.py

RUN python ffmpeg_download.py $TARGETPLATFORM

# build final image
FROM python:3.11.8-slim-bookworm AS tubearchivist

ARG INSTALL_DEBUG

ENV PYTHONUNBUFFERED=1
ENV PATH=/root/.local/bin:$PATH

# install distro packages needed
RUN set -e; \
    apt-get -y update; \
    apt-get -y install --no-install-recommends \
      atomicparsley \
      curl \
      nginx \
    ; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* ;

# install debug tools for testing environment
RUN set -e; \
    if [ "$INSTALL_DEBUG" ]; then \
        apt-get -y update; \
        apt-get -y install --no-install-recommends \
          bmon \
          iputils-ping \
          htop \
          lsof \
          net-tools \
          procps \
          vim \
        ; \
        apt-get clean; \
        rm -rf /var/lib/apt/lists/* ; \
        pip install --user \
          ipython \
          pytest \
          pytest-django \
        ; \
    fi

# copy build requirements
COPY --from=builder /root/.local /root/.local

# copy ffmpeg
COPY --from=ffmpeg-builder ./ffmpeg/ffmpeg /usr/bin/ffmpeg
COPY --from=ffmpeg-builder ./ffprobe/ffprobe /usr/bin/ffprobe

# copy nginx configuration
COPY docker_assets/nginx.conf /etc/nginx/sites-available/default

# copy backend code
COPY ./backend /app
COPY ./docker_assets/run.sh /app
COPY ./docker_assets/backend_start.py /app

# copy frontend code
COPY --from=node-builder ./frontend/dist /app/static

# final setup
RUN set -e; \
    chmod +x /app/run.sh; \
    sed -i 's/^user www\-data\;$/user root\;/' /etc/nginx/nginx.conf; \
    mkdir -p /cache /youtube;

# volumes
VOLUME /cache
VOLUME /youtube

EXPOSE 8000

# start
WORKDIR /app
CMD ["./run.sh"]
