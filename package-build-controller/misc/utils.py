import json
import os
import threading
from .const import SCHEMA, DEFAULT_NAMESPACE_FILE, DEFAULT_NAMESPACE ,ENV_NAMESPACE_FILE,\
    SERVICE_TOKEN_FILENAME, SERVICE_CERT_FILENAME


def load_json_file(file_name):
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
            "logSnippet": "p /usr/bin/pip; fi     \u0026\u0026 echo \"-----IMAGE_TEST--------\"
                ...gy=standalone\" \u003e\u003e/etc/.bazelrc' returned a non-zero code: 1",
            "message": "Docker build strategy has failed.",
            "output": {},
            "outputDockerImageReference": "docker-registry.default.svc:5000/
                thoth-prod-tensorflow/tf-rhel75-build-image-27:1",
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
            ptype = conditions[0].get("type", None)
            if ptype == "Complete":
                return ptype
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

def get_json_from_file(pfile, default=None):
    try:
        # 1) open file and extract value
        with open(pfile, 'r') as f:
            return json.load(f)
    except FileNotFoundError as exc:
        if default:
            # 3) use the default value in constants.py
            return default
        else:
            raise KeyError("default value not defined & json file: {} has issue.".format(exc))

def get_param_from_file(pfile, default=None):
    try:
        # 1) open file and extract value
        with open(pfile, 'r') as f:
            return f.read()
    except FileNotFoundError as exc:
        if default:
            # 3) use the default value in constants.py
            return default
        else:
            raise KeyError("default value not defined & file: {} not found.".format(exc))


def get_param_from_os(param):
    try:
        return os.environ[param.upper()]
    except KeyError:
        raise KeyError("{} param not defined in env".format(param.upper()))


def get_param_from_key(param, param_dict):
    try:
        # 1) all globals values maybe in the template.So pickup from environment
        return os.environ[param.upper()]
    except KeyError:
        if param_dict and param_dict.get(param.upper()):
            # 2) get from config.json
            return param_dict.get(param.upper())
        else:
            raise KeyError("{} default value not defined in env or in dict".format(param.upper()))


def get_param(param, param_dict,  default):
    try:
        # 1) all globals values maybe in the template.So pickup from environment
        return os.environ[param.upper()]
    except KeyError:
        if param_dict and param_dict.get(param.upper()):
            # 2) get from config.json
            return param_dict.get(param.upper())
        else:
            if default:
                # 3) use the default value in constants.py
                return default
            else:
                raise KeyError("{} default value not defined in env or const.py".format(param.upper()))


def name(obj, calling_locals=locals()):
    """
    quick function to print name of input
    """
    for k, v in list(calling_locals.items()):
        if v is obj:
            pname = k
            return pname
    return ""


def _get_incluster_token_file(token_file=None):
    return token_file if token_file else SERVICE_TOKEN_FILENAME


def _get_incluster_ca_file(ca_file=None):
    return ca_file if ca_file else SERVICE_CERT_FILENAME


def get_namespace():
    namespace_file = get_param(param=ENV_NAMESPACE_FILE, param_dict=None, default=DEFAULT_NAMESPACE_FILE)
    namespace = get_param_from_file(namespace_file, DEFAULT_NAMESPACE)
    return namespace


def get_namespace1(nfile):
    """Get namespace from namespace file."""
    try:
        with open(nfile, 'r') as namespace:
            return namespace.read()
    except FileNotFoundError as exc:
        raise FileNotFoundError("Unable to get namespace from namespace file") from exc


def get_service_account_token():
    """Get token from service account token file."""
    try:
        with open(_get_incluster_token_file(), 'r') as token_file:
            return token_file.read()
    except FileNotFoundError as exc:
        raise FileNotFoundError("Unable to get service account token, please check "
                                "that service has service account assigned with exposed token") from exc


def get_header(api_key_dict):
    auth = api_key_dict["authorization"]
    header = {
        'Content-Type': 'application/json',
        'Authorization': auth,
        'Accept': 'application/json',
        'Connection': 'close'
    }
    return header


class ResourceCounter:
    """Thread-safe incrementing counter. """
    def __init__(self, initial=0):
        """Initialize a counter to given initial value (default 0)."""
        self.value = initial
        self._lock = threading.Lock()

    def decrement(self, num=1):
        """Decrement the counter by num (default 1) and return the
        new value.
        """
        with self._lock:
            self.value = self.value - num
            return self.value

    def increment(self, num=1):
        """Increment the counter by num (default 1) and return the
        new value.
        """
        with self._lock:
            self.value = self.value + num
            return self.value

    def get_val(self):
        """Get value.
        """
        with self._lock:
            return self.value

    def set_val(self, num):
        """Set value and return the new value.
        """
        with self._lock:
            self.value = num
            return self.value

    def __str__(self):
        """string representation of value
        """
        return str(self.value)
