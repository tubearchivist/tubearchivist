# multi stage to build tube archivist
# first stage to build python wheel, copy into final image


# First stage to build python wheel
FROM python:3.10.5-slim-bullseye AS builder
ARG TARGETPLATFORM

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc

# install requirements
COPY ./tubearchivist/requirements.txt /requirements.txt
RUN pip install --user -r requirements.txt

# build final image
FROM python:3.10.5-slim-bullseye as tubearchivist

ARG TARGETPLATFORM
ARG INSTALL_DEBUG

ENV PYTHONUNBUFFERED 1

# copy build requirements
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# install distro packages needed
RUN apt-get clean && apt-get -y update && apt-get -y install --no-install-recommends \
    nginx \
    atomicparsley \
    curl \
    xz-utils && rm -rf /var/lib/apt/lists/*

# get newest patched ffmpeg and ffprobe builds for amd64 fall back to repo ffmpeg for arm64
RUN if [ "$TARGETPLATFORM" = "linux/amd64" ] ; then \
    curl -s https://api.github.com/repos/yt-dlp/FFmpeg-Builds/releases/latest \
        | grep browser_download_url \
        | grep ".*master.*linux64.*tar.xz" \
        | cut -d '"' -f 4 \
        | xargs curl -L --output ffmpeg.tar.xz && \
        tar -xf ffmpeg.tar.xz --strip-components=2 --no-anchored -C /usr/bin/ "ffmpeg" && \
        tar -xf ffmpeg.tar.xz --strip-components=2 --no-anchored -C /usr/bin/ "ffprobe" && \
        rm ffmpeg.tar.xz \
    ; elif [ "$TARGETPLATFORM" = "linux/arm64" ] ; then \
        apt-get -y update && apt-get -y install --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/* \
    ; fi

# install debug tools for testing environment
RUN if [ "$INSTALL_DEBUG" ] ; then \
        apt-get -y update && apt-get -y install --no-install-recommends \
        vim htop bmon net-tools iputils-ping procps \
        && pip install --user ipython \
    ; fi

# make folders
RUN mkdir /cache
RUN mkdir /youtube
RUN mkdir /app

# copy config files
COPY docker_assets/nginx.conf /etc/nginx/sites-available/default

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
