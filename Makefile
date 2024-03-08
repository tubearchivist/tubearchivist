DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_PROD := $(DOCKER_COMPOSE) -f docker-compose.yml
DOCKER_COMPOSE_DEV := $(DOCKER_COMPOSE) -f docker-compose.dev.yml

.PHONY: help prod dev clean

help:
	@echo "Usage: make [TARGET]"
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'

prod:
	$(DOCKER_COMPOSE_PROD) up -d

dev:
	$(DOCKER_COMPOSE_DEV) up --build --force-recreate

clean:
	$(DOCKER_COMPOSE_PROD) down -v --remove-orphans
	$(DOCKER_COMPOSE_DEV) down -v --remove-orphans
