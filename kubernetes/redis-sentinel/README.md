# Redis

## 1. Choosing setup

We are running redis in sentinel mode. This provides the right size and funktions we need for running flaski.

The most simple way to to set this up is through bitnami helm chart.

## 2. Install bitnami/redis

Create a namespace for your installation like `redis-dev`.
Edit the password in values.yaml then

```bash
$ helm repo add bitnami https://charts.bitnami.com/bitnami
$ helm install -f values.yaml redis-dev bitnami/redis -n redis-dev
```

See resulting output for using your redis sentinel

```bash
NAME: redisdev
LAST DEPLOYED: Tue Mar 29 12:40:26 2022
NAMESPACE: redisdev
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
CHART NAME: redis
CHART VERSION: 16.6.0
APP VERSION: 6.2.6

** Please be patient while the chart is being deployed **

Redis&trade; can be accessed via port 6379 on the following DNS name from within your cluster:

    redis-dev.redis-dev.svc.cluster.local for read only operations

For read/write operations, first access the Redis&trade; Sentinel cluster, which is available in port 26379 using the same domain name above.


To get your password run:
export REDIS_PASSWORD=$(kubectl get secret --namespace redis-dev redis-dev -o jsonpath="{.data.redis-password}" | base64 --decode)

To connect to your Redis&trade; server:

1. Run a Redis pod that you can use as a client:

   kubectl run --namespace redis-dev redis-client --restart='Never'  --env REDIS_PASSWORD=$REDIS_PASSWORD  --image docker.io/bitnami/redis:6.2.6-debian-10-r169 --command -- sleep infinity

   Use the following command to attach to the pod:

   kubectl exec --tty -i redis-client --namespace default -- bash

2. Connect using the Redis&trade; CLI:
   REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h 10.10.10.10 -p 6379 # Read only operations
   REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h redis-dev -p 26379 # Sentinel access

To connect to your database from outside the cluster execute the following commands:

    kubectl port-forward --namespace redis-dev svc/redis-dev 6379:6379 &
    REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h 127.0.0.1 -p 6379

I have no name!@redis-client:/$ REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h redis-dev.redis-dev.svc.cluster.local -p 6379
redis-dev.redis-dev.svc.cluster.local:6379> 
```
For more Information see the [Project Site](https://github.com/bitnami/charts/tree/master/bitnami/redis)