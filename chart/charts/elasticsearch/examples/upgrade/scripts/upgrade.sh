#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<-EOF
	USAGE:
	  $0 [--release <release-name>] [--from <elasticsearch-version>]
	  $0 --help

	OPTIONS:
	  --release <release-name>
	    Name of the Helm release to install
	  --from <elasticsearch-version>
	    Elasticsearch version to use for first install
	EOF
  exit 1
}

RELEASE="helm-es-upgrade"
FROM=""

while [[ $# -gt 0 ]]
do
  key="$1"

  case $key in
    --help)
      usage
    ;;
    --release)
      RELEASE="$2"
      shift 2
    ;;
    --from)
      FROM="$2"
      shift 2
    ;;
    *)
      log "Unrecognized argument: '$key'"
      usage
    ;;
  esac
done

if ! command -v jq > /dev/null
then
  echo 'jq is required to use this script'
  echo 'please check https://stedolan.github.io/jq/download/ to install it'
  exit 1
fi

# Elasticsearch chart < 7.4.0 are not compatible with K8S >= 1.16)
if [[ -z $FROM ]]
then
  KUBE_MINOR_VERSION=$(kubectl version -o json | jq --raw-output --exit-status '.serverVersion.minor' | sed 's/[^0-9]*//g')

  if [ "$KUBE_MINOR_VERSION" -lt 16 ]
  then
    FROM="7.0.0-alpha1"
  else
    FROM="7.4.0"
  fi
fi

helm repo add elastic https://helm.elastic.co

# Initial install
printf "Installing Elasticsearch chart %s\n" "$FROM"
helm upgrade --wait --timeout=600s --install "$RELEASE" elastic/elasticsearch --version "$FROM" --set clusterName=upgrade
kubectl rollout status sts/upgrade-master --timeout=600s

# Upgrade
printf "Upgrading Elasticsearch chart\n"
helm upgrade --wait --timeout=600s --set terminationGracePeriod=121 --install "$RELEASE" ../../ --set clusterName=upgrade
kubectl rollout status sts/upgrade-master --timeout=600s
