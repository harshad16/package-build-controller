
# OCP Connection
DEFAULT_QUOTA_NAME = "thoth-prod-tensorflow-quota"
NAMESPACE = 'thoth-prod-tensorflow'  # set default inplace default quotes
OCP_URL = ''
ACCESS_TOKEN = ''
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer {}'.format(ACCESS_TOKEN),
    'Accept': 'application/json',
    'Connection': 'close'
}

# Resource Quota
MIN_CPU = 6
MIN_MEMORY = "10Gi"
RESOURCE_QUOTA = "1"
QUOTA_NAME = DEFAULT_QUOTA_NAME
RESOURCE_LIMITS_CPU = MIN_CPU
RESOURCE_LIMITS_MEMORY = MIN_MEMORY
BUFFER_RESOURCE_LIMITS_MEMORY = "2Gi"
BUFFER_RESOURCE_LIMITS_CPU = "1"


# Buildconfig and Imagestream
GENERIC_WEBHOOK_SECRET = 'tf-build-secret'
SOURCE_REPOSITORY = 'https://github.com/thoth-station/tensorflow-build-s2i.git'
BAZEL_VERSION = '0.15.0'
VERSION = '1'
S2I_IMAGE = None


# Job
CUSTOM_BUILD = "bazel build --copt=-mavx --copt=-mavx2 --copt=-mfma" \
                         " --copt=-march=nocona  --copt=-mtune=haswell" \
                         " --copt=-ftree-vectorize --copt=-fPIC --copt=-fstack-protector-strong " \
                         " --copt=-fno-plt  --copt=-O2  --cxxopt=-fvisibility-inlines-hidden " \
                         " --cxxopt=-fmessage-length=0  --linkopt=-zrelro  --linkopt=-znow " \
                         " --copt=-mfpmath=both  --local_resources 4096,4.0,1.0  --cxxopt='-D_GLIBCXX_USE_CXX11_ABI=0' " \
                         " --verbose_failures  //tensorflow/tools/pip_package:build_pip_package"
BUILD_OPTS = " " #always give single space
TF_CUDA_VERSION = "9.2"
TF_CUDA_COMPUTE_CAPABILITIES = '3.0,3.5,5.2,6.0,6.1,7.0'
TF_CUDNN_VERSION = "7"
CUDA_TOOLKIT_PATH = "/usr/local/cuda"
CUDNN_INSTALL_PATH = "/usr/local/cuda"
GCC_HOST_COMPILER_PATH = "/usr/bin/gcc"
TF_NEED_OPENCL_SYCL = "0"
TF_CUDA_CLANG = "0"
TF_NEED_JEMALLOC = "1"
TF_NEED_GCP = "0"
TF_NEED_VERBS = "0"
TF_NEED_HDFS = "0"
TF_ENABLE_XLA = "0"
TF_NEED_OPENCL = "0"
TF_NEED_CUDA = "0"
TF_NEED_MPI = "0"
TF_NEED_GDR = "0"
TF_NEED_S3 = "0"
TF_NEED_KAFKA = "0"
TF_NEED_OPENCL_SYCL = "0"
TF_DOWNLOAD_CLANG = "0"
TF_SET_ANDROID_WORKSPACE = "0"
TF_NEED_TENSORRT = "0"
NCCL_INSTALL_PATH = "/usr/local/nccl-2.2"
TEST_WHEEL_FILE = "y"
TF_GIT_BRANCH = "r1.10"
SESHETA_GITHUB_ACCESS_TOKEN = ""
GIT_RELEASE_REPO = "https://github.com/sub-mod/tensorflow-wheels.git"


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
TENSORFLOW_BUILD_IMAGE = "tensorflow-build-image"
TENSORFLOW_BUILD_JOB = "tensorflow-build-job"

#GLOBAL
JOB_BACKOFF_LIMIT = 1
PROCESS_RESOURCES = [ "Build", "Job"]