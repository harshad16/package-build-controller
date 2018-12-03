import logging
import os
import threading
import time
from queue import Queue

import urllib3
from pybloom import BloomFilter

from .resource_watch import stream
from .build import create_imagestream, get_imagestream
from .const import QUOTA_NAME, OCP_URL, ACCESS_TOKEN, NAMESPACE, VERSION, HEADERS
from .event_thread import event_loop_init, process_events
from .quota_thread import process_quota
from .resource_thread import process_taskq
from .tensorflow_template import fill_imagestream_template, fill_job_template, fill_buildconfig_template
from .utils import load_json_file, check_none

urllib3.disable_warnings()

CONFIG_FILE = "./config.json"


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


def create_resource(quota_avail_event, consumer_done, task_q, global_count, object_map):
    logging.info('STARTING...')
    _running = True
    while _running and True:
        logging.debug('<< {} waiting for quota-thread. G:{}'.format(task_q.qsize(), global_count))
        if task_q.qsize() == 0 and global_count.get_val() == 0:
            consumer_done.set()
            _running = False
            logging.debug('<< {} break loop-1. G:{}'.format(task_q.qsize(), global_count))
            break
        with quota_avail_event:
            quota_available = quota_avail_event.wait(2) # waiting from quota-thread
            logging.debug('<< {} waiting for quota-thread DONE. quota_available: {} G:{}'.format(task_q.qsize(),
                                                                                            quota_available,
                                                                                            global_count))

            if task_q.qsize() == 0 and global_count.get_val() == 0:
                consumer_done.set()
                _running = False
                logging.debug('<< {} break loop-2. G:{}'.format(task_q.qsize(), global_count))
                break
            if quota_available:
                logging.debug('{} processing STARTED.'.format(task_q.qsize()))
                # ================================
                process_taskq(task_q, global_count, object_map)
                # ================================
                time.sleep(2)
            else:
                #TODO EXIT when all resources are created successfully
                if task_q.qsize() == 0 and global_count.get_val() == 0:
                    consumer_done.set()
                    _running = False
                    logging.debug('<< {} break loop-3. G:{}'.format(task_q.qsize(), global_count))
                    break
                elif task_q.qsize() == 0 and global_count.get_val() != 0:
                    #consumer_done.set()
                    time.sleep(5)
                    quota_avail_event.notifyAll() #TODO this is set when a build/job fails
                    logging.debug('>> notify quota-thread:True G:{}'.format(global_count))
                    if consumer_done.isSet():
                        logging.debug('===EXIT===')
                        logging.debug('<< {} break loop-4. G:{}'.format(task_q.qsize(), global_count))
                        break
                else:
                    logging.debug('{} doing other things'.format(task_q.qsize()))
    logging.info('{} EXITING'.format(task_q.qsize()))


def quota_check(quota_name, quota_event, consumer_done, task_q, global_count):
    logging.info('STARTING')
    logging.debug('QUOTA_NAME : {}'.format(quota_name))
    _running = True
    if QUOTA_NAME != "":
        while _running and True:
            logging.debug('[{}] waiting for resource-thread. G:{}'.format(task_q.qsize(), global_count))
            if consumer_done.isSet():
                logging.debug('[{}] consumer_done is set. break loop-1'.format(task_q.qsize()))
                _running = False
                break
            with quota_event:
                if task_q.qsize() == 0 and global_count.get_val() == 0:
                    logging.debug('[{}] break loop-2. G:{}'.format(task_q.qsize(), global_count))
                    _running = False
                    break
                # ================================
                process_quota(quota_name, quota_event, task_q)
                # ================================
    else:
        # NO quota resource exists. Assume unlimited.
        while True:
            if consumer_done.isSet():
                logging.debug('[{}] break loop-3'.format(task_q.qsize()))
                break
            with quota_event:
                # notify resource-thread
                quota_event.notifyAll()
                logging.debug('>> [{}] notify resource-thread:True. G:{}'.format(task_q.qsize(), global_count))
                time.sleep(5)
    logging.info('[{}] EXITING'.format(task_q.qsize()))


def event_loop(resource, bloom, object_map, task_q, global_count):
    logging.info('STARTING')
    control = 1
    _running = True
    # ----------------------------------
    #           event loop - init
    # ----------------------------------
    event_loop_init(bloom, object_map, task_q, global_count)
    # ----------------------------------
    #           event loop - start
    # ----------------------------------
    while _running and control != -1:
        try:
            for event, code in stream(host=OCP_URL, resource=resource, sa_token=ACCESS_TOKEN,
                                                     namespace=NAMESPACE, tls_verify=False):
                control = code
                if type(event) is dict and control == 1:
                    # ----------------------------------
                    #           event loop - process
                    # ----------------------------------
                    process_events(event, resource, bloom, object_map, task_q, global_count)
                if task_q.qsize() == 0 and global_count.get_val() == 0:
                    logging.debug('[{}] break loop-1. G:{}'.format(task_q.qsize(), global_count))
                    _running = False
                    break
                if control == -1:
                    logging.debug("stream terminated 1.......")
                    control = 1
                    continue
        except Exception as e:
            if "Connection" in str(e):
                logging.debug(str(e))
                logging.debug("stream terminated 2.......")
                control = 1
                if task_q.qsize() == 0 and global_count.get_val() == 0:
                    logging.debug('[{}] break loop-2. G:{}'.format(task_q.qsize(), global_count))
                    _running = False
                    break
                continue
            else:
                raise e


