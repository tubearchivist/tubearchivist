# multi stage to build tube archivist
# first stage to build python wheel, copy into final image


# First stage to build python wheel
FROM python:3.11.3-slim-bullseye AS builder
ARG TARGETPLATFORM

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libldap2-dev libsasl2-dev libssl-dev git

# install requirements
COPY ./tubearchivist/requirements.txt /requirements.txt
RUN pip install --user -r requirements.txt

# build final image
FROM python:3.11.3-slim-bullseye as tubearchivist

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

# install patched ffmpeg build, default to linux64
RUN if [ "$TARGETPLATFORM" = "linux/arm64" ] ; then \
    curl -s https://api.github.com/repos/yt-dlp/FFmpeg-Builds/releases/latest \
        | grep browser_download_url \
        | grep ".*master.*linuxarm64.*tar.xz" \
        | cut -d '"' -f 4 \
        | xargs curl -L --output ffmpeg.tar.xz ; \
    else \
    curl -s https://api.github.com/repos/yt-dlp/FFmpeg-Builds/releases/latest \
        | grep browser_download_url \
        | grep ".*master.*linux64.*tar.xz" \
        | cut -d '"' -f 4 \
        | xargs curl -L --output ffmpeg.tar.xz ; \
    fi && \
    tar -xf ffmpeg.tar.xz --strip-components=2 --no-anchored -C /usr/bin/ "ffmpeg" && \
    tar -xf ffmpeg.tar.xz --strip-components=2 --no-anchored -C /usr/bin/ "ffprobe" && \
    rm ffmpeg.tar.xz

# install debug tools for testing environment
RUN if [ "$INSTALL_DEBUG" ] ; then \
        apt-get -y update && apt-get -y install --no-install-recommends \
        vim htop bmon net-tools iputils-ping procps \
        && pip install --user ipython \
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
