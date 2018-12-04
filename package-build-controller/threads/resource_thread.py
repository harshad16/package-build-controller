import logging
from plugins.tensorflow_template import trigger_build
from kubernetes import client
from misc.utils import get_job_status, get_header, get_namespace
from clients.build import get_buildconfig, create_buildconfig, get_imagestream, create_imagestream, get_build
from clients.jobs import get_job, create_job, delete_job


def process_taskq(task_q, global_count, object_map):
    host = client.Configuration().host
    api_key = client.Configuration().api_key
    namespace = get_namespace()
    if task_q.qsize() == 0:
        return

    created = None
    check_key_exists = lambda mydict, mykey: mydict[mykey] if mykey in mydict else ""
    check_bkey_exists = lambda mydict, mykey: mydict[mykey] if mykey in mydict else False
    q_item = task_q.get()
    q_resource = check_key_exists(q_item, "object")
    retrigger = check_bkey_exists(q_item, "retrigger")

    # TODO use defaultdict
    if not q_resource and q_resource["kind"] and q_resource["metadata"]["name"]:
        return

    logging.debug('{} processing STARTED. Q-size: {} , G:{}.'.format(task_q.qsize(), task_q.qsize(), global_count))
    q_resource_name = q_resource["metadata"]["name"]
    q_resource_kind = q_resource["kind"]
    logging.debug('{} processing CREATING; name: {}; kind: {}; retrigger:{}'.format(task_q.qsize(),
                                                                                   q_resource_name,
                                                                                   q_resource_kind,
                                                                                   retrigger))
    # ==========================
    # BuildConfig
    # ==========================
    if q_resource_kind == "BuildConfig" and not retrigger:
        # The scheduler might have restarted;
        # So, have we built before ?
        build_created, build_response = get_buildconfig(req_url=host,
                                                        req_headers=get_header(api_key),
                                                        namespace=namespace,
                                                        build_config_name=q_resource_name)
        if not build_created:
            created = create_buildconfig(req_url=host,
                                         req_headers=get_header(api_key),
                                         namespace=namespace,
                                         build_config=q_resource)
            if not created:
                raise Exception('Build could not be created for {}'.format(q_resource_name))
            global_count.increment()
        else:
            # We have built this(q_resource) Resource before.

            latest_build_version = build_response["status"]['lastVersion']
            latest_build_version = str(latest_build_version)
            build_name = q_resource_name + "-" + latest_build_version
            bexist , bresp = get_build(req_url=host, req_headers=get_header(api_key), namespace=namespace,
                                       build_name=build_name)
            logging.debug('{} The Build {} exists={} version={}. G:{}'.format(task_q.qsize(),
                                                                                 q_resource_name,
                                                                                 bexist,
                                                                                 latest_build_version,
                                                                                 global_count))
            if bexist:
                phase = bresp["status"]["phase"]
                if phase == "Complete":
                    #global_count.decrement()
                    logging.debug('{} The Build {} status is {}. G:{}'.format(task_q.qsize(), build_name, phase, global_count))
                    # Lets do the next step associated with this resource
                    # TODO Ask a service what todo next?
                    # ==========================
                    # Create --> Job
                    # ==========================
                    job_name = q_resource_name.replace("image", "job")
                    builder_imagestream = q_resource_name + ":" + "1"
                    job_created, job_response = get_job(req_url=host, req_headers=get_header(api_key), namespace=namespace,
                                                        job_name=job_name)
                    job_status = get_job_status(job_response["status"])
                    logging.debug('{} The Job {} status is {}.'.format(task_q.qsize(), job_name, job_status))

                    if not job_created:
                        # Add job to Queue

                        # job_template = fill_job_template(application_name=job_name,
                        #                                 builder_imagesream=builder_imagestream,
                        #                                 nb_python_ver=q_item["nb_python_ver"])
                        job_template = object_map[job_name]
                        job_item = {"kind": "Job", "object": job_template, "trigger_count": 0, "retrigger": False}
                        task_q.task_done()
                        task_q.put(job_item)
                        global_count.increment()
                        logging.debug('{} processing DONE; ADDED new task: {}; kind: {} G:{}'.format(task_q.qsize(),
                                                                                                job_name,
                                                                                              "Job", global_count))
                        return #donot remove this.
                    else:
                        # JOB was created before the scheduler started.
                        # And also before buildconfig was in the task queue.
                        if job_status == "BackoffLimitExceeded":
                            #Delete the Job
                            logging.debug('{} processing DONE; deleting existing {}; '.format(task_q.qsize(), job_name))
                            dstate, dresp = delete_job(req_url=host,
                                                       req_headers=get_header(api_key),
                                                       namespace=namespace,
                                                       job_name=job_name)
                            # if deleted then add job task
                            if dstate:
                                # Add job to Queue
                                # job_template = fill_job_template(application_name=job_name,
                                #                                  builder_imagesream=builder_imagestream,
                                #                                  nb_python_ver=q_item["nb_python_ver"])
                                job_template = object_map[job_name]
                                job_item = {"kind": "Job", "object": job_template, "trigger_count": 0, "retrigger": False}
                                task_q.task_done()
                                task_q.put(job_item)
                                global_count.increment()
                                logging.debug('{} processing DONE; ADDED kind: {}; new name: {}; G:{}'.format(task_q.qsize(),
                                                                                                          "Job",
                                                                                                          job_name, global_count))
                                return #donot remove this.
                        elif job_status == "ACTIVE":
                            global_count.increment()
                            logging.debug('{} processing DONE; Job is already {}. G:{}; '.format(task_q.qsize(),
                                                                                                              job_status,
                                                                                                              global_count))
                        else:
                            logging.debug('{} The Job {} status is {}.- Trusting-1 Event Thread to do follow up actions'.format(task_q.qsize(),
                                                                                                                        job_name, job_status))
                elif phase == "Failed":
                    logging.debug('{} The Build {} retriggered since status={}. G:{}'.format(task_q.qsize(), build_name, phase, global_count))
                    trigger_build(req_url=host,
                                  req_headers=get_header(api_key),
                                  namespace=namespace,
                                  build_resource=q_resource)
                else:
                    logging.debug('{} The Build {} status is {}. TODO'.format(task_q.qsize(),q_resource_name, phase))
    elif q_resource_kind == "BuildConfig" and retrigger:
        build_created, build_response = get_buildconfig(req_url=host,
                                                        req_headers=get_header(api_key),
                                                        namespace=namespace,
                                                        build_config_name=q_resource_name)
        latest_build_version = build_response["status"]['lastVersion']
        latest_build_version = str(latest_build_version)
        build_name = q_resource_name + "-" + latest_build_version
        bexist , bresp = get_build(req_url=host, req_headers=get_header(api_key), namespace=namespace,
                                   build_name=build_name)
        logging.debug('{} The Build {} exists={} version={}. G:{}'.format(task_q.qsize(),
                                                                             q_resource_name,
                                                                             bexist,
                                                                             latest_build_version,
                                                                             global_count))

        if bexist:
            phase = bresp["status"]["phase"]
            if phase != "ACTIVE":
                trigger_build(req_url=host,
                              req_headers=get_header(api_key),
                              namespace=namespace,
                              build_resource=q_resource)
        else:
            trigger_build(req_url=host,
                          req_headers=get_header(api_key),
                          namespace=namespace,
                          build_resource=q_resource)
    # ==========================
    # ImageStream
    # ==========================
    elif q_resource_kind == "ImageStream":
        if not get_imagestream(req_url=host,
                               req_headers=get_header(api_key),
                               namespace=namespace,
                               imagestream_name=q_resource_name):
            created = create_imagestream(req_url=host, req_headers=get_header(api_key), namespace=namespace,
                                         imagestream=q_resource)
            if not created:
                raise Exception('Image {} could not be created.'.format(q_resource_name))
    # ==========================
    # Job
    # ==========================
    elif q_resource_kind == "Job":
        job_created, job_response = get_job(req_url=host, req_headers=get_header(api_key), namespace=namespace,
                                            job_name=q_resource_name)
        job_status = get_job_status(job_response["status"])
        if not job_created:
            created = create_job(req_url=host, req_headers=get_header(api_key), namespace=namespace, job_name=q_resource)
            if not created:
                raise Exception('Job {} could not be created.'.format(q_resource_name))
        else:
            # JOB was created before the scheduler started.
            logging.debug('{} The Job {} status is {}.Trusting Event Thread to do follow up actions.'.format(task_q.qsize(),
                                                                                                            q_resource_name, job_status))



    else:
        logging.debug('{} processing unknown resource : {}'.format(task_q.qsize(), str(q_resource_kind)))
    task_q.task_done()
    logging.debug('{} processing DONE for {}'.format(task_q.qsize(), q_resource_name))
    return created


