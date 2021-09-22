## Contributing to Tube Archivist

Welcome, and thanks for showing interest in improving Tube Archivist!  
If you haven't already, the best place to start is the README. This will give you an overview on what the project is all about.

## Report a bug

If you notice something is not working as expected, check to see if it has been previously reported in the [open issues](https://github.com/bbilly1/tubearchivist/issues).
If it has not yet been disclosed, go ahead and create an issue.

## Making changes

To fix a bug or implement a feature, fork the repository and make all changes to the testing branch. When ready, create a pull request.

## Releases

Everything on the master branch is what's in the latest release and is what you get in your container when you `pull` either the *:latest* tag or the newest named version. If you want to test the newest changes and improvements, clone the repository and build the docker container with the Dockerfile from the testing branch.

## Code formatting and linting

To keep things clean and consistent for everybody, there is a github action setup to lint and check the changes. You can test your code locally first if you want. For example if you made changes in the **download** module, run

```shell
./deploy.sh validate tubearchivist/home/src/download.py
```

to validate your changes. If you omit the path, all the project files will get checked. This is subject to change as the codebase improves. 