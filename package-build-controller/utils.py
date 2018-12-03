import json
import os

from .const import SCHEMA


def load_json_file(file_name):
    d = "{}"
    with open(file_name) as json_data:
        d = json.load(json_data)
    return d


def check_none(x):
    if x is None or x == "":
        return False
    else:
        return True


def is_value_in_label(labels, value):
    if len(labels) == 0:
        return None
    if value in labels.values():
            return value
    else:
        return None


def get_value_in_label(labels, key):
    if len(labels) == 0:
        return None
    if key in labels.keys():
        return labels[key]
    else:
        return None


def get_build_status(status):
    """
    Different possible values for BUILD status:

        "status":"Failure"

        "status": {
            "completionTimestamp": "2018-11-20T06:04:19Z",
            "config": {
                "kind": "BuildConfig",
                "name": "tf-rhel75-build-image-27",
                "namespace": "thoth-prod-tensorflow"
            },
            "duration": 14000000000,
            "logSnippet": "p /usr/bin/pip; fi     \u0026\u0026 echo \"-----IMAGE_TEST--------\"  ...gy=standalone\" \u003e\u003e/etc/.bazelrc' returned a non-zero code: 1",
            "message": "Docker build strategy has failed.",
            "output": {},
            "outputDockerImageReference": "docker-registry.default.svc:5000/thoth-prod-tensorflow/tf-rhel75-build-image-27:1",
            "phase": "Failed",
            "reason": "DockerBuildFailed",
            "stages": [
                {
                    "durationMilliseconds": 2897,
                    "name": "FetchInputs",
                    "startTime": "2018-11-20T06:04:07Z",
                    "steps": [
                        {
                            "durationMilliseconds": 2897,
                            "name": "FetchGitSource",
                            "startTime": "2018-11-20T06:04:07Z"
                        }
                    ]
                },
                {
                    "durationMilliseconds": 6526,
                    "name": "Build",
                    "startTime": "2018-11-20T06:04:13Z",
                    "steps": [
                        {
                            "durationMilliseconds": 6526,
                            "name": "DockerBuild",
                            "startTime": "2018-11-20T06:04:13Z"
                        }
                    ]
                }
            ],
            "startTimestamp": "2018-11-20T06:04:05Z"
        }

    """
    if isinstance(status, str):
        # Should be status Object ex: NotFound
        return status
    elif isinstance(status, dict):
        return status.get("phase", None)
    else:
        # This is an Error.
        # TODO raise error, catch in caller
        return status



def get_job_status(status):
    """
    Different possible values for JOB status:

        "status":"Failure"

        'status': {}

        "status": {
            "active": 1,
            "startTime": "2018-11-19T00:10:43Z"
        }

        "status": {
            "active": 1,
            "failed": 3,
            "startTime": "2018-11-19T00:10:31Z"
        }

        "status": {
            "completionTime": "2018-10-23T15:21:18Z",
            "conditions": [
                {
                    "lastProbeTime": "2018-10-23T15:21:18Z",
                    "lastTransitionTime": "2018-10-23T15:21:18Z",
                    "status": "True",
                    "type": "Complete"
                }
            ],
            "startTime": "2018-10-23T15:12:04Z",
            "succeeded": 1
        }

        "status": {
            "conditions": [
                {
                    "lastProbeTime": "2018-11-19T00:21:35Z",
                    "lastTransitionTime": "2018-11-19T00:21:35Z",
                    "message": "Job has reach the specified backoff limit",
                    "reason": "BackoffLimitExceeded",
                    "status": "True",
                    "type": "Failed"
                }
            ],
            "failed": 5,
            "startTime": "2018-11-19T00:10:31Z"
        }
    """
    if isinstance(status, str):
        # Should be status Object ex: NotFound
        return status
    elif isinstance(status, dict):
        conditions = status.get("conditions", None)
        if conditions:
            type = conditions[0].get("type", None)
            if type == "Complete":
                return type
            else:
                reason = conditions[0].get("reason", None)
                # BackoffLimitExceeded
                return reason
        else:
            active = status.get("active", None)
            failed = status.get("failed", None)
            # Running or failing
            return "ACTIVE"
    else:
        # This is an Error.
        # TODO raise error, catch in caller
        return status


def flatten(lst):
    for x in lst:
        if isinstance(x, list):
            for xx in flatten(x):
                yield xx
        else:
            yield x


def get_api(typee):
    for x in flatten(SCHEMA):
        if x['type'] == typee:
            return x['api']


def get_kind(typee):
    for x in flatten(SCHEMA):
        if x['type'] == typee:
            return x['kind']


def get_param(param, param_dict,  default):
    try:
        # 1) all globals values maybe in the template.So pickup from environment
        return os.environ[param.upper()]
    except KeyError:
        if param_dict.get(param.upper()):
            # 2) get from config.json
            return param_dict.get(param.upper())
        else:
            if default:
                # 3) use the defauly value in constants.py
                return default
            else:
                raise KeyError("{} default value not defined in constant.py".format(param.upper()))


def name(obj, callingLocals=locals()):
    """
    quick function to print name of input
    """
    for k, v in list(callingLocals.items()):
        if v is obj:
            name = k
            return name
    return ""

