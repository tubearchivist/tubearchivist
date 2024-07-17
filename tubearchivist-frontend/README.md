# Tubearchivist Frontend React

## Development environment:

Fist start the tubearchivist dev environment, then execute:

```bash
docker compose up --build
```

Now open: http://localhost:8001/

stop:

```bash
docker compose down

```

## Production environment:

Build the production image

```bash
docker build -t tubearchivist-frontend .
```

and switch to tubearchivist and execute

```bash
docker-compose -f .\docker-compose.yml up
```

# Folder structure

```
src ┐
    ├───api
    │   ├───action    // Functions that do write (POST,DELETE) calls to the backend
    │   └───loader    // Functions that do read-only (GET,HEAD) calls to the backend
    ├───components    // React components to be used in pages
    ├───configuration // Application configuration.
    │   ├───colours   // Css loader for themes
    │   ├───constants // global constants that have no good place
    │   └───routes    // Routes definitions used in Links and react-router-dom configuration
    ├───functions     // Useful functions
    └───pages         // React components that define a page/route
```
