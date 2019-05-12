import os
import json
import requests

from misc.const import (
    GENERIC_WEBHOOK_SECRET,
    SOURCE_REPOSITORY,
    PLUGIN_JOB_LABEL,
    PLUGIN_BUILD_CONFIG_LABEL,
    ENV_PLUGIN_CONFIG_FILE,
)
from misc.utils import get_param_from_key, get_param_from_os

PLUGIN_CONFIG_FILE = "./tensorflow_config.json"
LABELS = {
    PLUGIN_BUILD_CONFIG_LABEL: "tensorflow-build-image",
    PLUGIN_JOB_LABEL: "tensorflow-build-job",
}


def get_config():
    with open(PLUGIN_CONFIG_FILE) as f:
        data = json.load(f)
    return data


class TensorflowBuildPlugin:
    """TensorflowBuildPlugin. """

    def __init__(self, config_file=ENV_PLUGIN_CONFIG_FILE):
        self.config_file = get_param_from_os(config_file)
        self.config = self.get_config()

    def get_labels_dict(self):
        return LABELS

    def get_config(self):
        try:
            with open(self.config_file) as f:
                data = json.load(f)
                self.config = data
                return self.config
        except FileNotFoundError as exc:
            raise FileNotFoundError("Unable to get plugin config file") from exc

    def fill_imagestream_template(self, ims_name):
        imagestream = {
            "kind": "ImageStream",
            "apiVersion": "image.openshift.io/v1",
            "metadata": {
                "name": ims_name,
                "labels": {"appTypes": "tensorflow-build-image", "appName": ims_name},
            },
            "spec": {"lookupPolicy": {"local": True}},
        }
        return imagestream

    def fill_buildconfig_template1(
        self, build_name, docker_file_path, nb_python_ver, image_details
    ):
        config_copy = self.config.copy()
        config_copy.update(image_details)
        config_copy["SESHETA_GITHUB_ACCESS_TOKEN"] = os.getenv(
            "SESHETA_GITHUB_ACCESS_TOKEN"
        )
        new_param_dict = config_copy
        buildconfig = {
            "kind": "BuildConfig",
            "apiVersion": "build.openshift.io/v1",
            "metadata": {
                "name": build_name,
                "labels": {"appTypes": "tensorflow-build-image", "appName": build_name},
            },
            "spec": {
                "triggers": [
                    {"type": "ConfigChange"},
                    {"type": "ImageChange"},
                    {
                        "type": "Generic",
                        "generic": {
                            "secret": get_param_from_key(
                                "GENERIC_WEBHOOK_SECRET", new_param_dict
                            ),
                            "allowEnv": True,
                        },
                    },
                ],
                "affinity": {
                    "nodeAffinity": {
                        "requiredDuringSchedulingIgnoredDuringExecution": {
                            "nodeSelectorTerms": [
                                {
                                    "matchExpressions": [
                                        {
                                            "key": "processor",
                                            "operator": "In",
                                            "values": [
                                                "Intel-Xeon-Processor-Skylake-IBRS"
                                            ],
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                },
                "source": {
                    "type": "Git",
                    "git": {
                        "uri": get_param_from_key("SOURCE_REPOSITORY", new_param_dict),
                        "ref": "master",
                    },
                },
                "strategy": {
                    "type": "Docker",
                    "dockerStrategy": {
                        "noCache": True,
                        "dockerfilePath": docker_file_path,
                        "from": {
                            "kind": "DockerImage",
                            "name": get_param_from_key("S2I_IMAGE", new_param_dict),
                        },
                        "env": [
                            {"name": "NB_PYTHON_VER", "value": nb_python_ver},
                            {
                                "name": "BAZEL_VERSION",
                                "value": get_param_from_key(
                                    "BAZEL_VERSION", new_param_dict
                                ),
                            },
                        ],
                    },
                },
                "output": {
                    "to": {
                        "kind": "ImageStreamTag",
                        "name": build_name
                        + ":"
                        + get_param_from_key("VERSION", new_param_dict),
                    }
                },
                "resources": {
                    "limits": {
                        "cpu": get_param_from_key(
                            "RESOURCE_LIMITS_CPU", new_param_dict
                        ),
                        "memory": get_param_from_key(
                            "RESOURCE_LIMITS_MEMORY", new_param_dict
                        ),
                    },
                    "requests": {
                        "cpu": get_param_from_key(
                            "RESOURCE_LIMITS_CPU", new_param_dict
                        ),
                        "memory": get_param_from_key(
                            "RESOURCE_LIMITS_MEMORY", new_param_dict
                        ),
                    },
                },
                "successfulBuildsHistoryLimit": 2,
                "failedBuildsHistoryLimit": 2,
            },
        }
        return buildconfig

    def fill_job_template1(
        self, application_name, builder_imagestream, nb_python_ver, image_details
    ):
        config_copy = self.config.copy()
        config_copy.update(image_details)
        new_param_dict = config_copy
        job = {
            "kind": "Job",
            "apiVersion": "batch/v1",
            "metadata": {
                "name": application_name,
                "labels": {
                    "appTypes": "tensorflow-build-job",
                    "appName": application_name,
                },
            },
            "spec": {
                "backoffLimit": get_param_from_key("JOB_BACKOFF_LIMIT", new_param_dict),
                "template": {
                    "metadata": {
                        "labels": {
                            "appTypes": "tensorflow-build-job",
                            "deploymentconfig": application_name,
                            "appName": application_name,
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "env": [
                                    {
                                        "name": "CUSTOM_BUILD",
                                        "value": get_param_from_key(
                                            "CUSTOM_BUILD", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "BUILD_OPTS",
                                        "value": get_param_from_key(
                                            "BUILD_OPTS", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_CUDA_VERSION",
                                        "value": get_param_from_key(
                                            "TF_CUDA_VERSION", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_CUDA_COMPUTE_CAPABILITIES",
                                        "value": get_param_from_key(
                                            "TF_CUDA_COMPUTE_CAPABILITIES",
                                            new_param_dict,
                                        ),
                                    },
                                    {
                                        "name": "TF_CUDNN_VERSION",
                                        "value": get_param_from_key(
                                            "TF_CUDNN_VERSION", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_OPENCL_SYCL",
                                        "value": get_param_from_key(
                                            "TF_NEED_OPENCL_SYCL", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_CUDA_CLANG",
                                        "value": get_param_from_key(
                                            "TF_CUDA_CLANG", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "GCC_HOST_COMPILER_PATH",
                                        "value": get_param_from_key(
                                            "GCC_HOST_COMPILER_PATH", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "CUDA_TOOLKIT_PATH",
                                        "value": get_param_from_key(
                                            "CUDA_TOOLKIT_PATH", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "CUDNN_INSTALL_PATH",
                                        "value": get_param_from_key(
                                            "CUDNN_INSTALL_PATH", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_JEMALLOC",
                                        "value": get_param_from_key(
                                            "TF_NEED_JEMALLOC", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_GCP",
                                        "value": get_param_from_key(
                                            "TF_NEED_GCP", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_VERBS",
                                        "value": get_param_from_key(
                                            "TF_NEED_VERBS", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_HDFS",
                                        "value": get_param_from_key(
                                            "TF_NEED_HDFS", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_ENABLE_XLA",
                                        "value": get_param_from_key(
                                            "TF_ENABLE_XLA", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_OPENCL",
                                        "value": get_param_from_key(
                                            "TF_NEED_OPENCL", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_CUDA",
                                        "value": get_param_from_key(
                                            "TF_NEED_CUDA", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_MPI",
                                        "value": get_param_from_key(
                                            "TF_NEED_MPI", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_GDR",
                                        "value": get_param_from_key(
                                            "TF_NEED_GDR", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_S3",
                                        "value": get_param_from_key(
                                            "TF_NEED_S3", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_KAFKA",
                                        "value": get_param_from_key(
                                            "TF_NEED_KAFKA", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_OPENCL_SYCL",
                                        "value": get_param_from_key(
                                            "TF_NEED_OPENCL_SYCL", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_DOWNLOAD_CLANG",
                                        "value": get_param_from_key(
                                            "TF_DOWNLOAD_CLANG", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_SET_ANDROID_WORKSPACE",
                                        "value": get_param_from_key(
                                            "TF_SET_ANDROID_WORKSPACE", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_NEED_TENSORRT",
                                        "value": get_param_from_key(
                                            "TF_NEED_TENSORRT", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "NCCL_INSTALL_PATH",
                                        "value": get_param_from_key(
                                            "NCCL_INSTALL_PATH", new_param_dict
                                        ),
                                    },
                                    {"name": "NB_PYTHON_VER", "value": nb_python_ver},
                                    {
                                        "name": "BAZEL_VERSION",
                                        "value": get_param_from_key(
                                            "BAZEL_VERSION", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TF_GIT_BRANCH",
                                        "value": get_param_from_key(
                                            "TF_GIT_BRANCH", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "TEST_WHEEL_FILE",
                                        "value": get_param_from_key(
                                            "TEST_WHEEL_FILE", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "GIT_RELEASE_REPO",
                                        "value": get_param_from_key(
                                            "GIT_RELEASE_REPO", new_param_dict
                                        ),
                                    },
                                    {
                                        "name": "GIT_TOKEN",
                                        "value": get_param_from_key(
                                            "SESHETA_GITHUB_ACCESS_TOKEN",
                                            new_param_dict,
                                        ),
                                    },
                                ],
                                "affinity": {
                                    "nodeAffinity": {
                                        "requiredDuringSchedulingIgnoredDuringExecution": {
                                            "nodeSelectorTerms": [
                                                {
                                                    "matchExpressions": [
                                                        {
                                                            "key": "processor",
                                                            "operator": "In",
                                                            "values": [
                                                                "Intel-Xeon-Processor-Skylake-IBRS"
                                                            ],
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                },
                                "name": application_name,
                                "image": builder_imagestream,
                                "command": ["/entrypoint", "/usr/libexec/s2i/run"],
                                "resources": {
                                    "limits": {
                                        "cpu": get_param_from_key(
                                            "RESOURCE_LIMITS_CPU", new_param_dict
                                        ),
                                        "memory": get_param_from_key(
                                            "RESOURCE_LIMITS_MEMORY", new_param_dict
                                        ),
                                    },
                                    "requests": {
                                        "cpu": get_param_from_key(
                                            "RESOURCE_LIMITS_CPU", new_param_dict
                                        ),
                                        "memory": get_param_from_key(
                                            "RESOURCE_LIMITS_MEMORY", new_param_dict
                                        ),
                                    },
                                },
                            }
                        ],
                        "restartPolicy": "Never",
                    },
                },
            },
        }
        return job


def trigger_build(req_url, req_headers, namespace, build_resource):
    application_build_name = build_resource["metadata"]["name"]
    nb_python_ver = get_val_envlist(
        build_resource["spec"]["strategy"]["dockerStrategy"]["env"], "NB_PYTHON_VER"
    )
    bazel_version = get_val_envlist(
        build_resource["spec"]["strategy"]["dockerStrategy"]["env"], "BAZEL_VERSION"
    )
    trigger_payload = {
        "git": {"uri": SOURCE_REPOSITORY, "ref": "master"},
        "env": [
            {"name": "NB_PYTHON_VER", "value": nb_python_ver},
            {"name": "BAZEL_VERSION", "value": bazel_version},
        ],
    }
    # TODO donot hardcode GENERIC_WEBHOOK_SECRET
    build_trigger_api = "{}/apis/build.openshift.io/v1/namespaces/{}/buildconfigs/{}/webhooks/{}/generic".format(
        req_url, namespace, application_build_name, GENERIC_WEBHOOK_SECRET
    )
    build_trigger_response = requests.post(
        build_trigger_api, json=trigger_payload, headers=req_headers, verify=False
    )
    print(
        "Status code for Build Webhook Trigger request: ",
        build_trigger_response.status_code,
    )
    if build_trigger_response.status_code == 200:
        return True
    else:
        print("Error for Build Webhook Trigger request: ", build_trigger_response.text)
        return False


def get_val_envlist(env_list, key):
    if len(env_list) == 0:
        return ""
    for mydict in env_list:
        if key in mydict.values():
            return mydict["value"]
