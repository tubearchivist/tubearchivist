# Tubearchivist Frontend React

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
    ├───functions     // Useful functions and hooks
    ├───pages         // React components that define a page/route
    └───stores        // zustand stores
```
