## Contributing to Tube Archivist

Welcome, and thanks for showing interest in improving Tube Archivist!  
If you haven't already, the best place to start is the README. This will give you an overview on what the project is all about.

## Report a bug

If you notice something is not working as expected, check to see if it has been previously reported in the [open issues](https://github.com/tubearchivist/tubearchivist/issues).
If it has not yet been disclosed, go ahead and create an issue.  
If the issue doesn't move forward due to a lack of response, I assume it's solved and will close it after some time to keep the list fresh. 

## Wiki

The wiki is where all user functions are explained in detail. These pages are mirrored into the **docs** folder of the repo. This allows for pull requests and all other features like regular code. Make any changes there, and I'll sync them with the wiki tab.

## Development Environment

I have learned the hard way, that working on a dockerized application outside of docker is very error prone and in general not a good idea. So if you want to test your changes, it's best to run them in a docker testing environment.  

This is my setup I have landed on, YMMV:
- Clone the repo, work on it with your favorite code editor in your local filesystem. *testing* branch is the where all the changes are happening, might be unstable and is WIP.
- Then I have a VM on KVM hypervisor running standard Ubuntu Server LTS with docker installed. The VM keeps my projects separate and offers convenient snapshot functionality. The VM also offers ways to simulate lowend environments by limiting CPU cores and memory. But you could also just run docker on your host system.
- The `Dockerfile` is structured in a way that the actual application code is in the last layer so rebuilding the image with only code changes utilizes the build cache for everything else and will just take a few seconds.
- Take a look at the `deploy.sh` file. I have my local DNS resolve `tubearchivist.local` to the IP of the VM for convenience. To deploy the latest changes and rebuild the application to the testing VM run:
```bash
./deploy.sh test
```
- The command above will call the docker build command with `--build-arg INSTALL_DEBUG=1` to install additional useful debug tools.
- The `test` argument takes another optional argument to build for a specific architecture valid options are: `amd64`, `arm64` and `multi`, default is `amd64`.
- This `deploy.sh` file is not meant to be universally usable for every possible environment but could serve as an idea on how to automatically rebuild containers to test changes - customize to your liking. 

## Working with Elasticsearch
Additionally to the required services as listed in the example docker-compose file, the **Dev Tools** of [Kibana](https://www.elastic.co/guide/en/kibana/current/docker.html) are invaluable for running and testing Elasticsearch queries.  

If you want to run queries in on the Elasticsearch container directly from your host with for example `curl` or something like *postman*, you might want to **publish** the port 9200 instead of just **exposing** it.

## Implementing a new feature

Do you see anything on the roadmap that you would like to take a closer look at but you are not sure, what's the best way to tackle that? Or anything not on there yet you'd like to implement but are not sure how? Open up an issue and we try to find a solution together.

## Making changes

To fix a bug or implement a feature, fork the repository and make all changes to the testing branch. When ready, create a pull request.

## Releases

There are three different docker tags:
- **latest**: As the name implies is the latest multiarch release for regular usage.
- **unstable**: Intermediate amd64 builds for quick testing and improved collaboration. Don't mix with a *latest* installation, for your testing environment only. This is untested and WIP and will have breaking changes between commits that might require a reset to resolve. 
- **semantic versioning**: There will be a handful named version tags that will also have a matching release and tag on github.

If you want to see what's in your container, checkout the matching release tag. A merge to **master** usually means a *latest* or *unstable* release. If you want to preview changes in your testing environment, pull the *unstable* tag or clone the repository and build the docker container with the Dockerfile from the **testing** branch.

## Code formatting and linting

To keep things clean and consistent for everybody, there is a github action setup to lint and check the changes. You can test your code locally first if you want. For example if you made changes in the **download** module, run

```shell
./deploy.sh validate tubearchivist/home/src/download.py
```

to validate your changes. If you omit the path, all the project files will get checked. This is subject to change as the codebase improves. 