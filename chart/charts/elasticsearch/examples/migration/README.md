# Migration Guide from helm/charts

There are two viable options for migrating from the community Elasticsearch Helm
chart from the [helm/charts][] repo.

1. Restoring from Snapshot to a fresh cluster
2. Live migration by joining a new cluster to the existing cluster.

## Restoring from Snapshot

This is the recommended and preferred option. The downside is that it will
involve a period of write downtime during the migration. If you have a way to
temporarily stop writes to your cluster then this is the way to go. This is also
a lot simpler as it just involves launching a fresh cluster and restoring a
snapshot following the [restoring to a different cluster guide][].

## Live migration

If restoring from a snapshot is not possible due to the write downtime then a
live migration is also possible. It is very important to first test this in a
testing environment to make sure you are comfortable with the process and fully
understand what is happening.

This process will involve joining a new set of master, data and client nodes to
an existing cluster that has been deployed using the [helm/charts][] community
chart. Nodes will then be replaced one by one in a controlled fashion to
decommission the old cluster.

This example will be using the default values for the existing helm/charts
release and for the Elastic helm-charts release. If you have changed any of the
default values then you will need to first make sure that your values are
configured in a compatible way before starting the migration.

The process will involve a re-sync and a rolling restart of all of your data
nodes. Therefore it is important to disable shard allocation and perform a synced
flush like you normally would during any other rolling upgrade. See the
[rolling upgrades guide][] for more information.

* The default image for this chart is
`docker.elastic.co/elasticsearch/elasticsearch` which contains the default
distribution of Elasticsearch with a [basic license][]. Make sure to update the
`image` and `imageTag` values to the correct Docker image and Elasticsearch
version that you currently have deployed.

* Convert your current helm/charts configuration into something that is
compatible with this chart.

* Take a fresh snapshot of your cluster. If something goes wrong you want to be
able to restore your data no matter what.

* Check that your clusters health is green. If not abort and make sure your
cluster is healthy before continuing:

  ```
  curl localhost:9200/_cluster/health
  ```

* Deploy new data nodes which will join the existing cluster. Take a look at the
configuration in [data.yaml][]:

  ```
  make data
  ```

* Check that the new nodes have joined the cluster (run this and any other curl
commands from within one of your pods):

  ```
  curl localhost:9200/_cat/nodes
  ```

* Check that your cluster is still green. If so we can now start to scale down
the existing data nodes. Assuming you have the default amount of data nodes (2)
we now want to scale it down to 1:

  ```
  kubectl scale statefulsets my-release-elasticsearch-data --replicas=1
  ```

* Wait for your cluster to become green again:

  ```
  watch 'curl -s localhost:9200/_cluster/health'
  ```

* Once the cluster is green we can scale down again:

  ```
  kubectl scale statefulsets my-release-elasticsearch-data --replicas=0
  ```

* Wait for the cluster to be green again.
* OK. We now have all data nodes running in the new cluster. Time to replace the
masters by firstly scaling down the masters from 3 to 2. Between each step make
sure to wait for the cluster to become green again, and check with
`curl localhost:9200/_cat/nodes` that you see the correct amount of master
nodes. During this process we will always make sure to keep at least 2 master
nodes as to not lose quorum:

  ```
  kubectl scale statefulsets my-release-elasticsearch-master --replicas=2
  ```

* Now deploy a single new master so that we have 3 masters again. See
[master.yaml][] for the configuration:

  ```
  make master
  ```

* Scale down old masters to 1:

  ```
  kubectl scale statefulsets my-release-elasticsearch-master --replicas=1
  ```

* Edit the masters in [masters.yaml][] to 2 and redeploy:

  ```
  make master
  ```

* Scale down the old masters to 0:

  ```
  kubectl scale statefulsets my-release-elasticsearch-master --replicas=0
  ```

* Edit the [masters.yaml][] to have 3 replicas and remove the
`discovery.zen.ping.unicast.hosts` entry from `extraEnvs` then redeploy the
masters. This will make sure all 3 masters are running in the new cluster and
are pointing at each other for discovery:

  ```
  make master
  ```

* Remove the `discovery.zen.ping.unicast.hosts` entry from `extraEnvs` then
redeploy the data nodes to make sure they are pointing at the new masters:

  ```
  make data
  ```

* Deploy the client nodes:

  ```
  make client
  ```

* Update any processes that are talking to the existing client nodes and point
them to the new client nodes. Once this is done you can scale down the old
client nodes:

  ```
  kubectl scale deployment my-release-elasticsearch-client --replicas=0
  ```

* The migration should now be complete. After verifying that everything is
working correctly you can cleanup leftover resources from your old cluster.

[basic license]: https://www.elastic.co/subscriptions
[data.yaml]: https://github.com/elastic/helm-charts/blob/7.15/elasticsearch/examples/migration/data.yaml
[helm/charts]: https://github.com/helm/charts/tree/7.15/stable/elasticsearch
[master.yaml]: https://github.com/elastic/helm-charts/blob/7.15/elasticsearch/examples/migration/master.yaml
[restoring to a different cluster guide]: https://www.elastic.co/guide/en/elasticsearch/reference/6.8/modules-snapshots.html#_restoring_to_a_different_cluster
[rolling upgrades guide]: https://www.elastic.co/guide/en/elasticsearch/reference/6.8/rolling-upgrades.html
