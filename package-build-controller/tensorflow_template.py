import requests
from .const import *
from .utils import get_param


def fill_imagestream_template(ims_name):
    imagestream = {
        "kind": "ImageStream",
        "apiVersion": "image.openshift.io/v1",
        "metadata": {
            "name": ims_name,
            "labels": {
                "appTypes": "tensorflow-build-image",
                "appName": ims_name
            }
        },
        "spec": {
            "lookupPolicy": {
                "local": True
            }
        }
    }
    return imagestream


def fill_buildconfig_template(build_name, docker_file_path, nb_python_ver, image_details):
    buildconfig = {
        "kind": "BuildConfig",
        "apiVersion": "build.openshift.io/v1",
        "metadata": {
            "name": build_name,
            "labels": {
                "appTypes": "tensorflow-build-image",
                "appName": build_name
            }
        },
        "spec": {
            "triggers": [
                {
                    "type": "ConfigChange"
                },
                {
                    "type": "ImageChange"
                },
                {
                    "type": "Generic",
                    "generic": {
                        "secret": get_param("GENERIC_WEBHOOK_SECRET", image_details, GENERIC_WEBHOOK_SECRET),
                        "allowEnv": True
                    }
                }
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
                                        ]
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
                    "uri": get_param("SOURCE_REPOSITORY", image_details, SOURCE_REPOSITORY),
                    "ref": "master"
                }
            },
            "strategy": {
                "type": "Docker",
                "dockerStrategy": {
                    "noCache": True,
                    "dockerfilePath": docker_file_path,
                    "from": {
                        "kind": "DockerImage",
                        "name": get_param("S2I_IMAGE", image_details, None)
                    },
                    "env": [
                        {
                            "name": "NB_PYTHON_VER",
                            "value": nb_python_ver
                        },
                        {
                            "name": "BAZEL_VERSION",
                            "value":  get_param("BAZEL_VERSION", image_details, None)
                        }
                    ]
                }
            },
            "output": {
                "to": {
                    "kind": "ImageStreamTag",
                    "name": build_name + ":" + get_param("VERSION", image_details, VERSION)
                }
            },
            "resources": {
                "limits": {
                    "cpu": get_param("RESOURCE_LIMITS_CPU", image_details, RESOURCE_LIMITS_CPU),
                    "memory": get_param("RESOURCE_LIMITS_MEMORY", image_details, RESOURCE_LIMITS_MEMORY),
                },
                "requests": {
                    "cpu": get_param("RESOURCE_LIMITS_CPU", image_details, RESOURCE_LIMITS_CPU),
                    "memory": get_param("RESOURCE_LIMITS_MEMORY", image_details, RESOURCE_LIMITS_MEMORY),
                }
            },
            'successfulBuildsHistoryLimit': 2,
            'failedBuildsHistoryLimit': 2
        }
    }
    return buildconfig


