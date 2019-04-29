import logging
from clients.resource_watch import test_endpoint
from clients.build import get_buildconfig, get_build, get_build_logs
from misc.const import PROCESS_RESOURCES, PLUGIN_BUILD_CONFIG_LABEL, PLUGIN_JOB_LABEL
from clients.jobs import get_job, get_job_logs, get_all_pods
from kubernetes import client
from misc.utils import (
    is_value_in_label,
    get_value_in_label,
    get_job_status,
    get_build_status,
    get_namespace,
    get_header,
    get_job_pod,
)
from misc.github_issue import report_issue


def process_new_event(
    resource_type, event_obj, bloom, object_map, task_q, global_count
):
    host = client.Configuration().host
    api_key = client.Configuration().api_key
    namespace = get_namespace()
    if resource_type == "builds":
        # =========================
        # Process Failed Builds(init)
        # =========================
        if is_build_failed(event_obj["status"]):
            build_config_name = get_value_in_label(
                event_obj["metadata"]["labels"], "appName"
            )
            build_ver = int(event_obj["metadata"]["name"][-1:])
            bc_exist, bc_response = get_buildconfig(
                req_url=host,
                req_headers=get_header(api_key),
                namespace=namespace,
                build_config_name=build_config_name,
            )
            if bc_exist:
                latest_build_version = bc_response["status"]["lastVersion"]
                latest_build_id = int(latest_build_version)
                b_exist, build_resp = get_build(
                    req_url=host,
                    req_headers=get_header(api_key),
                    namespace=namespace,
                    build_name="{}-{}".format(build_config_name, str(latest_build_id)),
                )
                # -----------------------------------------------------
                # build_ver | latest_build_id |    ACTION
                # -----------------------------------------------------
                #   0       |       0         |    not possible(SKIP)
                #   x       |      less than x|    not possible(SKIP)
                #   x       |      more than x|    possible(PROCESS)
                # -----------------------------------------------------
                if not (build_ver < latest_build_id):
                    # If no new builds are Running then trigger
                    name = event_obj["metadata"]["name"]
                    bc_name = name[:-2]
                    ver = int(name[-1:])
                    # Do we know of the Build ?
                    if bc_name in object_map:
                        obj = object_map[bc_name]
                        # print(obj)
                        ver = ver + 1
                        obj["spec"]["output"]["to"]["name"] = bc_name + ":" + str(ver)
                        logging.debug(
                            "Adding new BuildConfig with version {} ".format(
                                obj["spec"]["output"]["to"]["name"]
                            )
                        )
                        task_q.put(
                            {
                                "kind": "BuildConfig",
                                "object": obj,
                                "trigger_count": 1,
                                "retrigger": True,
                            }
                        )
                        global_count.increment()
                        logging.debug(
                            "Adding new BuildConfig {} G:{}".format(
                                obj["spec"]["output"]["to"]["name"], global_count
                            )
                        )
                else:
                    logging.debug(
                        "Ignoring {}-{} since {}-{} found.".format(
                            build_config_name,
                            build_ver,
                            build_config_name,
                            latest_build_id,
                        )
                    )
    elif resource_type == "jobs":
        # =========================
        # Process Failed Jobs(init)
        # =========================
        if is_job_failed(event_obj["status"]):
            logging.debug(
                "Ignoring new Job event {}.Let Job EVENT do processing ".format(
                    event_obj["metadata"]["name"]
                )
            )
    elif resource_type == "events":
        if "type" in event_obj:
            if event_obj["object"]["involvedObject"]["name"]:
                # print("New EVENTS Object {} ".format(event_obj['object']['involvedObject']["kind"]))
                # =========================
                # EVENTS of type Pods
                # =========================
                name = event_obj["object"]["involvedObject"]["name"]
                if event_obj["object"]["involvedObject"]["kind"] == "Pod":
                    name = name[: -len("-build")]
                    ver = int(name.rsplit("-", 1)[1])
                    bc_name = name.rsplit("-", 1)[0]
                    status = event_obj["object"]["reason"]
                    logging.debug(
                        "TODO - processing EVENTS Object of type Pod {} with status {}".format(
                            name, status
                        )
                    )

                # =========================
                # EVENTS of type Build
                # =========================
                elif event_obj["object"]["involvedObject"]["kind"] == "Build":
                    name = name
                    ver = int(name.rsplit("-", 1)[1])
                    bc_name = name.rsplit("-", 1)[0]
                    status = event_obj["object"]["reason"]
                    logging.debug(
                        "processing EVENTS Object of type Build; {} with status {}; BuildConfig {}".format(
                            name, status, bc_name
                        )
                    )
                    bc_exist, bc_response = get_buildconfig(
                        req_url=host,
                        req_headers=get_header(api_key),
                        namespace=namespace,
                        build_config_name=bc_name,
                    )

                    if bc_exist:
                        latest_build_version = bc_response["status"]["lastVersion"]
                        latest_build_id = int(latest_build_version)
                        b_exist, build_resp = get_build(
                            req_url=host,
                            req_headers=get_header(api_key),
                            namespace=namespace,
                            build_name="{}-{}".format(bc_name, str(latest_build_id)),
                        )

                        if b_exist:
                            build_status = build_resp.get("status")
                            # if latest build is failed retrigger
                            if is_build_failed(build_status):
                                seen = bloom.add(
                                    [
                                        build_status["config"]["kind"],
                                        build_status["config"]["name"],
                                        build_status["phase"],
                                    ]
                                )
                                if not seen:
                                    logging.debug(
                                        "Build not seen {} Failed-status is {}".format(
                                            bc_name, build_status["phase"]
                                        )
                                    )
                                    latest_build_id += 1
                                    if bc_name in object_map:
                                        obj = object_map[bc_name]
                                        # print(obj)
                                        obj["spec"]["output"]["to"]["name"] = (
                                            bc_name + ":" + str(latest_build_id)
                                        )
                                        logging.debug(
                                            "Adding new BuildConfig to retrigger {} ".format(
                                                obj["spec"]["output"]["to"]["name"]
                                            )
                                        )
                                        task_q.put(
                                            {
                                                "kind": "BuildConfig",
                                                "object": obj,
                                                "trigger_count": 1,
                                                "retrigger": True,
                                            }
                                        )
                                else:
                                    logging.debug(
                                        "Build seen {} Failed-status is {}".format(
                                            bc_name, build_status["phase"]
                                        )
                                    )
                                    build_pod_name = "{}-{}-build".format(
                                        bc_name, latest_build_id
                                    )
                                    pod_exist, logs = get_build_logs(
                                        req_url=host,
                                        req_headers=get_header(api_key),
                                        namespace=namespace,
                                        build_pod=build_pod_name,
                                    )
                                    if report_issue(
                                        bc_name, build_status["phase"], detail=logs
                                    ):
                                        logging.debug(
                                            "The build {} status is {}. A GitHub Issue has been raised.".format(
                                                bc_name, build_status["phase"]
                                            )
                                        )
                                    else:
                                        logging.debug(
                                            "The build {} status is {}. Failed to raise a GitHub Issue. Please contact the admin".format(
                                                bc_name, build_status["phase"]
                                            )
                                        )
                                    if (
                                        pod_exist
                                        and "gpg: keyserver receive failed: Keyserver error"
                                        in logs
                                    ):
                                        obj = object_map[bc_name]
                                        task_q.put(
                                            {
                                                "kind": "BuildConfig",
                                                "object": obj,
                                                "trigger_count": 1,
                                                "retrigger": True,
                                            }
                                        )
                                    else:
                                        global_count.decrement()
                                        logging.debug(
                                            "Build seen {} Failed-status is {} G:{}".format(
                                                bc_name,
                                                build_status["phase"],
                                                global_count,
                                            )
                                        )

                            else:
                                # Build is COMPLETE
                                seen = bloom.add(
                                    [
                                        build_status["config"]["kind"],
                                        build_status["config"]["name"],
                                        build_status["phase"],
                                    ]
                                )
                                if not seen and bc_name in object_map.keys():
                                    # global_count.decrement()
                                    logging.debug(
                                        "{} The Build {} status is {} global_count={}.".format(
                                            task_q.qsize(),
                                            bc_name,
                                            build_status["phase"],
                                            global_count,
                                        )
                                    )
                                    job_name = bc_name.replace("image", "job")
                                    jexist, jresp = get_job(
                                        req_url=host,
                                        req_headers=get_header(api_key),
                                        namespace=namespace,
                                        job_name=job_name,
                                    )
                                    if not jexist:
                                        if job_name in object_map:
                                            job = object_map[job_name]
                                            task_q.put(
                                                {
                                                    "kind": "Job",
                                                    "object": job,
                                                    "trigger_count": 0,
                                                    "retrigger": False,
                                                }
                                            )
                                            global_count.increment()
                                            logging.debug(
                                                "{} The Build->Job {} does not exist.Adding it. G:{}.".format(
                                                    task_q.qsize(),
                                                    job_name,
                                                    global_count,
                                                )
                                            )
                                    else:
                                        job_status = get_job_status(jresp.get("status"))
                                        logging.debug(
                                            "{} The Build->Job {} status is {}.G:{}.".format(
                                                task_q.qsize(),
                                                job_name,
                                                job_status,
                                                global_count,
                                            )
                                        )

                # =========================
                # EVENTS of type Jobs
                # =========================
                elif event_obj["object"]["involvedObject"]["kind"] == "Job":
                    job_name = event_obj["object"]["involvedObject"]["name"]
                    jbool, jresponse = get_job(
                        req_url=host,
                        req_headers=get_header(api_key),
                        namespace=namespace,
                        job_name=job_name,
                    )
                    job_status = get_job_status(jresponse.get("status"))

                    if job_status == "BackoffLimitExceeded":
                        global_count.decrement()
                        # Raising GitHub Issue
                        _, pods_info = get_all_pods(
                            req_url=host,
                            req_headers=get_header(api_key),
                            namespace=namespace,
                        )
                        job_pod_name = get_job_pod(job_name, pods_info)
                        pod_exist, joblogs = get_job_logs(
                            req_url=host,
                            req_headers=get_header(api_key),
                            namespace=namespace,
                            job_pod=job_pod_name,
                        )
                        detail = "Due to BackoffLimitExceeded"
                        if joblogs:
                            detail = joblogs
                        if report_issue(job_name, job_status, detail=detail):
                            logging.debug(
                                "{} The Job {} status is {} global_count={}. A GitHub Issue has been raised.".format(
                                    task_q.qsize(), job_name, job_status, global_count
                                )
                            )
                        else:
                            logging.debug(
                                "{} The Job {} status is {} global_count={}. Failed to raise a GitHub Issue. Please contact the admin".format(
                                    task_q.qsize(), job_name, job_status, global_count
                                )
                            )

                    elif job_status == "Complete":
                        global_count.decrement()
                        logging.debug(
                            "{} The Job {} status is {}. global_count={}.".format(
                                task_q.qsize(), job_name, job_status, global_count
                            )
                        )
                    else:
                        # if active
                        logging.debug(
                            "{} The Job {} status is {}.TODO".format(
                                task_q.qsize(), job_name, job_status
                            )
                        )
                        # print(json.dumps(event, indent=4, sort_keys=True))


