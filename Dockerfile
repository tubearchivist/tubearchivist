# build the tube archivist image from default python slim image

FROM python:3.9.7-slim-bullseye

ENV PYTHONUNBUFFERED 1

# install distro packages needed
RUN apt-get clean && apt-get -y update && apt-get -y install --no-install-recommends \
    build-essential \
    ffmpeg \
    nginx \
    curl && rm -rf /var/lib/apt/lists/*

# copy config files
COPY nginx.conf /etc/nginx/conf.d/

# make folders
RUN mkdir /cache
RUN mkdir /youtube
RUN mkdir /app

# install python dependencies
COPY ./tubearchivist/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt --src /usr/local/src

# copy application into container
COPY ./tubearchivist /app
COPY ./run.sh /app
COPY ./uwsgi.ini /app

# volumes
VOLUME /cache
VOLUME /youtube

# start
WORKDIR /app
EXPOSE 8000

RUN chmod +x ./run.sh

CMD ["./run.sh"]
