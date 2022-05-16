# MariaDB

## 1. Choosing setup

We are running MariaDB with galera master master setup. This provides the right size and funktions we need for running flaski.

The most simple way to to set this up is through bitnami helm chart.

## 2. Install bitnami/mariadb-galera

Create a namespace for your installation like `galera-dev`.
Populate the passwords in values.yaml then:

```bash
$ helm repo add bitnami https://charts.bitnami.com/bitnami
$ helm install -f values.yaml galeradev bitnami/mariadb-galera -n galeradev
```

See resulting output for using your mariadb-galera setup

```bash
NAME: galeradev
LAST DEPLOYED: Mon May  9 14:32:29 2022
NAMESPACE: galeradev
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
CHART NAME: mariadb-galera
CHART VERSION: 7.1.8
APP VERSION: 10.6.7

** Please be patient while the chart is being deployed **
Tip:

  Watch the deployment status using the command:

    kubectl get sts -w --namespace galeradev -l app.kubernetes.io/instance=galeradev

MariaDB can be accessed via port "3306" on the following DNS name from within your cluster:

    galeradev-mariadb-galera.galera-dev.svc.cluster.local

To obtain the password for the MariaDB admin user run the following command:

    echo "$(kubectl get secret --namespace galeraddev galeradev-mariadb-galera -o jsonpath="{.data.mariadb-root-password}" | base64 --decode)"

To connect to your database run the following command:

    kubectl run galeradev-mariadb-galera-client --rm --tty -i --restart='Never' --namespace galeradev --image docker.io/bitnami/mariadb-galera:10.6.4-debian-10-r31 --command \
      -- mysql -h galeradev-mariadb-galera -P3306 -uflaski -p$(kubectl get secret --namespace galeradev galeradev-mariadb-galera -o jsonpath="{.data.mariadb-password}" | base64 --decode) flaski

To upgrade this helm chart:

    helm upgrade --namespace galeradev galeradev bitnami/mariadb-galera \
      --set rootUser.password=$(kubectl get secret --namespace galeradev galeradev-mariadb-galera -o jsonpath="{.data.mariadb-root-password}" | base64 --decode) \
      --set db.user=flaski --set db.password=$(kubectl get secret --namespace galeradev galeradev-mariadb-galera -o jsonpath="{.data.mariadb-password}" | base64 --decode) --set db.name=flaski \
      --set galera.mariabackup.password=$(kubectl get secret --namespace galeradev galeradev-mariadb-galera -o jsonpath="{.data.mariadb-galera-mariabackup-password}" | base64 --decode) 
```

For more Information see the [Project Site](https://github.com/bitnami/charts/tree/master/bitnami/mariadb-galera)