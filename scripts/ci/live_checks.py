"""Measure the real container and cluster; preserve results even when a target is missed."""

import csv
import datetime as dt
import json
import os
from pathlib import Path
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request

OUT = Path("results/fresh")
OUT.mkdir(parents=True, exist_ok=True)
SUMMARY = {}
TEXTS = [
    json.loads(line)["text"] for line in Path("data/validation.jsonl").read_text().splitlines()
]


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def run(*args, check=True):
    result = subprocess.run(args, capture_output=True, text=True)
    if check and result.returncode:
        raise RuntimeError(f"{args}: {result.stdout}\n{result.stderr}")
    return result.stdout


def kube(*args):
    return json.loads(run("kubectl", "-n", "app", *args, "-o", "json"))


def pod_list():
    return kube("get", "pods", "-l", "app=command-parser")["items"]


def ready(pod):
    return any(
        c["type"] == "Ready" and c["status"] == "True"
        for c in pod.get("status", {}).get("conditions", [])
    )


def wait_ready(count=2, timeout=240):
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        pods = [p for p in pod_list() if not p["metadata"].get("deletionTimestamp")]
        if len(pods) == count and all(ready(p) for p in pods):
            return pods
        time.sleep(1)
    raise RuntimeError("Timed out waiting for ready replicas")


