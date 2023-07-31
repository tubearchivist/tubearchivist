## Contributing to Tube Archivist

Welcome, and thanks for showing interest in improving Tube Archivist!  

## Table of Content
- [How to open an issue](#how-to-open-an-issue)
  - [Bug Report](#bug-report)
  - [Feature Request](#feature-request)
  - [Installation Help](#installation-help)
- [How to make a Pull Request](#how-to-make-a-pull-request)
- [Improve to the Documentation](#improve-to-the-documentation)
- [Development Environment](#development-environment)
---

## How to open an issue
Please read this carefully before opening any [issue](https://github.com/tubearchivist/tubearchivist/issues) on GitHub.

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
This project needs your help to grow further. There is no shortage of ideas, see the open [issues on GH](https://github.com/tubearchivist/tubearchivist/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement) and the [roadmap](https://github.com/tubearchivist/tubearchivist#roadmap), what this project lacks is contributors to implement these ideas.

Existing ideas are easily *multiple years* worth of development effort, at least at current speed. Best and fastest way to implement your feature is to do it yourself, that's why this project is open source after all. This project is *very* selective with accepting new feature requests at this point.  

Good feature requests usually fall into one or more of these categories:
- You want to work on your own idea within the next few days or weeks.
- Your idea is beneficial for a wide range of users, not just for you.
- Your idea extends the current project by building on and improving existing functionality.
- Your idea is quick and easy to implement, for an experienced as well as for a first time contributor.

Your request is likely going to be rejected if:
- Your idea requires multiple days worth of development time and is unrealistic to be implemented any time soon.
- There are already other ways to do what you are trying to do.
- You are trying to do something that only applies to your platform, your specific workflow or your specific setup.
- Your idea would fundamentally change how the project works or it wouldn't be able to be implemented with backwards compatibility.
- Your idea is not a good fit for this project.

### Installation Help
GitHub is most likely not the best place to ask for installation help. That's inherently individual and one on one.
1. First step is always, help yourself. Start at the [Readme](https://github.com/tubearchivist/tubearchivist) or the additional platform specific installation pages in the [docs](https://docs.tubearchivist.com/).
2. If that doesn't answer your question, open a `#support` thread on [Discord](https://www.tubearchivist.com/discord).
3. Only if that is not an option, open an issue here.

IMPORTANT: When receiving help, contribute back to the community by improving the installation instructions with your newly gained knowledge.

---

## How to make a Pull Request

Thank you for contributing and helping improve this project. This is a quick checklist to help streamline the process:

- For **code changes**, make your PR against the [testing branch](https://github.com/tubearchivist/tubearchivist/tree/testing). That's where all active development happens. This simplifies the later merging into *master*, minimizes any conflicts and usually allows for easy and convenient *fast-forward* merging.
- For **documentation changes**, make your PR directly against the *master* branch.
- Show off your progress, even if not yet complete, by creating a [draft](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests#draft-pull-requests) PR first and switch it as *ready* when you are ready.
- Make sure all your code is linted and formatted correctly, see below. The automatic GH action unfortunately needs to be triggered manually by a maintainer for first time contributors, but will trigger automatically for existing contributors.

### Making changes to the JavaScript

The JavaScript does not require any build step; you just edit the files directly. However, there is config for eslint and prettier (a linter and formatter respectively); their use is recommended but not required. To use them, install `node`, run `npm i` from the root directory of this repository to install dependencies, then run `npm run lint` and `npm run format` to run eslint and prettier respectively.

### Code formatting and linting

To keep things clean and consistent for everybody, there is a github action setup to lint and check the changes. You can test your code locally first if you want. For example if you made changes in the **video** module, run

```shell
./deploy.sh validate tubearchivist/home/src/index/video.py
```

to validate your changes. If you omit the path, all the project files will get checked. This is subject to change as the codebase improves.

---

## Improve to the Documentation

The documentation available at [docs.tubearchivist.com](https://docs.tubearchivist.com/) and is build from a separate repo [tubearchivist/docs](https://github.com/tubearchivist/docs). The Readme has additional instructions on how to make changes.

---

## Development Environment

I have learned the hard way, that working on a dockerized application outside of docker is very error prone and in general not a good idea. So if you want to test your changes, it's best to run them in a docker testing environment. You might be able to run the application directly, but this document assumes you're using docker.

### Instructions

Set up docker on your development machine.

Clone this repository.

Functional changes should be made against the unstable `testing` branch, so check that branch out, then make a new branch for your work.

Edit the `docker-compose.yml` file and replace the [`image: bbilly1/tubearchivist` line](https://github.com/tubearchivist/tubearchivist/blob/4af12aee15620e330adf3624c984c3acf6d0ac8b/docker-compose.yml#L7) with `build: .`. Also make any other changes to the environment variables and so on necessary to run the application, just like you're launching the application as normal.

Run `docker compose up --build`. This will bring up the application. Kill it with `ctrl-c` or by running `docker compose down` from a new terminal window in the same directory.

Make your changes locally and re-run `docker compose up --build`. The `Dockerfile` is structured in a way that the actual application code is in the last layer so rebuilding the image with only code changes utilizes the build cache for everything else and will just take a few seconds.

### Develop environment inside a VM

You may find it nice to run everything inside of a VM, though this is not necessary. There's a `deploy.sh` script which has some helpers for this use case. YMMV, this is what one of the developers does:

- Clone the repo, work on it with your favorite code editor in your local filesystem. *testing* branch is where all the changes are happening, might be unstable and is WIP.
- Then I have a VM running standard Ubuntu Server LTS with docker installed. The VM keeps my projects separate and offers convenient snapshot functionality. The VM also offers ways to simulate low end environments by limiting CPU cores and memory. You can use this [Ansible Docker Ubuntu](https://github.com/bbilly1/ansible-playbooks) playbook to get started quickly. But you could also just run docker on your host system.
- I have my local DNS resolve `tubearchivist.local` to the IP of the VM for convenience. To deploy the latest changes and rebuild the application to the testing VM run:
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
