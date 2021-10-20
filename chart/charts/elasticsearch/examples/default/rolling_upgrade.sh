#!/usr/bin/env bash -x

kubectl proxy || true &

make &
PROC_ID=$!

while kill -0 "$PROC_ID" >/dev/null 2>&1; do
    echo "PROCESS IS RUNNING"
    if curl --fail 'http://localhost:8001/api/v1/proxy/namespaces/default/services/elasticsearch-master:9200/_search' ; then
        echo "cluster is healthy"
    else
        echo "cluster not healthy!"
        exit 1
    fi
    sleep 1
done
echo "PROCESS TERMINATED"
exit 0
