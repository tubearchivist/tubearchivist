# Docker for Mac

This example deploy a 3 nodes Elasticsearch 7.15.0 cluster on [Docker for Mac][]
using [custom values][].

Note that this configuration should be used for test only and isn't recommended
for production.


## Usage

* Deploy Elasticsearch chart with the default values: `make install`

* You can now setup a port forward to query Elasticsearch API:

  ```
  kubectl port-forward svc/elasticsearch-master 9200
  curl localhost:9200/_cat/indices
  ```


[custom values]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/examples/docker-for-mac/values.yaml
[docker for mac]: https://docs.docker.com/docker-for-mac/kubernetes/
