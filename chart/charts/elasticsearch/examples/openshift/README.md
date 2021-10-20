# OpenShift

This example deploy a 3 nodes Elasticsearch 7.15.0 cluster on [OpenShift][]
using [custom values][].

## Usage

* Deploy Elasticsearch chart with the default values: `make install`

* You can now setup a port forward to query Elasticsearch API:

  ```
  kubectl port-forward svc/elasticsearch-master 9200
  curl localhost:9200/_cat/indices
  ```

## Testing

You can also run [goss integration tests][] using `make test`


[custom values]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/examples/openshift/values.yaml
[goss integration tests]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/examples/openshift/test/goss.yaml
[openshift]: https://www.openshift.com/
