# Frequently Asked Questions

## 1. Scope of this project
Tube Archivist is *Your self hosted YouTube media server*, which also defines the primary scope of what this project tries to do:
- **Self hosted**: This assumes you have full control over the underlying operating system and hardware and can configure things to work properly with Docker, it's volumes and networks as well as whatever disk storage and filesystem you choose to use.
- **YouTube**: Downloading, indexing and playing videos from YouTube, there are currently no plans to expand this to any additional platforms.
- **Media server**: This project tries to be a stand alone media server in it's own web interface.

Additionally to that, progress is also happening on:
- **API**: Endpoints for additional integrations.
- **Browser Extension**: To integrate between youtube.com and Tube Archivist.

Defining the scope is important for the success of any project:
- A scope too broad will result in development effort spreading too thin and will run into danger that his project tries to do too many things and none of them well.
- A too narrow scope will make this project uninteresting and will exclude audiences that could also benefit from this project.
- Not defining a scope will easily lead to misunderstandings and false hopes of where this project tries to go.

Of course this is subject to change, as this project continues to grow and more people contribute.

## 2. Emby/Plex/Jellyfin/Kodi integrations
Although there are similarities between these excellent projects and Tube Archivist, they have a very different use case. Trying to fit the metadata relations and database structure of a YouTube archival project into these media servers that specialize in Movies and TV shows is always going to be limiting.

Part of the scope is to be its own media server, so that's where the focus and effort of this project is. That being said, the nature of self hosted and open source software gives you all the possible freedom to use your media as you wish.

## 3. To Docker or not to Docker
This project is a classical docker application: There are multiple moving parts that need to be able to interact with each other and need to be compatible with multiple architectures and operating systems. Additionally Docker also drastically reduces development complexity which is highly appreciated.  

So Docker is the only supported installation method. If you don't have any experience with Docker, consider investing the time to learn this very useful technology.

## 4. Finetuning Elasticsearch
A minimal configuration of Elasticsearch (ES) is provided in the example docker-compose.yml file. ES is highly configurable and very interesting to learn more about. Refer to the [documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html) if you want to get into it.

## 5. Advanced Authentication
If you like to use things like SSO, LDAP or 2FA to login, consider using something like Authelia as a reverse proxy so this project can focus on the core task. Tube Archivist has a *remember me* checkbox at login to extend your sessions lifetime in your browser. 
