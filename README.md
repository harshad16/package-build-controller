# Package-build-controller
Openshift controller to Build tensorflow, numpy packages

## Deployment

Using OpenShift Templates and Ansible playbooks package-Build-controller can be easily deployed to any OpenShift cluster.   
Steps to following:  
 - Make sure serviceaccount `package-build-controller` is setup in the cluster to manage the package-build-controller operations.  
   oc command to setup sa: `oc create sa package-build-controller`
 - Make sure serviceaccount has edit access right in the cluster.  
   oc command to setup policy: `oc policy add-role-to-user edit system:serviceaccount:<namespace/project>:package-build-controller`
 - Deploy the package-build-controller:
   ```
   ansible-playbook --extra-vars "OCP_URL=<openshift-host-cluster-url>
   OCP_TOKEN=<openshift-login-token>
   OCP_NAMESPACE=<openshift-namespace>
   SESHETA_GITHUB_ACCESS_TOKEN=<github-oauth-token>"
   playbooks/provision.yaml
   ```

## Setup Dev Environment

Before we can test locally, we need to install some dependencies and gather some information about our Cluster.

```
yum -y install libffi-devel
pip3 install requests pkiutils pyopenssl
```

Now, create a directory in which we store incluster configs.  
The directory name below coincides with the directory that would be mounted into a pod.  
Note:In Openshift following files are used by pods to make api calls.
```
/var/run/secrets/kubernetes.io/serviceaccount/namespace
/var/run/secrets/kubernetes.io/serviceaccount/token
/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

Endpoints are:
```
https://kubernetes.default.svc.cluster.local  
https://openshift.default.svc.cluster.local
```

```
oc login # Interactive step

# 1. Get Token
oc whoami -t > test/kubernetes.io/serviceaccount/token

# 2. Get OpenShift CA file
echo QUIT | openssl s_client -showcerts -connect <kubernetes-master-hostname>:8443 2>&1  | openssl x509 -text | sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' > test/kubernetes.io/serviceaccount/ca.crt

# 3. Get Namespace of the Pod
oc project -q > test/kubernetes.io/serviceaccount/namespace

```

Note: The token & namespace file should not have a new line at end of file.
