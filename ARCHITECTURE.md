# The Inner Workings of Tube Archivist
This is a high level overview of the architecture of Tube Archivist, intended for interested contributors to find your way around quickly.

```
                        Tube Archivist
        ______________________|_____________________
        |                     |                    |
-------------------    ---------------    -------------------
|                 |    |             |    |                 |
|  DjangoProject  |    |  RedisJson  |    |  ElasticSearch  |
|                 |    |             |    |                 |
-------------------    ---------------    -------------------
```

## DjangoProject
This is the main Python application. Django serves its data container internally with **Uwsgi** on port 8080, the interface is served with **Nginx** on the public port 8000.

Users created static files like media files and artwork as well as application artwork like logos and fonts are served directly from Nginx, while the rest of the application uses uwsgi_pass to proxy the requests to uwsgi.

Config files are located in the `docker_assets` folder. The script `run.sh` is the container `CMD` command and entry point, validating env vars, connection to ElasticSearch (ES) and will start the application.

Compared to other Django projects, this application doesn't make use of the database models, due to a lack of integration with ES. This project has its own abstractions and integrations, treating ES as a REST API.

Long running application tasks are handed off to **Celery** - using **Redis** as a broker - to run asynchronously from the main threads. 
- All tasks are defined in the `home.tasks.py` module.

There are three Django apps:
- **config**: The root app, routing the main endpoints and the main `settings.py` file
- **api**: The API app with its views and functionality
- **home**: Most of the application logic, templates and views, will probably get split up further in the future.

The *home* app is split up into packages in the `src` directory:
- **download**: All download related classes, interact with yt-dlp, download artwork, handle the download queue and post processing tasks.
- **es**: All index setup and validation classes, handles mapping validations and makes mapping changes, wrapper functions to simplify interactions with Elasticsearch, backup and restore.
- **frontend**: All direct interactions with the frontend, like Django forms, searching, watched state changes, and legacy api_calls in the process of moving to the api app.
- **index**: Contains all functionality for scraping and indexing videos, channels, playlists, comments, subtitles, etc...
- **ta**: Loose collection of functions and classes, handle application config and contains redis wrapper classes.

## RedisJson
Holds the main application config json object that gets dynamically edited from the frontend, serves as a message broker for **Celery**. Redis serves as a temporary and thread safe link between Django and the frontend, storing progress messages and temporary queues for processing. Used to store locking keys for threads and execution details for tasks.

- Wrapper classes to interact with Redis are located in the `home.src.ta.ta_redis.py` module.

## ElasticSearch (ES)
Is used to store and index all metadata, functions as an application database and makes it all searchable. The mapping defines which fields are indexed as searchable text fields and which fields are used for match filtering.

- The index setup and validation is handled in the `home.src.es.index_setup.py` module.
- Wrapper classes for making requests to ES are located in the `home.src.es.connect.py` module.