def fill_job_template(application_name, builder_imagesream, nb_python_ver, image_details):
    job = {
        "kind": "Job",
        "apiVersion": "batch/v1",
        "metadata": {
            "name": application_name,
            "labels": {
                "appTypes": "tensorflow-build-job",
                "appName": application_name
            }
        },
        "spec": {
            "backoffLimit": get_param("JOB_BACKOFF_LIMIT", image_details, JOB_BACKOFF_LIMIT),
            "template": {
                "metadata": {
                    "labels": {
                        "appTypes": "tensorflow-build-job",
                        "deploymentconfig": application_name,
                        "appName": application_name
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "env": [
                                {
                                    "name": "CUSTOM_BUILD",
                                    "value": get_param("CUSTOM_BUILD", image_details, CUSTOM_BUILD)
                                },
                                {
                                    "name": "BUILD_OPTS",
                                    "value": get_param("BUILD_OPTS", image_details, BUILD_OPTS)
                                },
                                {
                                    "name": "TF_CUDA_VERSION",
                                    "value": get_param("TF_CUDA_VERSION", image_details, TF_CUDA_VERSION)
                                },
                                {
                                    "name": "TF_CUDA_COMPUTE_CAPABILITIES",
                                    "value": get_param("TF_CUDA_COMPUTE_CAPABILITIES", image_details, TF_CUDA_COMPUTE_CAPABILITIES)
                                },
                                {
                                    "name": "TF_CUDNN_VERSION",
                                    "value": get_param("TF_CUDNN_VERSION", image_details, TF_CUDNN_VERSION)
                                },
                                {
                                    "name": "TF_NEED_OPENCL_SYCL",
                                    "value": get_param("TF_NEED_OPENCL_SYCL", image_details, TF_NEED_OPENCL_SYCL)
                                },
                                {
                                    "name": "TF_CUDA_CLANG",
                                    "value": get_param("TF_CUDA_CLANG", image_details, TF_CUDA_CLANG)
                                },
                                {
                                    "name": "GCC_HOST_COMPILER_PATH",
                                    "value": get_param("GCC_HOST_COMPILER_PATH", image_details, GCC_HOST_COMPILER_PATH)
                                },
                                {
                                    "name": "CUDA_TOOLKIT_PATH",
                                    "value": get_param("CUDA_TOOLKIT_PATH", image_details, CUDA_TOOLKIT_PATH)
                                },
                                {
                                    "name": "CUDNN_INSTALL_PATH",
                                    "value": get_param("CUDNN_INSTALL_PATH", image_details, CUDNN_INSTALL_PATH)
                                },
                                {
                                    "name": "TF_NEED_JEMALLOC",
                                    "value": get_param("TF_NEED_JEMALLOC", image_details, TF_NEED_JEMALLOC)
                                },
                                {
                                    "name": "TF_NEED_GCP",
                                    "value": get_param("TF_NEED_GCP", image_details, TF_NEED_GCP)
                                },
                                {
                                    "name": "TF_NEED_VERBS",
                                    "value": get_param("TF_NEED_VERBS", image_details, TF_NEED_VERBS)
                                },
                                {
                                    "name": "TF_NEED_HDFS",
                                    "value": get_param("TF_NEED_HDFS", image_details, TF_NEED_HDFS)
                                },
                                {
                                    "name": "TF_ENABLE_XLA",
                                    "value": get_param("TF_ENABLE_XLA", image_details, TF_ENABLE_XLA)
                                },
                                {
                                    "name": "TF_NEED_OPENCL",
                                    "value": get_param("TF_NEED_OPENCL", image_details, TF_NEED_OPENCL)
                                },
                                {
                                    "name": "TF_NEED_CUDA",
                                    "value": get_param("TF_NEED_CUDA", image_details, TF_NEED_CUDA)
                                },
                                {
                                    "name": "TF_NEED_MPI",
                                    "value": get_param("TF_NEED_MPI", image_details, TF_NEED_MPI)
                                },
                                {
                                    "name": "TF_NEED_GDR",
                                    "value": get_param("TF_NEED_GDR", image_details, TF_NEED_GDR)
                                },
                                {
                                    "name": "TF_NEED_S3",
                                    "value": get_param("TF_NEED_S3", image_details, TF_NEED_S3)
                                },
                                {
                                    "name": "TF_NEED_KAFKA",
                                    "value": get_param("TF_NEED_KAFKA", image_details, TF_NEED_KAFKA)
                                },
                                {
                                    "name": "TF_NEED_OPENCL_SYCL",
                                    "value": get_param("TF_NEED_OPENCL_SYCL", image_details, TF_NEED_OPENCL_SYCL)
                                },
                                {
                                    "name": "TF_DOWNLOAD_CLANG",
                                    "value": get_param("TF_DOWNLOAD_CLANG", image_details, TF_DOWNLOAD_CLANG)
                                },
                                {
                                    "name": "TF_SET_ANDROID_WORKSPACE",
                                    "value": get_param("TF_SET_ANDROID_WORKSPACE", image_details, TF_SET_ANDROID_WORKSPACE)
                                },
                                {
                                    "name": "TF_NEED_TENSORRT",
                                    "value": get_param("TF_NEED_TENSORRT", image_details, TF_NEED_TENSORRT)
                                },
                                {
                                    "name": "NCCL_INSTALL_PATH",
                                    "value": get_param("NCCL_INSTALL_PATH", image_details, NCCL_INSTALL_PATH)
                                },
                                {
                                    "name": "NB_PYTHON_VER",
                                    "value": nb_python_ver
                                },
                                {
                                    "name": "BAZEL_VERSION",
                                    "value": get_param("BAZEL_VERSION", image_details, BAZEL_VERSION)
                                },
                                {
                                    "name": "TF_GIT_BRANCH",
                                    "value": get_param("TF_GIT_BRANCH", image_details, TF_GIT_BRANCH)
                                },
                                {
                                    "name": "TEST_WHEEL_FILE",
                                    "value": get_param("TEST_WHEEL_FILE", image_details, TEST_WHEEL_FILE)
                                },
                                {
                                    "name": "GIT_RELEASE_REPO",
                                    "value": get_param("GIT_RELEASE_REPO", image_details, GIT_RELEASE_REPO)
                                },
                                {
                                    "name": "GIT_TOKEN",
                                    "value": SESHETA_GITHUB_ACCESS_TOKEN
                                }
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
                                                        ]
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                }
                            },
                            "name": application_name,
                            "image": builder_imagesream,
                            "command": ["/entrypoint", "/usr/libexec/s2i/run"],
                            "resources": {
                                "limits": {
                                    "cpu": get_param("RESOURCE_LIMITS_CPU", image_details, RESOURCE_LIMITS_CPU),
                                    "memory": get_param("RESOURCE_LIMITS_MEMORY", image_details, RESOURCE_LIMITS_MEMORY),
                                },
                                "requests": {
                                    "cpu": get_param("RESOURCE_LIMITS_CPU", image_details, RESOURCE_LIMITS_CPU),
                                    "memory": get_param("RESOURCE_LIMITS_MEMORY", image_details, RESOURCE_LIMITS_MEMORY),
                                }
                            }
                        }
                    ],
                    "restartPolicy": "Never"
                }
            }
        }
    }
    return job


def trigger_build(req_url, req_headers, namespace, build_resource):
    application_build_name = build_resource["metadata"]["name"]
    nb_python_ver = get_val_envlist(build_resource["spec"]["strategy"]["dockerStrategy"]['env'], "NB_PYTHON_VER")
    bazel_version = get_val_envlist(build_resource["spec"]["strategy"]["dockerStrategy"]['env'], "BAZEL_VERSION")
    trigger_payload = {
        "git": {
            "uri": SOURCE_REPOSITORY,
            "ref": "master"
        },
        "env": [
            {
                "name": "NB_PYTHON_VER",
                "value": nb_python_ver
            },
            {
                "name": "BAZEL_VERSION",
                "value": bazel_version
            }
        ]
    }
    # TODO donot hardcode GENERIC_WEBHOOK_SECRET
    build_trigger_api = '{}/apis/build.openshift.io/v1/namespaces/{}/buildconfigs/{}/webhooks/{}/generic'.format(
        req_url,
        namespace,
        application_build_name,
        GENERIC_WEBHOOK_SECRET)
    build_trigger_response = requests.post(build_trigger_api, json=trigger_payload, headers=req_headers,
                                           verify=False)
    print("Status code for Build Webhook Trigger request: ", build_trigger_response.status_code)
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



