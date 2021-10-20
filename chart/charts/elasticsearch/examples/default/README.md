# Default

This example deploy a 3 nodes Elasticsearch 7.15.0 cluster using
[default values][].


## Usage

* Deploy Elasticsearch chart with the default values: `make install`

* You can now setup a port forward to query Elasticsearch API:

  ```
  kubectl port-forward svc/elasticsearch-master 9200
  curl localhost:9200/_cat/indices
  ```


## Testing

You can also run [goss integration tests][] using `make test`


[goss integration tests]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/examples/default/test/goss.yaml
[default values]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/values.yaml
