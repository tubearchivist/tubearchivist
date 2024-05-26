# multi stage to build tube archivist
# build python wheel, download and extract ffmpeg, copy into final image


# First stage to build python wheel
FROM python:3.11.8-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libldap2-dev libsasl2-dev libssl-dev git

# install requirements
COPY ./tubearchivist/requirements.txt /requirements.txt
RUN pip install --user -r requirements.txt

# build ffmpeg
FROM python:3.11.8-slim-bookworm as ffmpeg-builder

ARG TARGETPLATFORM

COPY docker_assets/ffmpeg_download.py ffmpeg_download.py
RUN python ffmpeg_download.py $TARGETPLATFORM

# build final image
FROM python:3.11.8-slim-bookworm as tubearchivist

ARG INSTALL_DEBUG

ENV PYTHONUNBUFFERED 1

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
    curl && rm -rf /var/lib/apt/lists/*

# install debug tools for testing environment
RUN if [ "$INSTALL_DEBUG" ] ; then \
        apt-get -y update && apt-get -y install --no-install-recommends \
        vim htop bmon net-tools iputils-ping procps \
        && pip install --user ipython pytest pytest-django \
    ; fi

# make folders
RUN mkdir /cache /youtube /app

# copy config files
COPY docker_assets/nginx.conf /etc/nginx/sites-available/default
RUN sed -i 's/^user www\-data\;$/user root\;/' /etc/nginx/nginx.conf

# copy application into container
COPY ./tubearchivist /app
COPY ./docker_assets/run.sh /app
COPY ./docker_assets/uwsgi.ini /app

# volumes
VOLUME /cache
VOLUME /youtube

# start
WORKDIR /app
EXPOSE 8000

RUN chmod +x ./run.sh

CMD ["./run.sh"]