def main():
    logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)
    #logging.getLogger("requests").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)

    login_checks = [check_none(v) for v in [OCP_URL, NAMESPACE, ACCESS_TOKEN]]
    if not all(login_checks):
        raise Exception("Release Trigger can't start! OCP credentials are not provided!")

    # TODO may use config.json or use CRD
    # Load BUILD_MAP
    # TODO use configuration Object
    build_map = os.getenv('BUILD_MAP', "{}")
    if build_map == "{}":
        build_map = load_json_file(CONFIG_FILE)

    if not build_map:
        raise Exception("No BUILD_MAP loaded.Nothing todo")

    imagestream_list = []
    buildconfig_list = []
    job_list = []
    object_map = {}

    # Process BUILD_MAP
    for py_version, os_details in build_map.items():
        for os_version, image_details in os_details.items():
            try:
                application_build_name = "tf-{}-build-image-{}".format(os_version.lower(),
                                                                           py_version.replace('.', ''))
                application_name = 'tf-{}-build-job-{}'.format(os_version.lower(), py_version.replace('.', ''))
                builder_imagestream = '{}:{}'.format(application_build_name, VERSION)
                nb_python_ver = py_version
                docker_file_path = 'Dockerfile.{}'.format(os_version.lower())
                logging.debug("-------------------VARIABLES-------------------------")
                logging.debug("APPLICATION_BUILD_NAME: {}".format(application_build_name))
                logging.debug("APPLICATION_NAME: {}".format(application_name))
                logging.debug("BUILDER_IMAGESTREAM: {}".format(builder_imagestream))
                logging.debug("PYTHON VERSION: {}".format(nb_python_ver))
                logging.debug("DOCKERFILE: {}".format(docker_file_path))
                for var_key, var_val in image_details.items():
                    # self.__dict__[var_key] = var_val
                    logging.debug("{}: {}".format(var_key, var_val))
                logging.debug("-----------------------------------------------------")
                imagestream_template = fill_imagestream_template(ims_name=application_build_name)
                imagestream_list.append({"kind": "ImageStream",
                                         "object": imagestream_template,
                                         "trigger_count": 0,
                                         "retrigger": False})
                job_template = fill_job_template(application_name=application_name,
                                                builder_imagesream=builder_imagestream,
                                                nb_python_ver=nb_python_ver, image_details=image_details)
                object_map[application_name] = job_template
                job_list.append(job_template)
                build_template = fill_buildconfig_template(build_name=application_build_name,
                                                           docker_file_path=docker_file_path,
                                                           nb_python_ver=nb_python_ver,
                                                           image_details=image_details)
                object_map[application_build_name] = build_template

                buildconfig_list.append({"kind": "BuildConfig",
                                         "object": build_template,
                                         "trigger_count": 0,
                                         "retrigger": False,
                                         "application_name": application_name,
                                         "builder_imagestream": builder_imagestream,
                                         "nb_python_ver": nb_python_ver})
            except Exception as e:
                logging.error('Exception: ', e)
                logging.error('Error in Tensorflow Build or Job trigger! Please refer the above log, Starting the next '
                          'one in queue!')

    for ims in imagestream_list:
        ims_name = ims["object"]["metadata"]["name"]
        ims_exist, ims_response = get_imagestream(req_url=OCP_URL, req_headers=HEADERS,
                                                  namespace=NAMESPACE,
                                                  imagestream_name=ims_name)
        if not ims_exist:
            generated_img = create_imagestream(req_url=OCP_URL, req_headers=HEADERS, namespace=NAMESPACE,
                                                             imagestream=ims["object"])
            if not generated_img:
                raise Exception('Image could not be generated for {}'.format(ims_name))

    quota_event = threading.Condition()
    done_event = threading.Event()
    global_count = ResourceCounter()
    task_q = Queue(maxsize=1000)
    bloom = BloomFilter(10000, 0.001)

    # TODO TFBuildConfig  OpenBlasBuildConfig, numpy
    for y in buildconfig_list:
        task_q.put(y)


    #global_count.set_val(task_q.qsize())
    logging.debug("Q size {}".format(task_q.qsize()))
    quota_thread = threading.Thread(name='quota-thread',
                                    target=quota_check,
                                    args=(QUOTA_NAME, quota_event, done_event, task_q, global_count))


    resource_thread = threading.Thread(name='resource-thread',
                                       target=create_resource,
                                       args=(quota_event, done_event, task_q, global_count, object_map))

    event_thread = threading.Thread(name='event-thread',
                                    target=event_loop,
                                    args=("events", bloom, object_map, task_q, global_count))

    #event_thread.daemon = True
    event_thread.start()
    time.sleep(3)
    quota_thread.start()
    resource_thread.start()
    event_thread.join()
    resource_thread.join()
    quota_thread.join()
    logging.debug('END')



if __name__ == '__main__':
    main()