def is_build_failed(build_status):
    return build_status["phase"] != "Complete" and build_status["phase"] not in [
        "Pending",
        "Running",
        "BuildStarted",
    ]


def is_job_failed(job_status):
    jresp_conditions = job_status.get("conditions", None)
    if jresp_conditions:
        jstatus_type = jresp_conditions[0]["type"]
        if jstatus_type == "Complete":
            return False, "Complete"
        jstatus_reason = jresp_conditions[0]["reason"]
        return True, jstatus_reason
    else:
        if "active" in job_status:
            return False, "active"


def process_events(event, resource, bloom, object_map, task_q, global_count):
    # Only process events from resources in PROCESS_RESOURCES
    if event["object"]["involvedObject"]["kind"] in PROCESS_RESOURCES:
        m_message, seen_before, m_count = add_event_to_map(
            event=event, resource=resource, bloom=bloom
        )
        logging.debug(
            "EVENTS: seen-before: {} {} B:{} G:{}".format(
                seen_before, m_message, m_count, global_count
            )
        )
        if not seen_before:
            # if EVENT is new...i.e it is not seen by BloomFilter then process events.
            process_new_event("events", event, bloom, object_map, task_q, global_count)
            # if EVENT is old...i.e it is seen by BloomFilter before then do not do anything.


