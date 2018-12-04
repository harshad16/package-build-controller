
# OCP Connection
DEFAULT_QUOTA_NAME = "thoth-prod-tensorflow-quota"
DEFAULT_NAMESPACE = 'thoth-prod-tensorflow'  # set default inplace default quotes
DEFAULT_IMAGE_VERSION = "1"
DEFAULT_NAMESPACE_FILE = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
SERVICE_TOKEN_FILENAME = '/var/run/secrets/kubernetes.io/serviceaccount/token'
SERVICE_CERT_FILENAME = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'

ENV_NAMESPACE_FILE = "NAMESPACE_FILE"

# TODO remove these 2
GENERIC_WEBHOOK_SECRET = "tf-build-secret"
SOURCE_REPOSITORY = "https://github.com/thoth-station/tensorflow-build-s2i.git"


# Resource Quota
MIN_CPU = 6
MIN_MEMORY = "10Gi"


RESOURCE_LIMITS_CPU = MIN_CPU
RESOURCE_LIMITS_MEMORY = MIN_MEMORY
BUFFER_RESOURCE_LIMITS_MEMORY = "2Gi"
BUFFER_RESOURCE_LIMITS_CPU = "1"


OPENSHIFT="oapi"
KUBE="api"
SCHEMA = [{"kind": "Builds", "type": "builds", "api": OPENSHIFT},
          {"kind": "DeploymentConfig", "type": "deploymentconfigs", "api": OPENSHIFT},
          {"kind": "Endpoints", "type": "endpoints", "api": KUBE},
          {"kind": "Events", "type": "events", "api": KUBE},
          {"kind": "Group", "type": "groups", "api": OPENSHIFT},
          {"kind": "Job", "type": "jobs", "api": KUBE},
          {"kind": "Image", "type": "images", "api": OPENSHIFT},
          {"kind": "ImageStream", "type": "imagestreams", "api": OPENSHIFT },
          {"kind": "ImageStreamImage", "type": "imagestreamimages", "api": OPENSHIFT},
          {"kind": "ImageStreamTag", "type": "imagestreamtags", "api": OPENSHIFT},
          {"kind": "LocalResourceAccessReview", "type": "localresourceaccessreviews", "api": OPENSHIFT},
          {"kind": "Namespace", "type": "namespaces", "api": KUBE},
          {"kind": "Node", "type": "nodes", "api": KUBE},
          {"kind": "Pod", "type": "pods", "api": KUBE},
          {"kind": "PolicyBinding", "type": "policybindings", "api": OPENSHIFT},
          {"kind": "RoleBinding", "type": "rolebindings", "api": OPENSHIFT},
          {"kind": "Route", "type": "routes", "api": OPENSHIFT},
          {"kind": "PersistentVolume", "type": "persistentvolumes", "api": KUBE},
          {"kind": "PersistentVolumeClaim", "type": "persistentvolumeclaims", "api": KUBE},
          {"kind": "Project", "type": "projects", "api": OPENSHIFT},
          {"kind": "ProjectRequest", "type": "projectrequests", "api": OPENSHIFT },
          {"kind": "ReplicationController", "type": "replicationcontrollers", "api": KUBE},
          {"kind": "Service", "type": "services", "api": KUBE },
          {"kind": "SubjectAccessReview", "type": "subjectaccessreviews", "api": OPENSHIFT},
          {"kind": "User", "type": "users", "api": OPENSHIFT}]


#GLOBAL

PROCESS_RESOURCES = [ "Build", "Job"]
PLUGIN_JOB_LABEL = "JOB_LABEL"
PLUGIN_BUILD_CONFIG_LABEL = "BUILD_CONFIG_LABEL"
ENV_PLUGIN_CONFIG_FILE = "ENV_PLUGIN_CONFIG_FILE"
ENV_BUILD_MAP = 'BUILD_MAP'