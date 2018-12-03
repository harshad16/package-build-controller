import logging
import time
import requests
from .const import OCP_URL, HEADERS, NAMESPACE, MIN_MEMORY, MIN_CPU


def process_quota(quota_name, quota_event, task_q):
    quota_available, avail_cpu, avail_mem = do_resource_requests_check(task_q, quota_name)
    if task_q.qsize() == 0:
        logging.debug('[{}] task_q empty. memory={}; cpu={}'.format(task_q.qsize(), avail_mem,
                                                                    avail_cpu))
        time.sleep(3)
        #event_is_set = quota_event.wait(2)
        #logging.debug('>> [{}] notify resource-thread:{}.'.format(task_q.qsize(), event_is_set))

    else:
        if not quota_available:
            # We are looping for new resources to be available
            event_is_set = quota_event.wait(2)
            logging.debug('[{}] Resources NOT available; memory={}; cpu={}'.format(task_q.qsize(),
                                                                                     avail_mem,
                                                                                     avail_cpu))
            logging.debug('>> [{}] notify resource-thread:{}.'.format(task_q.qsize(), event_is_set))

        else:
            # notify resource-thread
            quota_event.notifyAll()
            logging.debug('[{}] Resources available; memory={}; cpu={}'.format(task_q.qsize(), avail_mem,
                                                                                avail_cpu))
            logging.debug('>> [{}] notify resource-thread:True.'.format(task_q.qsize()))
            time.sleep(5)


def do_resource_requests_check(task_q, quota_name):
    if task_q.qsize() == 0:
        quota_available, avail_mem, avail_cpu = is_resource_available(req_url=OCP_URL,
                                                                     req_headers=HEADERS,
                                                                     namespace=NAMESPACE,
                                                                     quota_name=quota_name,
                                                                     resource_mem=0,
                                                                     resource_cpu=0)
        logging.debug('[{}] quota_available={}, avail_mem={}, avail_cpu={}'.format(task_q.qsize(),
                                                                                      quota_available,
                                                                                      avail_mem,
                                                                                      avail_cpu))
        return quota_available, avail_cpu, avail_mem
    else:
        item = task_q.queue[0]  # This is like peek() instead of qq.get()
        resource = item["object"]
        mem_requested = None
        cpu_requested = None
        avail_mem = None
        avail_cpu = None
        quota_available = True
        spec = None

        if resource and resource != "-1" and resource["kind"] == 'Job':
            # TODO a Job can have many containers. Find for each container.
            spec = resource["spec"]["template"]["spec"]['containers'][0]
        elif resource and resource != "-1" and resource["kind"] == 'BuildConfig':
            spec = resource.get("spec", None)

        if (spec and "resources" in spec
            and ("requests" in spec["resources"]) and
                (spec["resources"]["requests"]["cpu"] or spec["resources"]["requests"]["memory"])):
            mem_requested = spec["resources"]["limits"]["memory"]
            cpu_requested = spec["resources"]["limits"]["cpu"]
            logging.debug('[{}] mem_requested={}; cpu_requested={} by {} '.format(task_q.qsize(),
                                                                               mem_requested,
                                                                               cpu_requested,
                                                                               resource["metadata"]["name"]))
        if mem_requested and cpu_requested:
            quota_available, avail_mem, avail_cpu = is_resource_available(req_url=OCP_URL,
                                                                           req_headers=HEADERS,
                                                                           namespace=NAMESPACE,
                                                                           quota_name=quota_name,
                                                                           resource_mem=mem_requested,
                                                                           resource_cpu=cpu_requested)
            logging.debug('[{}] quota_available={}, avail_mem={}, avail_cpu={}'.format(task_q.qsize(),
                                                                                      quota_available,
                                                                                      avail_mem,
                                                                                      avail_cpu))
        return quota_available, avail_cpu, avail_mem


def is_resource_available(req_url, req_headers, namespace, quota_name,
                          resource_mem=MIN_MEMORY, resource_cpu=MIN_CPU):
    avail_mem, avail_cpu = get_avail_mem_cpu(req_url, req_headers, namespace, quota_name)

    if avail_mem == "0" and avail_cpu == "0":
        return False, avail_mem, avail_cpu
    if avail_mem == "" and avail_cpu == "":
        return False, avail_mem, avail_cpu

    available_mem_int = avail_mem - get_mem_gi_int(str(resource_mem)) #- get_mem_gi_int(str(BUFFER_RESOURCE_LIMITS_MEMORY))
    available_cpu_int = avail_cpu - get_cpu_int(str(resource_cpu)) #- get_cpu_int(str(BUFFER_RESOURCE_LIMITS_CPU))

    if available_mem_int >= 0 and available_cpu_int >= 0:
        return True, avail_mem, avail_cpu
    else:
        return False, avail_mem, avail_cpu


def get_avail_mem_cpu(req_url, req_headers, namespace, quota_name):
    avail_mem = 0
    avail_cpu = 0
    endpoint = getQuotaEndpoint(req_url, namespace, quota_name)
    response = requests.get(endpoint, headers=req_headers, verify=False)
    #print("Status code for resource quota GET request: ", response.status_code)
    if response.status_code == 200:
        #print("Resource Quota: ", response.json())
        if 'status' in response.json() and response.json().get('status'):
            quota = response.json().get('status')
            #print("Used Quota: \n CPU:{} \n Memory:{}".format(quota['used'].get("limits.cpu", ""),
            #                                                  quota['used'].get("limits.memory", "")))

            used_mem = quota['used'].get("limits.memory", "")
            used_cpu = quota['used'].get("limits.cpu", "")
            hard_mem = quota['hard'].get("limits.memory", "")
            hard_cpu = quota['hard'].get("limits.cpu", "")

            hard_mem_int = get_mem_gi_int(hard_mem)
            used_mem_int = get_mem_gi_int(used_mem)
            hard_cpu_int = get_cpu_int(str(hard_cpu))
            used_cpu_int = get_cpu_int(used_cpu)
            avail_mem = hard_mem_int - used_mem_int
            avail_cpu = hard_cpu_int - used_cpu_int
    return avail_mem, avail_cpu


def get_mem_gi_int(used_mem):
    """returns int Gi value"""
    used_mem_int = 0
    if 'Gi' in used_mem:
        used_mem_int = int(used_mem.strip('Gi'));
    elif 'Mi' in used_mem:
        used_mem_int = int(used_mem.strip('Mi')) * 0.001
    return used_mem_int


def get_cpu_int(used_cpu):
    used_int_cpu = 0
    if 'm' in used_cpu:
        used_int_cpu = int(used_cpu.strip('m')) * 0.001
    else:
        used_int_cpu = int(used_cpu.strip('m'))
    return used_int_cpu


def getQuotaEndpoint(reqURL, namespace, quotaName):
    if quotaName:
        return '{}/api/v1/namespaces/{}/resourcequotas/{}'.format(reqURL, namespace,
                                                                  quotaName)
    else:
        return '{}/api/v1/namespaces/{}/resourcequotas'.format(reqURL, namespace)

