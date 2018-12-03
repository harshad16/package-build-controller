
# Packages
import urllib3
import requests
import logging
from .const import *


def get_job_endpoint(req_url, namespace, job_name=None):
    if job_name:
        return '{}/apis/batch/v1/namespaces/{}/jobs/{}'.format(req_url, namespace,
                                                               job_name)
    else:
        return '{}/apis/batch/v1/namespaces/{}/jobs'.format(req_url, namespace)


def get_job(req_url, req_headers, namespace, job_name=None):
    endpoint = get_job_endpoint(req_url, namespace, job_name)
    response = requests.get(endpoint, headers=req_headers, verify=False)
    #print("Status code for get_job GET request: ", response.json())
    if response.status_code == 200:
        return True, response.json()
    else:
        #logging.error("Error for get_job GET request: {}".format(response.json()))
        return False, response.json()


def delete_job(req_url, req_headers, namespace, job_name):
    endpoint = get_job_endpoint(req_url, namespace, job_name)
    response = requests.delete(endpoint, headers=req_headers, verify=False)
    #print("Status code for job {} DELETE request: {}".format(job_name, response.json()))
    if response.status_code == 200:
        return True, response.json()
    else:
        print("Error for job DELETE request: ", response.text)
        return False, response.json()


# creates ajob from template
#
#  job = self.job_template(application_name=application_name,
#                         builder_imagesream=builder_imagesream,
#                         nb_python_ver=nb_python_ver)
def create_job(req_url, req_headers, namespace, job_name):
    endpoint = get_job_endpoint(req_url, namespace)
    response = requests.post(endpoint, json=job_name, headers=req_headers, verify=False)
    print("Status code for job {} POST request: {}".format(job_name, response.json()))
    if response.status_code == 201:
        return True
    else:
        print("Error for job POST request: ", response.text)
        return False


def update_job(req_url, req_headers, job, job_name):
    endpoint = get_job_endpoint(req_url, NAMESPACE, job_name)
    response = requests.post(endpoint, json=job, headers=req_headers, verify=False)
    print("Status code for job PUT request: ", response.json())
    if response.status_code == 200:
        return True
    else:
        print("Error for job PUT request: ", response.text)
        return False


def get_job_status(req_url, req_headers, namespace, job_name):
    endpoint = get_job_endpoint(req_url, namespace, job_name)
    response = requests.get(endpoint, headers=req_headers, verify=False)
    #print("get_job_status GET request: ", response.json())
    if response.status_code == 200:
        job_details = response.json().get('status')
        # tODO use the method to get correct job state
        print('Job Status: ', job_details)
        if job_details and 'active' in job_details:
            return True, response.json()
        else:
            return False, response.json()
    else:
        print("Error for job GET request: ", response.text)
        return False, response.json()


if __name__ == '__main__':
    urllib3.disable_warnings()
    get_job(OCP_URL, HEADERS, NAMESPACE, job_name="tf-fedora27-build-job-27")