def request(text="weather in london", port=8080):
    start = time.monotonic()
    req = urllib.request.Request(
        f"http://localhost:{port}/parse",
        data=json.dumps({"text": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        response = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return {
            "status": response.status,
            "headers": dict(response.headers),
            "body": response.read().decode(),
            "seconds": time.monotonic() - start,
        }


def wait_http(port=8000):
    for _ in range(120):
        try:
            with urllib.request.urlopen(f"http://localhost:{port}/readyz", timeout=2) as r:
                if r.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(1)
    raise RuntimeError("Container did not become ready")


def header(response, key):
    return next((v for k, v in response["headers"].items() if k.lower() == key.lower()), None)


def launch_load(name, duration="2m"):
    env = os.environ.copy()
    env["LOADTEST_HEADERS_OUT"] = str(OUT / f"{name}_headers.json")
    env["LOCUST_STOP_TIMEOUT"] = "30"
    log = (OUT / f"{name}.txt").open("w")
    command = [
        "locust",
        "-f",
        "tools/locustfile.py",
        "--headless",
        "--users",
        "4",
        "--spawn-rate",
        "4",
        "--run-time",
        duration,
        "--host",
        "http://localhost:8080",
        "--csv",
        str(OUT / name),
    ]
    process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    return process, log


def finish_load(name, process, log):
    code = process.wait(timeout=300)
    log.close()
    rows = list(csv.DictReader((OUT / f"{name}_stats.csv").open()))
    row = next(r for r in rows if r["Name"] == "Aggregated")
    total, failures = int(row["Request Count"]), int(row["Failure Count"])
    headers = json.loads((OUT / f"{name}_headers.json").read_text())
    successful_headers = sum(headers["per_replica"].values())
    result = {
        "requests": total,
        "failures": failures,
        "failure_percent": 100 * failures / total,
        "p50_ms": float(row["50%"]),
        "p95_ms": float(row["95%"]),
        "rps": float(row["Requests/s"]),
        "locust_exit": code,
        "headers": headers,
        "headers_match_successes": successful_headers == total - failures,
    }
    SUMMARY[name] = result
    save("live_summary.json", SUMMARY)
    return result


def container_checks():
    size = int(
        run("docker", "image", "inspect", "cloud-mini/service:v1", "--format", "{{.Size}}").strip()
    )
    run(
        "docker",
        "run",
        "-d",
        "--name",
        "limited-parser",
        "--cpus",
        "1",
        "--memory",
        "1g",
        "--memory-swap",
        "1g",
        "--network",
        "host",
        "--env-file",
        ".env",
        "-e",
        "MODEL_URI=s3://models/v1",
        "-e",
        "MODEL_VERSION=v1",
        "-e",
        "S3_ENDPOINT=http://localhost:8333",
        "cloud-mini/service:v1",
    )
    wait_http()
    samples = []
    stop = threading.Event()

    def sample():
        while not stop.is_set():
            samples.append(
                {
                    "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "stats": run(
                        "docker",
                        "stats",
                        "--no-stream",
                        "--format",
                        "{{json .}}",
                        "limited-parser",
                        check=False,
                    ).strip(),
                }
            )
            stop.wait(0.5)

    sampler = threading.Thread(target=sample)
    sampler.start()
    replies = [request(text, port=8000) for text in TEXTS[:50]]
    stop.set()
    sampler.join()
    peak = run(
        "docker", "exec", "limited-parser", "cat", "/sys/fs/cgroup/memory.peak", check=False
    ).strip()
    (OUT / "limited_container_logs.txt").write_text(run("docker", "logs", "limited-parser"))
    run("docker", "stop", "limited-parser")
    state = json.loads(run("docker", "inspect", "limited-parser"))[0]
    save(
        "limited_container_inspect.json",
        {
            "state": state["State"],
            "image": state["Image"],
            "cpu_limit_nano": state["HostConfig"]["NanoCpus"],
            "memory_limit_bytes": state["HostConfig"]["Memory"],
        },
    )
    save("limited_container_requests.json", replies)
    save("limited_container_memory.json", samples)
    SUMMARY["container"] = {
        "image_bytes": size,
        "image_under_2gb": size <= 2_000_000_000,
        "requests": len(replies),
        "successful": sum(r["status"] == 200 for r in replies),
        "oom_killed": state["State"]["OOMKilled"],
        "exit_code": state["State"]["ExitCode"],
        "memory_peak_bytes": int(peak) if peak.isdigit() else None,
        "cpu_limit_nano": state["HostConfig"]["NanoCpus"],
        "memory_limit_bytes": state["HostConfig"]["Memory"],
    }
    run("docker", "rm", "limited-parser")
    run(
        "docker",
        "run",
        "-d",
        "--name",
        "fault-parser",
        "--cpus",
        "1",
        "--memory",
        "1g",
        "--memory-swap",
        "1g",
        "--network",
        "host",
        "--env-file",
        ".env",
        "-e",
        "MODEL_URI=s3://models/v1",
        "-e",
        "MODEL_VERSION=v1",
        "-e",
        "S3_ENDPOINT=http://localhost:8333",
        "-e",
        "FAULT_INJECT=1",
        "cloud-mini/service:v1",
    )
    wait_http()
    result = request(port=8000)
    SUMMARY["fault_injection"] = result
    assert result["status"] == 500 and json.loads(result["body"]) == {
        "error": "invalid_model_output"
    }
    run("docker", "rm", "-f", "fault-parser")
    save("live_summary.json", SUMMARY)


def cold_start_checks():
    runs = []
    for index in range(3):
        old_uids = {p["metadata"]["uid"] for p in pod_list()}
        run("kubectl", "-n", "app", "delete", "pods", "-l", "app=command-parser", "--wait=false")
        snapshots = []
        began = time.monotonic()
        while time.monotonic() - began < 240:
            pods = pod_list()
            endpoints = kube("get", "endpoints", "command-parser")
            addresses = [
                a for subset in endpoints.get("subsets", []) for a in subset.get("addresses", [])
            ]
            new = [p for p in pods if p["metadata"]["uid"] not in old_uids]
            old_live = any(p["metadata"]["uid"] in old_uids for p in pods)
            snapshots.append(
                {
                    "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "new_pods": len(new),
                    "new_ready": sum(ready(p) for p in new),
                    "old_pods_present": old_live,
                    "ready_endpoints": len(addresses),
                }
            )
            if len(new) == 2 and all(ready(p) for p in new) and not old_live:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Cold-start readiness timeout")
        timings = []
        for pod in new:
            metadata = pod["metadata"]
            ready_condition = next(c for c in pod["status"]["conditions"] if c["type"] == "Ready")
            created = dt.datetime.fromisoformat(
                metadata["creationTimestamp"].replace("Z", "+00:00")
            )
            became_ready = dt.datetime.fromisoformat(
                ready_condition["lastTransitionTime"].replace("Z", "+00:00")
            )
            elapsed = (became_ready - created).total_seconds()
            timings.append(elapsed)
            logs = run("kubectl", "-n", "app", "logs", metadata["name"], "--timestamps")
            (OUT / f'cold_{index+1}_{metadata["name"]}.txt').write_text(logs)
            assert (
                "downloading model from s3://models/v1" in logs
                and "model download complete" in logs
            )
            save(f'cold_{index+1}_{metadata["name"]}.json', pod)
        no_endpoints = any(
            s["new_pods"]
            and not s["new_ready"]
            and not s["old_pods_present"]
            and s["ready_endpoints"] == 0
            for s in snapshots
        )
        runs.append(
            {
                "run": index + 1,
                "pod_seconds": timings,
                "run_seconds": max(timings),
                "no_endpoints_while_unready_observed": no_endpoints,
            }
        )
        save(f"cold_{index+1}_endpoint_observations.json", snapshots)
    SUMMARY["cold_start"] = {
        "runs": runs,
        "median_seconds": statistics.median(r["run_seconds"] for r in runs),
    }
    save("live_summary.json", SUMMARY)


def load_balancing():
    samples = []
    process, log = launch_load("loadtest")
    while process.poll() is None:
        samples.append(
            {
                "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "top": run("kubectl", "-n", "app", "top", "pods", check=False),
                "pods": [{"name": p["metadata"]["name"], "ready": ready(p)} for p in pod_list()],
            }
        )
        time.sleep(2)
    result = finish_load("loadtest", process, log)
    save("pod_resource_samples.json", samples)
    counts = result["headers"]["per_replica"]
    total = sum(counts.values())
    result["replica_shares"] = {name: value / total for name, value in counts.items()}
    result["each_replica_30_percent"] = len(counts) == 2 and min(counts.values()) / total >= 0.30
    save("live_summary.json", SUMMARY)


def rollout_checks():
    process, log = launch_load("rolling_update", "3m")
    time.sleep(10)
    run(
        "kubectl",
        "-n",
        "app",
        "set",
        "env",
        "deployment/command-parser",
        "MODEL_VERSION=v2",
        "MODEL_URI=s3://models/v2",
    )
    rollout = run(
        "kubectl", "-n", "app", "rollout", "status", "deployment/command-parser", "--timeout=240s"
    )
    after_update = request()
    run("kubectl", "-n", "app", "rollout", "undo", "deployment/command-parser")
    rollback = run(
        "kubectl", "-n", "app", "rollout", "status", "deployment/command-parser", "--timeout=240s"
    )
    after_rollback = request()
    result = finish_load("rolling_update", process, log)
    result.update(
        {
            "rollout": rollout,
            "rollback": rollback,
            "after_update": after_update,
            "after_rollback": after_rollback,
            "v1_restored": header(after_rollback, "X-Model-Version") == "v1",
            "target_met": result["failure_percent"] <= 0.5,
        }
    )
    save("live_summary.json", SUMMARY)


def recovery_checks():
    wait_ready()
    process, log = launch_load("recovery")
    time.sleep(10)
    pod = pod_list()[0]["metadata"]["name"]
    start = time.monotonic()
    deleted = run("kubectl", "-n", "app", "delete", "pod", pod, "--wait=false")
    while any(p["metadata"]["name"] == pod for p in pod_list()):
        time.sleep(0.5)
    restored = wait_ready()
    elapsed = time.monotonic() - start
    result = finish_load("recovery", process, log)
    result.update(
        {
            "deleted": deleted,
            "restored_seconds": elapsed,
            "restored_pods": [p["metadata"]["name"] for p in restored],
            "target_met": result["failure_percent"] <= 2,
        }
    )
    save("live_summary.json", SUMMARY)


def hpa_checks():
    run("kubectl", "apply", "-f", "k8s/hpa.yaml")
    run("kubectl", "-n", "app", "scale", "deployment/command-parser", "--replicas=1")
    wait_ready(1)
    observations = []
    process, log = launch_load("hpa_load", "3m")
    scaled_up = False
    while process.poll() is None:
        hpa = kube("get", "hpa", "command-parser")
        deployment = kube("get", "deployment", "command-parser")
        observations.append(
            {
                "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "phase": "load",
                "hpa": hpa["status"],
                "deployment": deployment["status"],
            }
        )
        if deployment["status"].get("readyReplicas") == 2:
            scaled_up = True
        time.sleep(5)
    finish_load("hpa_load", process, log)
    scaled_down = False
    start = time.monotonic()
    while time.monotonic() - start < 300:
        hpa = kube("get", "hpa", "command-parser")
        deployment = kube("get", "deployment", "command-parser")
        observations.append(
            {
                "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "phase": "idle",
                "hpa": hpa["status"],
                "deployment": deployment["status"],
            }
        )
        if (
            hpa["status"].get("desiredReplicas") == 1
            and deployment["status"].get("replicas") == 1
            and deployment["status"].get("readyReplicas") == 1
        ):
            scaled_down = True
            break
        time.sleep(5)
    SUMMARY["hpa_cycle"] = {
        "scaled_1_to_2": scaled_up,
        "scaled_back_to_1": scaled_down,
        "idle_wait_seconds": time.monotonic() - start,
    }
    save("hpa_observations.json", observations)
    save("live_summary.json", SUMMARY)


if __name__ == "__main__":
    try:
        container_checks()
        run("kubectl", "-n", "app", "delete", "hpa", "command-parser", "--ignore-not-found")
        run("kubectl", "-n", "app", "scale", "deployment/command-parser", "--replicas=2")
        wait_ready()
        cold_start_checks()
        load_balancing()
        rollout_checks()
        recovery_checks()
        hpa_checks()
        (OUT / "kubernetes_objects.txt").write_text(
            run("kubectl", "get", "deploy,svc,ingress,hpa,pods", "-A")
        )
    finally:
        save("live_summary.json", SUMMARY)
