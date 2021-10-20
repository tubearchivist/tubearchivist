PREFIX := helm-es-migration

data:
	helm upgrade --wait --timeout=$(TIMEOUT) --install --values data.yaml $(PREFIX)-data ../../

master:
	helm upgrade --wait --timeout=$(TIMEOUT) --install --values master.yaml $(PREFIX)-master ../../

client:
	helm upgrade --wait --timeout=$(TIMEOUT) --install --values client.yaml $(PREFIX)-client ../../
