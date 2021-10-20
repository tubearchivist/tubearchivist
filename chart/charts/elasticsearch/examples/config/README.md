# Config

This example deploy a single node Elasticsearch 7.15.0 with authentication and
custom [values][].


## Usage

* Create the required secrets: `make secrets`

* Deploy Elasticsearch chart with the default values: `make install`

* You can now setup a port forward to query Elasticsearch API:

  ```
  kubectl port-forward svc/config-master 9200
  curl -u elastic:changeme http://localhost:9200/_cat/indices
  ```


## Testing

You can also run [goss integration tests][] using `make test`


[goss integration tests]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/examples/config/test/goss.yaml
[values]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/examples/config/values.yaml
