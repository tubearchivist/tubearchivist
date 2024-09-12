# Contributing to Tube Archivist

Welcome, and thanks for showing interest in improving Tube Archivist!  

## Table of Content
- [Next Steps](#next-steps)
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

## Next Steps
Going forward, this project will focus on developing a new modern frontend.

- For the time being, don't open any new PRs that are not towards the new frontend.
- New features requests likely won't get accepted during this process.
- Depending on the severity, bug reports may or may not get fixed during this time.
- When in doubt, reach out.

Join us on [Discord](https://tubearchivist.com/discord) if you want to help with that process.

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

### Making changes to the JavaScript

The JavaScript does not require any build step; you just edit the files directly. However, there is config for eslint and prettier (a linter and formatter respectively); their use is recommended but not required. To use them, install `node`, run `npm i` from the root directory of this repository to install dependencies, then run `npm run lint` and `npm run format` to run eslint and prettier respectively.

### Code formatting and linting

To keep things clean and consistent for everybody, there is a github action setup to lint and check the changes. You can test your code locally first if you want. For example if you made changes in the **video** module, run

```shell
./deploy.sh validate tubearchivist/home/src/index/video.py
```

to validate your changes. If you omit the path, all the project files will get checked. This is subject to change as the codebase improves.

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