def event_loop_init(bloom, object_map, task_q, global_count):
    builds = "builds"
    host = client.Configuration().host
    api_key = client.Configuration().api_key
    namespace = get_namespace()
    past_builds = test_endpoint(
        host=host, req_headers=get_header(api_key), namespace=namespace, resource=builds
    )
    logging.debug("PAST BUILDS : {}".format(len(past_builds.json()["items"])))
    for pbuild in past_builds.json()["items"]:
        if is_value_in_label(
            pbuild["metadata"]["labels"], object_map[PLUGIN_BUILD_CONFIG_LABEL]
        ):
            mkey, mstatus, mcount = add_build_to_map(build=pbuild, map=bloom)
            logging.debug(
                "BUILDS : seen-before: {} {} B:{} G:{}".format(
                    mstatus, mkey, mcount, global_count
                )
            )
            process_new_event("builds", pbuild, bloom, object_map, task_q, global_count)
    jobs = "jobs"
    _, past_jobs = get_job(
        req_url=host, req_headers=get_header(api_key), namespace=namespace
    )
    logging.debug("PAST Jobs : {}".format(len(past_jobs["items"])))
    for pjob in past_jobs["items"]:
        if is_value_in_label(pjob["metadata"]["labels"], object_map[PLUGIN_JOB_LABEL]):
            mkey, mstatus, mcount = add_job_to_map(job=pjob, map=bloom)
            logging.debug(
                "JOBS : seen-before: {} {} B:{} G:{}".format(
                    mstatus, mkey, mcount, global_count
                )
            )
            process_new_event("jobs", pjob, bloom, object_map, task_q, global_count)


