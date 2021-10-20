default: test

include ../../../helpers/examples.mk

PREFIX := helm-es-multi
RELEASE := helm-es-multi-master
TIMEOUT := 1200s

install:
	helm upgrade --wait --timeout=$(TIMEOUT) --install --values master.yaml $(PREFIX)-master ../../
	helm upgrade --wait --timeout=$(TIMEOUT) --install --values data.yaml $(PREFIX)-data ../../
	helm upgrade --wait --timeout=$(TIMEOUT) --install --values client.yaml $(PREFIX)-client ../../

test: install goss

purge:
	helm del $(PREFIX)-master
	helm del $(PREFIX)-data
	helm del $(PREFIX)-client
