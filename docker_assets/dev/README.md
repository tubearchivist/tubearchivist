# dev environment setup with vscode

build the dev container
`docker-compose -f docker-compose.dev.yml build --no-cache`

start the dev container
`docker-compose -f docker-compose.dev.yml up`

use vscode remote explorer and attach to `tubearchivist`

## in new vscode window attached to container
- Menu -> Run -> Add Configuration
- Django
- add argument `"0.0.0.0:8000"` to `.vscode/launch.json` as shown below

```
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Django",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/manage.py",
            "args": [
                "runserver",
                "0.0.0.0:8000"
            ],
            "django": true,
            "justMyCode": true
        }
    ]
}
```
- Menu -> Run -> Start Debugging

Now you are running with a dev environment where you can connect to the app at http://localhost:8000 with debugging and volume mapped source code.