def add_job_to_map(job, map):
    host = client.Configuration().host
    api_key = client.Configuration().api_key
    namespace = get_namespace()
    job_exists, jresponse = get_job(
        req_url=host,
        req_headers=get_header(api_key),
        namespace=namespace,
        job_name=job["metadata"]["name"],
    )
    if job_exists:
        job_status = get_job_status(jresponse.get("status"))
        seen_before = map.add(
            [
                "Job",
                job["metadata"]["name"],
                jresponse["metadata"]["resourceVersion"],
                job_status,
            ]
        )
        message = "Kind: {0}; Name: {1}; version:{2}; reason:{3}".format(
            "Job",
            job["metadata"]["name"],
            jresponse["metadata"]["resourceVersion"],
            job_status,
        )
        logging.debug(
            "JOBS :*seen-before: {} {} {} ".format(seen_before, message, map.count)
        )
        if not seen_before:
            message = "Kind: {0}; Name: {1}; version:{2}; reason:{3}".format(
                "Job",
                job["metadata"]["name"],
                job["metadata"]["resourceVersion"],
                get_job_status(job["status"]),
            )

            seen_before = map.add(
                [
                    "Job",
                    job["metadata"]["name"],
                    job["metadata"]["resourceVersion"],
                    get_job_status(job["status"]),
                ]
            )
            return message, seen_before, map.count
        else:
            return message, seen_before, map.count
    else:
        return "", True, map.count


def add_build_to_map(build, map):
    # print(event)
    message = "Kind: {0}; Name: {1}; version:{2}; reason:{3}".format(
        "Build",
        build["metadata"]["name"],
        build["metadata"]["resourceVersion"],
        build["status"]["phase"],
    )
    # print(message)
    status = map.add(
        [
            "Build",
            build["metadata"]["name"],
            build["metadata"]["resourceVersion"],
            build["status"]["phase"],
        ]
    )
    return message, status, map.count


def add_resource(event, map):
    if "type" in event:
        message = "Kind: {0}; Name: {1}; version:{2}; reason:{3}".format(
            event["object"]["kind"],
            event["object"]["metadata"]["name"],
            event["object"]["metadata"]["resourceVersion"],
            event["object"]["status"]["phase"],
        )
        status = map.add(
            [
                event["object"]["kind"],
                event["object"]["metadata"]["name"],
                event["object"]["metadata"]["resourceVersion"],
                event["object"]["status"]["phase"],
            ]
        )
        return message, status, map.count


def add_event_to_map(event, resource, bloom):
    if resource == "events":
        if "type" in event:
            kind = event["object"]["involvedObject"]["kind"]
            if kind == "Job":
                return add_event_job_to_map(bloom, event)
            else:
                return add_event_build_to_map(bloom, event)
    else:
        return add_resource(event, bloom)


