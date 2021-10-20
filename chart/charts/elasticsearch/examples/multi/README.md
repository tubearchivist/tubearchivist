# Multi

This example deploy an Elasticsearch 7.15.0 cluster composed of 3 different Helm
releases:

- `helm-es-multi-master` for the 3 master nodes using [master values][]
- `helm-es-multi-data` for the 3 data nodes using [data values][]
- `helm-es-multi-client` for the 3 client nodes using [client values][]

## Usage

* Deploy the 3 Elasticsearch releases: `make install`

* You can now setup a port forward to query Elasticsearch API:

  ```
  kubectl port-forward svc/multi-master 9200
  curl -u elastic:changeme http://localhost:9200/_cat/indices
  ```

## Testing

You can also run [goss integration tests][] using `make test`


[client values]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/examples/multi/client.yaml
[data values]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/examples/multi/data.yaml
[goss integration tests]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/examples/multi/test/goss.yaml
[master values]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/examples/multi/master.yaml
