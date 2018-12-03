import datetime
import json
import logging
import requests
import urllib3
from pybloom import BloomFilter
from misc.utils import get_api


def get_api_url(host, namespace, resource, bool_watch=True):
    if bool_watch:
        return "{}/{}/v1/namespaces/{}/{}?watch=true".format(host, get_api(resource), namespace, resource)
    else:
        return "{}/{}/v1/namespaces/{}/{}".format(host, get_api(resource), namespace, resource)


def test_endpoint(host, namespace, resource, sa_token, tls_verify=False):
    url = get_api_url(host, namespace, resource, bool_watch=False)
    print("test_endpoint url = {}".format(url))
    # TODO try catch remove https
    test_req = requests.Request("GET", url,
                                headers={'Authorization': 'Bearer {0}'.format(sa_token)},
                                params=""
                                ).prepare()
    session = requests.session()
    test_resp = session.send(test_req, verify=tls_verify)
    if test_resp.status_code != 200:
        raise Exception("Unable to contact OpenShift API at {0}. Message from server: {1}".format(url,
                                                                                                  test_resp.text))
    return test_resp


def stream(host, namespace, resource, sa_token, tls_verify=False):
    url = get_api_url(host, namespace, resource, bool_watch=True)
    print("stream url = {}".format(url))
    start = datetime.datetime.now()
    session = requests.Session()
    req = requests.Request("GET", url,
                           headers={'Authorization': 'Bearer {0}'.format(sa_token)},
                           params=""
                           ).prepare()

    resp = session.send(req, stream=True, verify=tls_verify)

    if resp.status_code != 200:
        raise Exception("Unable to contact OpenShift API at {0}. Message from server: {1}".format(url,
                                                                                                  resp.text))
    try:
        lines = resp.iter_lines() #chunk_size=1
        first_line = next(lines)
        for line in lines:
            if line:
                try:
                    yield json.loads(line.decode('utf-8')), 1
                    # TODO: Use the specific exception type here.
                    # TODO: Logging -> "No Json Object could be decoded."
                except Exception as e:
                    raise Exception("Watcher error 1: {0}".format(e))
        return json.loads("{}"), -1
    except Exception as e:
        raise Exception("Watcher error 2: {0}".format(e))
    finally:
        end = datetime.datetime.now()
        diff = end-start
        print("===================")
        print("ran for {} seconds ".format(diff.seconds))
        print("===================")


"""
{
  'type': 'ADDED',
  'object': {
    'kind': 'Event',
    'apiVersion': 'v1',
    'metadata': {
      'name': 'tf-rhel75-build-image-27-3-build.15668310d08c690d',
      'namespace': 'thoth-prod-tensorflow',
      'selfLink': '/api/v1/namespaces/thoth-prod-tensorflow/events/tf-rhel75-build-image-27-3-build.15668310d08c690d',
      'uid': 'af30e1ec-e6cf-11e8-af59-fa163e4a655d',
      'resourceVersion': '191774624',
      'creationTimestamp': '2018-11-12T23:07:10Z'
    },
    'involvedObject': {
      'kind': 'Pod',
      'namespace': 'thoth-prod-tensorflow',
      'name': 'tf-rhel75-build-image-27-3-build',
      'uid': 'a8abebe8-e6cf-11e8-b1ff-fa163ed2928c',
      'apiVersion': 'v1',
      'resourceVersion': '191774488',
      'fieldPath': 'spec.containers{docker-build}'
    },
    'reason': 'Started',
    'message': 'Started container',
    'source': {
      'component': 'kubelet',
      'host': 'cpt-0042.paas.prod.upshift.rdu2.redhat.com'
    },
    'firstTimestamp': '2018-11-12T23:07:10Z',
    'lastTimestamp': '2018-11-12T23:07:10Z',
    'count': 1,
    'type': 'Normal',
    'eventTime': None,
    'reportingComponent': '',
    'reportingInstance': ''
  }
}
"""
# we process All NEW events.
# never create any resources here


# if object is not seen before return False
# if object is seen before it return True





if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s")
    urllib3.disable_warnings()
    bloom = BloomFilter(10000, 0.001)

    # resp = test_endpoint(host=OCP_URL, sa_token=SA_TOKEN, namespace=NAMESPACE, resource="builds")
    # print(resp.json())


    # for event, x in stream(host=OCP_URL, sa_token=SA_TOKEN, namespace=NAMESPACE, resource="events"):
    #     if x!= -1:
    #         m, c = add_event(event=event)
    #         print(m , c)

    # for resource, x in stream(host=OCP_URL, sa_token=SA_TOKEN, namespace=NAMESPACE, resource="builds"):
    #     if x!= -1:
    #         m, c = add_resource(event=resource)
    #         print(m , c)

    #event_loop(bloom=bloom, resource="builds")