# MicroK8S

This example deploy a 3 nodes Elasticsearch 7.15.0 cluster on [MicroK8S][]
using [custom values][].

Note that this configuration should be used for test only and isn't recommended
for production.


## Requirements

The following MicroK8S [addons][] need to be enabled:
- `dns`
- `helm`
- `storage`


## Usage

* Deploy Elasticsearch chart with the default values: `make install`

* You can now setup a port forward to query Elasticsearch API:

  ```
  kubectl port-forward svc/elasticsearch-master 9200
  curl localhost:9200/_cat/indices
  ```


[addons]: https://microk8s.io/docs/addons
[custom values]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/examples/microk8s/values.yaml
[MicroK8S]: https://microk8s.io
