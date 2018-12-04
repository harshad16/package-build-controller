import urllib3
import requests
import logging
import openshift


def get_imagestream_endp(req_url, namespace, imagestream=None):
    if imagestream:
        return '{}/apis/image.openshift.io/v1/namespaces/{}/imagestreams/{}'.\
            format(req_url, namespace, imagestream)
    else:
        return '{}/apis/image.openshift.io/v1/namespaces/{}/imagestreams'.\
            format(req_url, namespace)


def get_buildconfig_endp(req_url, namespace, build_config_name=None):
    if build_config_name:
        return '{}/apis/build.openshift.io/v1/namespaces/{}/buildconfigs/{}'.\
            format(req_url, namespace, build_config_name)
    else:
        return '{}/apis/build.openshift.io/v1/namespaces/{}/buildconfigs'.\
            format(req_url, namespace)


def get_build_endp(req_url, namespace, build_name):
    return '{}/apis/build.openshift.io/v1/namespaces/{}/builds/{}'.format(req_url,
                                                                          namespace,
                                                                          build_name)


def get_imagestream1(ocp_client, namespace, imagestream):
    try:
        response = ocp_client.resources.get(api_version='image.openshift.io/v1', kind='ImageStream')\
            .get(namespace=namespace, name=imagestream)
        return True, response
    except openshift.dynamic.exceptions.NotFoundError as exc:
        return False, exc


def get_imagestream(req_url, req_headers, namespace, imagestream_name):
    endpoint = get_imagestream_endp(req_url, namespace, imagestream_name)
    respose = requests.get(endpoint, headers=req_headers, verify=False)
    if respose.status_code == 200:
        return True, respose.json()
    else:
        logging.error("Error for imagestream GET request: ".format(respose.json()))
        return False, respose.json()


def create_imagestream(req_url, req_headers, namespace, imagestream):
    endpoint = get_imagestream_endp(req_url, namespace)
    response = requests.post(endpoint, json=imagestream, headers=req_headers, verify=False)
    # print("Status code for imagestream POST request: ", response.status_code)
    if response.status_code == 201:
        return True
    else:
        print("Error for imagestream POST request: ", response.text)
        return False


def get_buildconfig(req_url, req_headers, namespace, build_config_name):
    endpoint = get_buildconfig_endp(req_url, namespace, build_config_name)
    response = requests.get(endpoint, headers=req_headers, verify=False)
    # logging.debug("Status code for BuildConfig GET request: {}".format(response.json()))
    if response.status_code == 200:
        return True, response.json()
    else:
        logging.error("Error for Buildconfig GET request: {}".format(response.json()))
        return False, response.json()


def create_buildconfig(req_url, req_headers, namespace, build_config):
    endpoint = get_buildconfig_endp(req_url, namespace)
    response = requests.post(endpoint, json=build_config, headers=req_headers, verify=False)
    logging.debug("Status code for Buildconfig POST request: {}".format(response.json()))
    if response.status_code in [200, 201]:
        return True
    else:
        logging.error("Error for Buildconfig POST request: {}".format(response.json))
        return False


def delete_build(req_url, req_headers, namespace):
    endpoint = get_buildconfig_endp(req_url, namespace)
    response = requests.delete(endpoint, headers=req_headers, verify=False)
    print("Status code for Buildconfig POST request: ", response.json())
    if response.status_code in [200, 201]:
        return True
    else:
        print("Error for Buildconfig POST request: ", response.text)
        return False


def get_build_logs(req_url, req_headers, namespace, build_pod):
    build_pod_endpoint = '{}/api/v1/namespaces/{}/pods/{}/log'.format(req_url, namespace, build_pod)
    response = requests.get(build_pod_endpoint, headers=req_headers, verify=False)
    # logging.debug("Status code for Build Pod log GET request: {}".format(response.json()))
    if response.status_code == 200:
        with open('{}.txt'.format(build_pod), 'w') as f:
            f.write(response.text)
        logging.debug("Log of {} {}".format(build_pod, response.text))
        return True, response.text
    else:
        logging.error("Error for build pod log GET request: ".format(response.text))
        return False, response.text


def get_latest_build(req_url, req_headers, namespace, build_config_name):
    endpoint = get_buildconfig_endp(req_url, namespace, build_config_name)
    response = requests.get(endpoint, headers=req_headers, verify=False)
    # logging.debug("Status code for latest Buildconfig GET request: {}".format(response.json()))
    if 'status' in response.json():
        response = response.json()
        if 'code' in response and response['code'] == 404:
            return "0"

        latest_build_status = response["status"]
        # logging.debug(response.json())
        # print(latest_build_status)
        return latest_build_status['lastVersion']
    else:
        return "0"


def get_build(req_url, req_headers, namespace, build_name):
    endpoint = get_build_endp(req_url, namespace, build_name)
    response = requests.get(endpoint, headers=req_headers, verify=False)
    # logging.debug("Status code for Build GET request: {}".format(response.json()))
    if response.status_code == 200:
        return True, response.json()
    else:
        # logging.error("Error for Build GET request: {}".format(response.json()))
        return False, response.json()


def get_status_build(req_url, req_headers, namespace, build_name):
    endpoint = get_build_endp(req_url, namespace, build_name)
    response = requests.get(endpoint, headers=req_headers, verify=False)
    logging.debug("Status code for latest Build's GET request: {}".format(response.json()))
    if 'status' in response.json():
        response = response.json()
        if 'code' in response and response['code'] == 404:
            return "0"
        build_status = response.get('status')
        # logging.debug(response.json())
        return build_status
    else:
        return "0"


if __name__ == '__main__':
    urllib3.disable_warnings()
    # get_buildconfig(OCP_URL, HEADERS, DEFAULT_NAMESPACE, "tf-fedora27-build-image-27")
    # get_latest_build(OCP_URL, HEADERS, NAMESPACE, "tf-fedora27-build-image-27")
