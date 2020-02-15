# Kubernetes

## 1. `minikube` and `kubctl`

For running a local kubernetes development cluster you will need to install `minikube`. Please follow the instructions [here](https://kubernetes.io/docs/tasks/tools/install-minikube/).

You will also need to install Kubernetes command line tool as shown [here](https://kubernetes.io/docs/tasks/tools/install-kubectl/).

## 2. Starting a Kubernetes cluster

You can either run a local cluster with minikube (ideal for development) or deploy your containers on the cloud (eg. Google Compute Platform).

**a) minikube**

To start `minikube` run:
```bash
minikube start --vm-driver virtualbox
```
While other drivers can be choosen `virtualbox` is currently working problem free on Mac.
Enable ingress:
```bash
minikube addons enable ingress
```
and control that your ingress pod is running:
```bash
kubectl get pods -n kube-system
```
If you need to stop and delete minikube run:
```bash
minikube stop && minikube delete
```

**b) Google Cloud Compute**

Start by installing Google Cloud SDK as shown [here](https://cloud.google.com/sdk/install).

Set a default porject:
```bash
gcloud config set project <project-id>
```
Set a default compute zone:
```bash
gcloud config set compute/zone <compute-zone>
```
Set a Google Kubernetes Engine (GKE) cluster:
```bash
gcloud container clusters get-credentials <cluster-name>
```

## 3. Deploy you App
If you need to get registry authorization to pull containers you will need to create a matching secret. eg.:
```bash
kubectl create secret docker-registry <secret name> --docker-server=<registry address> --docker-username=<registry user name> --docker-password=<registry password> --docker-email=<your associated email>
```
Create a secret for flaskis' mail account:
```bash
kubectl create secret generic gmailpass --from-literal=pass='<password>'
```
Create persistent volumes and persistent volumes claims for persistent data:
```bash
kubectl apply -f users-volume.yaml
kubectl apply -f users-volume-claim.yaml
kubectl apply -f db-volume.yaml
kubectl apply -f db-volume-claim.yaml
```
Use deployments to start your pods:
```bash
kubectl apply -f mariadb-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f server-deployment.yaml
```
This will start respective deployments and services. Services make sure that in case pod dies and a new one starts the address in use to contact the pod is not IP dependent.

Check that your pods and services are running:
```bash
kubectl get pods
kubectl get services
```
If you have problems starting a pod you can investigate a failing pod with:
```bash
kubectl describe pods <pod name>
```
To check the `stdout` of a running pod:
```bash
kubectl logs <pod name>
```
To enter a shell in a container:
```bash
kubectl exec -it <pod name> -- /bin/bash
```
To delete a pod:
```bash
kubectl delete pod <pod name>
```
To delete a deployment:
```bash
kubectl delete deployment <deployment name>
```
To delete a service:
```bash
kubectl delete service <service name>
```

## 4. Create an ingress

If you want to access your App from the web you will need to create an ingress.

**a) Deploy with self-signed key**

Create certificates:
```bash
export DOMAIN=<my domain name>
openssl req -x509 -newkey rsa:4096 -sha256 -nodes -keyout ${HOME}/tls_self.key -out ${HOME}/tls_self.crt -subj "/CN=*.${DOMAIN}" -days 365
SECRET_NAME=$(echo $DOMAIN | sed 's/\./-/g')-tls; echo $SECRET_NAME
kubectl create secret tls $SECRET_NAME --cert=${HOME}/tls_self.crt --key=${HOME}/tls_self.key
```

Edit the `nignx/server-ingress.yaml` accordingly:
```bash
spec:
  tls:
    - secretName: <SECRET_NAME>
      hosts:
        - '*.<DOMAIN>'
  rules:
  - host: <FLASKI WEB ADDRESS>
```
Apply the config:
```bash
kubectl apply -f nginx/nginx-config.yaml
```
Deploy nginx:
```bash
kubectl apply -f nginx/nginx-deployment.yaml
```
Apply the ingress:
```bash
kubectl apply -f nginx/nginx-ingress.yaml
```
You can now access you application over the given `<FLASKI WEB ADDRESS>`.

**b) Deploy on GKE with letsencrypt**

