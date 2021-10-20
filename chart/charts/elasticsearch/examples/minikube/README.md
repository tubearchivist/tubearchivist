# Minikube

This example deploy a 3 nodes Elasticsearch 7.15.0 cluster on [Minikube][]
using [custom values][].

If helm or kubectl timeouts occur, you may consider creating a minikube VM with
more CPU cores or memory allocated.

Note that this configuration should be used for test only and isn't recommended
for production.


## Requirements

In order to properly support the required persistent volume claims for the
Elasticsearch StatefulSet, the `default-storageclass` and `storage-provisioner`
minikube addons must be enabled.

```
minikube addons enable default-storageclass
minikube addons enable storage-provisioner
```


## Usage

* Deploy Elasticsearch chart with the default values: `make install`

* You can now setup a port forward to query Elasticsearch API:

  ```
  kubectl port-forward svc/elasticsearch-master 9200
  curl localhost:9200/_cat/indices
  ```


[custom values]: https://github.com/elastic/helm-charts/tree/7.15/elasticsearch/examples/minikube/values.yaml
[minikube]: https://minikube.sigs.k8s.io/docs/
