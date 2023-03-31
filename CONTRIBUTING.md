## Contributing to Tube Archivist

Welcome, and thanks for showing interest in improving Tube Archivist!  
If you haven't already, the best place to start is the README. This will give you an overview on what the project is all about.

## Report a bug

If you notice something is not working as expected, check to see if it has been previously reported in the [open issues](https://github.com/tubearchivist/tubearchivist/issues).
If it has not yet been disclosed, go ahead and create an issue.  
If the issue doesn't move forward due to a lack of response, I assume it's solved and will close it after some time to keep the list fresh. 

## Documentation

The documentation available at [docs.tubearchivist.com](https://docs.tubearchivist.com/), is build from [tubearchivist/docs](https://github.com/tubearchivist/docs). The Readme has additional instructions on how to make changes.

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

- Clone the repo, work on it with your favorite code editor in your local filesystem. *testing* branch is the where all the changes are happening, might be unstable and is WIP.
- Then I have a VM running standard Ubuntu Server LTS with docker installed. The VM keeps my projects separate and offers convenient snapshot functionality. The VM also offers ways to simulate lowend environments by limiting CPU cores and memory. You can use this [Ansible Docker Ubuntu](https://github.com/bbilly1/ansible-playbooks) playbook to get started quickly. But you could also just run docker on your host system.
- I have my local DNS resolve `tubearchivist.local` to the IP of the VM for convenience. To deploy the latest changes and rebuild the application to the testing VM run:
```bash
./deploy.sh test
```
- The command above will call the docker build command with `--build-arg INSTALL_DEBUG=1` to install additional useful debug tools.
- The `test` argument takes another optional argument to build for a specific architecture valid options are: `amd64`, `arm64` and `multi`, default is `amd64`.
- This `deploy.sh` script is not meant to be universally usable for every possible environment but could serve as an idea on how to automatically rebuild containers to test changes - customize to your liking. 

## Working with Elasticsearch
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

## Implementing a new feature

Do you see anything on the roadmap that you would like to take a closer look at but you are not sure, what's the best way to tackle that? Or anything not on there yet you'd like to implement but are not sure how? Reach out on Discord and we'll look into it together.

## Making changes

To fix a bug or implement a feature, fork the repository and make all changes to the testing branch. When ready, create a pull request.

## Making changes to the JavaScript

The JavaScript does not require any build step; you just edit the files directly. However, there is config for eslint and prettier (a linter and formatter respectively); their use is recommended but not required. To use them, install `node`, run `npm i` from the root directory of this repository to install dependencies, then run `npm run lint` and `npm run format` to run eslint and prettier respectively.

## Releases

There are three different docker tags:
- **latest**: As the name implies is the latest multiarch release for regular usage.
- **unstable**: Intermediate amd64 builds for quick testing and improved collaboration. Don't mix with a *latest* installation, for your testing environment only. This is untested and WIP and will have breaking changes between commits that might require a reset to resolve. 
- **semantic versioning**: There will be a handful named version tags that will also have a matching release and tag on github.

If you want to see what's in your container, checkout the matching release tag. A merge to **master** usually means a *latest* or *unstable* release. If you want to preview changes in your testing environment, pull the *unstable* tag or clone the repository and build the docker container with the Dockerfile from the **testing** branch.

## Code formatting and linting

To keep things clean and consistent for everybody, there is a github action setup to lint and check the changes. You can test your code locally first if you want. For example if you made changes in the **video** module, run

```shell
./deploy.sh validate tubearchivist/home/src/index/video.py
```

to validate your changes. If you omit the path, all the project files will get checked. This is subject to change as the codebase improves. 