def add_event_build_to_map(bloom, event):
    host = client.Configuration().host
    api_key = client.Configuration().api_key
    namespace = get_namespace()
    build_exist, bresponse = get_build(
        req_url=host,
        req_headers=get_header(api_key),
        namespace=namespace,
        build_name=event["object"]["involvedObject"]["name"],
    )
    if not build_exist:
        message = "Kind: {0}; Name: {1}; version:{2}; reason:{3}".format(
            event["object"]["involvedObject"]["kind"],
            event["object"]["involvedObject"]["name"],
            event["object"]["involvedObject"]["resourceVersion"],
            event["object"]["reason"],
        )
        # seen_before = bloom.add([event['object']['involvedObject']['kind'], event['object']['involvedObject']['name'],
        #                          event['object']['involvedObject']['resourceVersion'],
        #                          event['object']['reason']])
        return message, True, bloom.count
    else:
        build_status = get_build_status(bresponse.get("status"))
        seen_before = bloom.add(
            [
                event["object"]["involvedObject"]["kind"],
                event["object"]["involvedObject"]["name"],
                bresponse["metadata"]["resourceVersion"],
                build_status,
            ]
        )
        message = "Kind: {0}; Name: {1}; version:{2}; reason:{3}".format(
            event["object"]["involvedObject"]["kind"],
            event["object"]["involvedObject"]["name"],
            bresponse["metadata"]["resourceVersion"],
            build_status,
        )
        if not seen_before:
            message = "Kind: {0}; Name: {1}; version:{2}; reason:{3}".format(
                event["object"]["involvedObject"]["kind"],
                event["object"]["involvedObject"]["name"],
                event["object"]["involvedObject"]["resourceVersion"],
                event["object"]["reason"],
            )
            seen_before = bloom.add(
                [
                    event["object"]["involvedObject"]["kind"],
                    event["object"]["involvedObject"]["name"],
                    event["object"]["involvedObject"]["resourceVersion"],
                    event["object"]["reason"],
                ]
            )
            return message, seen_before, bloom.count
        else:
            return message, seen_before, bloom.count


def add_event_job_to_map(bloom, event):
    host = client.Configuration().host
    api_key = client.Configuration().api_key
    namespace = get_namespace()
    job_exist, jresponse = get_job(
        req_url=host,
        req_headers=get_header(api_key),
        namespace=namespace,
        job_name=event["object"]["involvedObject"]["name"],
    )
    if not job_exist:
        message = "Kind: {0}; Name: {1}; version:{2}; reason:{3}".format(
            event["object"]["involvedObject"]["kind"],
            event["object"]["involvedObject"]["name"],
            event["object"]["involvedObject"]["resourceVersion"],
            event["object"]["reason"],
        )
        seen_before = bloom.add(
            [
                event["object"]["involvedObject"]["kind"],
                event["object"]["involvedObject"]["name"],
                event["object"]["involvedObject"]["resourceVersion"],
                event["object"]["reason"],
            ]
        )
        return message, seen_before, bloom.count
    job_status = get_job_status(jresponse.get("status"))
    seen_before = bloom.add(
        [
            event["object"]["involvedObject"]["kind"],
            event["object"]["involvedObject"]["name"],
            jresponse["metadata"]["resourceVersion"],
            job_status,
        ]
    )
    message = "Kind: {0}; Name: {1}; version:{2}; reason:{3}".format(
        event["object"]["involvedObject"]["kind"],
        event["object"]["involvedObject"]["name"],
        jresponse["metadata"]["resourceVersion"],
        job_status,
    )
    if not seen_before:
        message = "Kind: {0}; Name: {1}; version:{2}; reason:{3}".format(
            event["object"]["involvedObject"]["kind"],
            event["object"]["involvedObject"]["name"],
            event["object"]["involvedObject"]["resourceVersion"],
            event["object"]["reason"],
        )
        seen_before = bloom.add(
            [
                event["object"]["involvedObject"]["kind"],
                event["object"]["involvedObject"]["name"],
                event["object"]["involvedObject"]["resourceVersion"],
                event["object"]["reason"],
            ]
        )
        return message, seen_before, bloom.count
    else:
        return message, seen_before, bloom.count
