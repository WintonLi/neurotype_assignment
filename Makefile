IMAGE_NAME ?= yunxili/neurotype-assignment
IMAGE_TAG ?= latest
IMAGE := $(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: build docker-push purge up down

build:
	docker compose build app

docker-push:
	@set -e; \
	. ./.credentials; \
	echo "$$DOCKER_HUB_KEY" | docker login --username yunxili --password-stdin; \
	docker compose build app; \
	docker push $(IMAGE)

up:
	docker compose up -d

down:
	docker compose down

purge: down
	docker image rm -f $(IMAGE) || true