This section is based on a [digitalocean.com tutorial](https://www.digitalocean.com/community/tutorials/how-to-set-up-an-nginx-ingress-with-cert-manager-on-digitalocean-kubernetes).

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.26.1/deploy/static/mandatory.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.26.1/deploy/static/provider/cloud-generic.yaml
```
Check that your pods are running:
```bash
kubectl get pods --all-namespaces -l app.kubernetes.io/name=ingress-nginx
```
Get your App's external IP:
```bash
kubectl get svc --namespace=ingress-nginx
```
Create a name space for the certificate manager:
```bash
kubectl create namespace cert-manager
```
Deploy the certificate manager:
```bash
kubectl apply --validate=false -f https://github.com/jetstack/cert-manager/releases/download/v0.12.0/cert-manager.yaml
```
Check that the pods are running:
```bash
kubectl get pods --namespace cert-manager
```
Edit `letsencrytp/staging_issuer.yaml` with your email address:
```bash
email: <email address>
```
Create the ClusterIssuer:
```bash
kubectl create -f letsencrypt/staging_issuer.yaml
```
Edit `letsencrypt/server-ingress.yaml` in `staging` modus:
```bash
apiVersion: networking.k8s.io/v1beta1 # for versions before 1.14 use extensions/v1beta1
kind: Ingress
metadata:
  name: server-ingress
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-staging"
spec:
  tls:
    - hosts:
      - '*.<DOMAIN>'
      secretName: server-tls
  rules:
  - host: <FLASKI WEB ADDRESS>
    http:
      paths:
        - backend:
            serviceName: server
            servicePort: 80
```
If you don't have a domain you can always use your IP's address as domain eg. `<IP>.nip.io` and subsequently as a Flaski address `flaski.<IP>.nip.io`. You can also comment out the `tls` block as well as the `cert-manager.io` entries to ty your App on `http` withouth tls.

Apply the ingress:
```bash
kubectl apply -f letsencrypt/server-ingress.yaml
```
Check the ingress and the certificate:
```bash
kubectl describe ingress
kubectl describe certificate
```
On the output of the last command you expect to see:
```bash
Normal  Issued        47s    cert-manager  Certificate issued successfully
```
On the headers of your page
```bash
wget --save-headers -O- <FLASKI WEB ADDRESS>
```
you expect to see
```
. . .
HTTP request sent, awaiting response... 308 Permanent Redirect
. . .
ERROR: cannot verify echo1.example.com's certificate, issued by ‘CN=Fake LE Intermediate X1’:
  Unable to locally verify the issuer's authority.
To connect to echo1.example.com insecurely, use `--no-check-certificate'.
```
This indicates that HTTPS has successfully been enabled, but the certificate cannot be verified as it’s a fake temporary certificate issued by the Let’s Encrypt staging server.

Edit `letsencrytp/prod_issuer.yaml` with your email address:
```bash
email: <email address>
```
Create the ClusterIssuer:
```bash
kubectl create -f letsencrypt/prod_issuer.yaml
```
Edit `letsencrypt/server-ingress.yaml` in `production` modus:
```bash
apiVersion: networking.k8s.io/v1beta1 # for versions before 1.14 use extensions/v1beta1
kind: Ingress
metadata:
  name: server-ingress
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
    - hosts:
      - '*.<DOMAIN>'
      secretName: server-tls
  rules:
  - host: <FLASKI WEB ADDRESS>
    http:
      paths:
        - backend:
            serviceName: server
            servicePort: 80
```
Apply the ingress:
```bash
kubectl apply -f letsencrypt/server-ingress.yaml
```
And check the status of your certificate:
```bash
kubectl describe certificate server-tls
```
You should see
```
  Normal  Issued        10s (x2 over 6m45s)  cert-manager  Certificate issued successfully
```
Use `curl` to verify that HTTPS is working correctly:
```bash
curl <FLASKI WEB ADDRESS>
```
where you should see:
```bash
<html>
<head><title>308 Permanent Redirect</title></head>
<body>
<center><h1>308 Permanent Redirect</h1></center>
<hr><center>nginx/1.15.9</center>
</body>
</html>
```
and finally 
```bash
curl https://<FLASKI WEB ADDRESS>
```





