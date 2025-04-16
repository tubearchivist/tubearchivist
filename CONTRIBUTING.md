# Contributing to Tube Archivist

Welcome, and thanks for showing interest in improving Tube Archivist!  

## Table of Content
- [Beta Testing](#beta-testing)
- [How to open an issue](#how-to-open-an-issue)
  - [Bug Report](#bug-report)
  - [Feature Request](#feature-request)
  - [Installation Help](#installation-help)
- [How to make a Pull Request](#how-to-make-a-pull-request)
- [Contributions beyond the scope](#contributions-beyond-the-scope)
- [User Scripts](#user-scripts)
- [Improve to the Documentation](#improve-to-the-documentation)
- [Development Environment](#development-environment)
---

## Beta Testing
Be the first to help test new features and improvements and provide feedback! There are regular `:unstable` builds for easy access. That's for the tinkerers and the breave. Ideally use a testing environment first, before a release be the first to install it on your main system.

There is always something that can get missed during development. Look at the commit messages tagged with `#build`, these are the unstable builds and give a quick overview what has changed.

- Test the features mentioned, play around, try to break it.
- Test the update path by installing the `:latest` release first, the upgrade to `:unstable` to check for any errors.
- Test the unstable build on a fresh install.

Then provide feedback, if there is a problem but also if there is no problem. Reach out on [Discord](https://tubearchivist.com/discord) in the `#beta-testing` channel with your findings.

This will help with a smooth update for the regular release. Plus you get to test things out early! 

## How to open an issue
Please read this carefully before opening any [issue](https://github.com/tubearchivist/tubearchivist/issues) on GitHub. Make sure you read [Next Steps](#next-steps) above.

**Do**:
- Do provide details and context, this matters a lot and makes it easier for people to help.
- Do familiarize yourself with the project first, some questions answer themselves when using the project for some time. Familiarize yourself with the [Readme](https://github.com/tubearchivist/tubearchivist) and the [documentation](https://docs.tubearchivist.com/), this covers a lot of the common questions, particularly the [FAQ](https://docs.tubearchivist.com/faq/).
- Do respond to questions within a day or two so issues can progress. If the issue doesn't move forward due to a lack of response, we'll assume it's solved and we'll close it after some time to keep the list fresh.

**Don't**:
- Don't open *duplicates*, that includes open and closed issues.
- Don't open an issue for something that's already on the [roadmap](https://github.com/tubearchivist/tubearchivist#roadmap), this needs your help to implement it, not another issue.
- Don't open an issue for something that's a [known limitation](https://github.com/tubearchivist/tubearchivist#known-limitations). These are *known* by definition and don't need another reminder. Some limitations may be solved in the future, maybe by you?
- Don't overwrite the *issue template*, they are there for a reason. Overwriting that shows that you don't really care about this project. It shows that you have a misunderstanding how open source collaboration works and just want to push your ideas through. Overwriting the template may result in a ban.

### Bug Report
Bug reports are highly welcome! This project has improved a lot due to your help by providing feedback when something doesn't work as expected. The developers can't possibly cover all edge cases in an ever changing environment like YouTube and yt-dlp.

Please keep in mind:
- Docker logs are the easiest way to understand what's happening when something goes wrong, *always* provide the logs upfront.
- Set the environment variable `DJANGO_DEBUG=True` to Tube Archivist and reproduce the bug for a better log output. Don't forget to remove that variable again after.
- A bug that can't be reproduced, is difficult or sometimes even impossible to fix. Provide very clear steps *how to reproduce*.

### Feature Request
This project doesn't take any new feature requests. This project doesn't lack ideas, see the currently open tasks and roadmap. New feature requests aren't helpful at this point in time. Thank you for your understanding.

### Installation Help
GitHub is most likely not the best place to ask for installation help. That's inherently individual and one on one.
1. First step is always, help yourself. Start at the [Readme](https://github.com/tubearchivist/tubearchivist) or the additional platform specific installation pages in the [docs](https://docs.tubearchivist.com/).
2. If that doesn't answer your question, open a `#support` thread on [Discord](https://www.tubearchivist.com/discord).
3. Only if that is not an option, open an issue here.

IMPORTANT: When receiving help, contribute back to the community by improving the installation instructions with your newly gained knowledge.

---

## How to make a Pull Request

Make sure you read [Next Steps](#next-steps) above.

Thank you for contributing and helping improve this project. Focus for the foreseeable future is on improving and building on existing functionality, *not* on adding and expanding the application.

This is a quick checklist to help streamline the process:

- For **code changes**, make your PR against the [testing branch](https://github.com/tubearchivist/tubearchivist/tree/testing). That's where all active development happens. This simplifies the later merging into *master*, minimizes any conflicts and usually allows for easy and convenient *fast-forward* merging.
- For **documentation changes**, make your PR directly against the *master* branch.
- Show off your progress, even if not yet complete, by creating a [draft](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests#draft-pull-requests) PR first and switch it as *ready* when you are ready.
- Make sure all your code is linted and formatted correctly, see below. The automatic GH action unfortunately needs to be triggered manually by a maintainer for first time contributors, but will trigger automatically for existing contributors.

### Code formatting and linting

This project uses the excellent [pre-commit](https://github.com/pre-commit/pre-commit) library. The [pre-commit-config.yml](https://github.com/tubearchivist/tubearchivist/blob/master/.pre-commit-config.yaml) file is part of this repo.

**Quick Start**
- Run `pre-commit install` from the root of the repo.
- Next time you commit to your local git repo, the defined hooks will run.
- On first run, this will download and install the needed environments to your local machine, that can take some time. But that will be reused on sunsequent commits. 

That is also running as a Git Hub action.

---

## Contributions beyond the scope

As you have read the [FAQ](https://docs.tubearchivist.com/faq/) and the [known limitations](https://github.com/tubearchivist/tubearchivist#known-limitations) and have gotten an idea what this project tries to do, there will be some obvious shortcomings that stand out, that have been explicitly excluded from the scope of this project, at least for the time being.

Extending the scope of this project will only be feasible with more [regular contributors](https://github.com/tubearchivist/tubearchivist/graphs/contributors) that are willing to help improve this project in the long run. Contributors that have an overall improvement of the project in mind and not just about implementing this *one* thing.  

Small minor additions, or making a PR for a documented feature request or bug, even if that was and will be your only contribution to this project, are always welcome and is *not* what this is about.

Beyond that, general rules to consider:

- Maintainability is key: It's not just about implementing something and being done with it, it's about maintaining it, fixing bugs as they occur, improving on it and supporting it in the long run.
- Others can do it better: Some problems have been solved by very talented developers. These things don't need to be reinvented again here in this project.
- Develop for the 80%: New features and additions *should* be beneficial for 80% of the users. If you are trying to solve your own problem that only applies to you, maybe that would be better to do in your own fork or if possible by a standalone implementation using the API.
- If all of that sounds too strict for you, as stated above, start becoming a regular contributor to this project.

---

## User Scripts
Some of you might have created useful scripts or API integrations around this project. Sharing is caring! Please add a link to your script to the Readme [here](https://github.com/tubearchivist/tubearchivist#user-scripts).
- Your repo should have a `LICENSE` file with one of the common open source licenses. People are expected to fork, adapt and build upon your great work.
- Your script should not modify the *official* files of Tube Archivist. E.g. your symlink script should build links *outside* of your `/youtube` folder. Or your fancy script that creates a beautiful artwork gallery should do that *outside* of the `/cache` folder. Modifying the *official* files and folders of TA are probably not supported.
- On the top of the repo you should have a mention and a link back to the Tube Archivist repo. Clearly state to **not** to open any issues on the main TA repo regarding your script.
- Example template:
  - `[<user>/<repo>](https://linktoyourrepo.com)`: A short one line description.

---

## Improve to the Documentation

The documentation available at [docs.tubearchivist.com](https://docs.tubearchivist.com/) and is build from a separate repo [tubearchivist/docs](https://github.com/tubearchivist/docs). The Readme there has additional instructions on how to make changes.

---

## Development Environment

This codebase is set up to be developed natively outside of docker as well as in a docker container. Developing outside
of a docker container can be convenient, as IDE and hot reload usually works out of the box. But testing inside of a
container is still essential, as there are subtle differences, especially when working with the filesystem and networking
between containers.

In general, you need to perform the following steps:
1. Define the environment variables
2. Configure and launch Elasticsearch and Redis
3. Configure and launch the backend, worker and scheduler
4. Configure and launch the fronted

Note:
- Subtitles currently fail to load with `DJANGO_DEBUG=True`, that is due to incorrect `Content-Type` error set by Django's 
  static file implementation. That's only if you run the Django dev server, Nginx sets the correct headers.

### Native Instruction

The instructions to develop the application in a native environment might be applied, with minor changes, to the other cases.
To speed up the development, you will need 5 terminals:
- 1 terminal to run docker compose
- 1 terminal to install the virtual environment, the python libraries and launch the backend
- 1 terminal to run the worker
- 1 terminal to run the scheduler
- 1 terminal to run the frontend

#### Define the environment variables

Create a file named `.env` in the `backend` folder with the following content (you can modify them according your needs, but
in general they should work out of the box). Or copy, paste and rename the default development template `dev_assets/template.env`
file.

```shell
TA_HOST="http://localhost:3000"
TA_USERNAME="tubearchivist"
TA_PASSWORD="verysecret"
TA_MEDIA_DIR="static/volume/media"
TA_CACHE_DIR="static"
TA_APP_DIR="."
REDIS_CON="redis://localhost:6379"
ES_URL="http://localhost:9200"
ELASTIC_PASSWORD="verysecret"
TZ="America/New_York"
DJANGO_DEBUG=True
```

#### Configure and run Elasticsearch and Redis

When working in a native environment (laptop/computer), you probably want to focus on the development of the application
components (backend/frontend), rather than the external resources like Elasticsearch or Redis. Therefore, it's recommended
to still run Redis and ES in a docker container. Be sure both containers are reachable over the network.
In order to achieve that, add the `ports` element to both the `archivist-es` and `archivist-redis` services in the
`docker-compose.yml` file.
Moreover, the default `tubearchivist` service should be commented out.

The containers should be launched first, as they are dependencies for all the other services.

```yaml
services:
#  tubearchivist:
#    container_name: tubearchivist
#    ...

  archivist-redis:
    ...
    ports:
      - "6379:6379"

  archivist-es:
    ...
    ports:
      - "9200:9200"
```

Then launch the containers with this command:

```shell
# From the root folder of the repository, launch docker compose.
# Both containers, archivist-redis and archivist-es should start

docker compose up
```

#### Configure and launch the backend, worker and scheduler

You need to configure a virtual environment, install the requirements and then launch the services. For simplicity, it is
suggested to launch the services in different terminal as described below.

To set up the virtual environment with name `.venv`, run the following command:

```shell
# From the root folder of the repository, launch this command in the second terminal

# Create the virtual environment
python3 -m venv .venv
```

The virtual environment needs to be set up only once, but it needs to be sourced every time the terminals for the backend
and queue are closed.

To install the python libraries, launch the following commands:

```shell
# This can be executed in the second terminal

# Load the virtual environment
source .venv/bin/activate

# Move to the backend folder
cd backend

# Install the libraries
python3 -m pip install -r requirements-dev.txt
```

The installation of the libraries should be executed each time the contents `requirements-dev.txt` file change.

The first execution of the backend is quite tricky, as there are several steps to be executed. You can take a look at
the container startup script `docker_assets/run.sh`. However, for simplicity, there is
a shell script (`run_dev_backend.sh` in the `dev_assets` folder) which can be executed and contains all the required
commands to bootstrap a test environment. The script can be run at each new restart of the application. It performs the
following steps:
- prepares the environment (needed for the first execution)
- applies the migrations
- checks the environment
- checks the connections
- prepares the environment
- launches the backend application

```shell
# This can be executed in the second terminal

# Load the virtual environment
source .venv/bin/activate

# Move to the backend folder
cd backend

# Launch the script from the backend folder
../dev_assets/run_dev_backend.sh
```

At the end of the setup, if there are no errors, you will see a similar message:

```text
System check identified no issues (0 silenced).
April 12, 2025 - 13:51:52
Django version 5.1.7, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

The backend will be available on [http://localhost:8000/api/](http://localhost:8000/api/).

If the backend works correctly, you need to launch the worker.

```shell
# This can be executed in the third terminal

# Load the virtual environment
source .venv/bin/activate

# Launch the worker from the root folder of the repository
.venv/bin/celery -A task.celery worker \
  --loglevel=INFO \
  --concurrency 4 \
  --max-tasks-per-child 5 \
  --max-memory-per-child 150000
```

You can now launch the scheduler in a new terminal.

```shell
# This can be executed in the fourth terminal

# Load the virtual environment
source .venv/bin/activate

# Launch the scheduler from the root folder of the repository
.venv/bin/celery -A task beat --loglevel=INFO \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

#### Configure and launch the fronted

The frontend is simpler to install. Firstly, you have to install the dependencies, then to launch the application.

```shell
# This can be executed in the fifth terminal

# Move to the frontend folder
cd frontend

# Install the npm libraries
npm install

# Launch the frontend application
npm run dev
```

The frontend should be available at [http://localhost:3000](http://localhost:3000).

### Docker Instructions

Set up docker on your development machine.

Clone this repository.

Functional changes should be made against the unstable `testing` branch, so check that branch out, then make a new branch for your work.

Edit the `docker-compose.yml` file and replace the [`image: bbilly1/tubearchivist` line](https://github.com/tubearchivist/tubearchivist/blob/4af12aee15620e330adf3624c984c3acf6d0ac8b/docker-compose.yml#L7) with `build: .`. Also make any other changes to the environment variables and so on necessary to run the application, just like you're launching the application as normal.

Run `docker compose up --build`. This will bring up the application. Kill it with `ctrl-c` or by running `docker compose down` from a new terminal window in the same directory.

Make your changes locally and re-run `docker compose up --build`. The `Dockerfile` is structured in a way that the actual application code is in the last layer so rebuilding the image with only code changes utilizes the build cache for everything else and will just take a few seconds.

### Develop environment inside a VM

You may find it nice to run everything inside of a VM for complete environment snapshots and encapsulation, though this is not strictly necessary. There's a `deploy.sh` script which has some helpers for this use case:

- This assumes a standard Ubuntu Server VM with docker and docker compose already installed.
- Configure your local DNS to resolve `tubearchivist.local` to the IP of the VM.
- To deploy the latest changes and rebuild the application to the testing VM run:
```bash
./deploy.sh test
```
- The command above will call the docker build command with `--build-arg INSTALL_DEBUG=1` to install additional useful debug tools.
- The `test` argument takes another optional argument to build for a specific architecture valid options are: `amd64`, `arm64` and `multi`, default is `amd64`.
- This `deploy.sh` script is not meant to be universally usable for every possible environment but could serve as an idea on how to automatically rebuild containers to test changes - customize to your liking.

### Working with Elasticsearch
Additionally to the required services as listed in the example docker-compose file, the **Dev Tools** of [Kibana](https://www.elastic.co/guide/en/kibana/current/docker.html) are invaluable for running and testing Elasticsearch queries.

**Quick start**  
Generate your access token in Elasitcsearch:
```bash
bin/elasticsearch-service-tokens create elastic/kibana kibana
```

Example docker compose, use same version as for Elasticsearch:
```yml
services:
  kibana:
    image: docker.elastic.co/kibana/kibana:0.0.0
    container_name: kibana
    environment:
    - "ELASTICSEARCH_HOSTS=http://archivist-es:9200"
    - "ELASTICSEARCH_SERVICEACCOUNTTOKEN=<your-token-here>"
    ports:
    - "5601:5601"
```

If you want to run queries on the Elasticsearch container directly from your host with for example `curl` or something like *postman*, you might want to **publish** the port 9200 instead of just **exposing** it.

**Persist Token**  
The token will get stored in ES in the `config` folder, and not in the `data` folder. To persist the token between ES container rebuilds, you'll need to persist the config folder as an additional volume:

1. Create the token as described above
2. While the container is running, copy the current config folder out of the container, e.g.: 
```
docker cp archivist-es:/usr/share/elasticsearch/config/ volume/es_config
```
3. Then stop all containers and mount this folder into the container as an additional volume:
```yml
- ./volume/es_config:/usr/share/elasticsearch/config
```
4. Start all containers back up.

Now your token will persist between ES container rebuilds.
