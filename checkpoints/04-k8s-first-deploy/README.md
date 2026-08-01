# Checkpoint 4 — Same app, now on Kubernetes (≈15 min)

**Goal:** get the identical image running on a real cluster and understand the four
objects that got it there: Namespace, Deployment, Pod, Service.

> **Instructor prep:** create the cluster and load the image BEFORE the session.
> `kind create cluster` takes 1–3 minutes on good wifi and much longer on bad wifi.

**Four words you need before the commands make sense:**

| Word | Meaning |
|---|---|
| **Cluster** | A group of machines Kubernetes manages as if they were one big computer. |
| **Node** | One machine in that group. With `kind`, each "machine" is really a container on your laptop. |
| **kind** | *Kubernetes IN Docker* — a throwaway practice cluster, no cloud account needed. |
| **Namespace** | A folder inside the cluster that keeps our objects away from everything else. Ours is `nsu-demo`, which is why every command below ends in `-n nsu-demo`. |

## 1. Cluster up (pre-session)

```bash
cd checkpoints/04-k8s-first-deploy

kind create cluster --config kind-config.yaml
kubectl cluster-info --context kind-nsu
kubectl get nodes            # 1 control-plane + 2 workers
```

Show them: `docker ps`. The "nodes" of the cluster are just Docker containers.
The abstraction is thinner than it looks.

## 2. Get our image into the cluster

The cluster has its own image store; it cannot see your laptop's images.

```bash
# built back in Checkpoint 2/3
docker build -t nsu-guestbook:v1 ../03-compose-db
kind load docker-image nsu-guestbook:v1 --name nsu
```

> Skip this and you get `ErrImagePull`. Which is a fine thing to demo on purpose.

## 3. Apply the manifests

```bash
kubectl apply -f k8s/

kubectl get all -n nsu-demo
kubectl get pods -n nsu-demo -w      # watch them go Pending -> ContainerCreating -> Running
```

Open <http://localhost:8080>. Same app, same image, new world — except the big name at
the top is now a pod name like `api-7d9c8f5b6-x2klm` instead of a container ID. Compare it with
`kubectl get pods -n nsu-demo`: that is the exact pod that answered your request.

## 4. Read the room's mind: "what did I just do?"

You wrote down what you *want*. Kubernetes made reality match it.

```
Deployment ("I want 1 api pod")
    └─ ReplicaSet (counts pods, creates/deletes to hit the number)
         └─ Pod (one or more containers sharing a network + storage)
              └─ Container (your image, running)

Service ("api") ── stable DNS name + IP ──> whichever pods are alive right now
```

Pods die and get replaced with new IPs constantly. That is why nothing ever talks to
a pod IP — everything talks to a Service name.

## 5. kubectl survival kit

```bash
kubectl get pods -n nsu-demo                    # what exists
kubectl describe pod <name> -n nsu-demo         # WHY is it not starting (read Events at the bottom)
kubectl logs <pod> -n nsu-demo                  # app output
kubectl logs -f deploy/api -n nsu-demo          # follow the deployment's logs
kubectl exec -it <pod> -n nsu-demo -- sh        # shell inside
kubectl get svc -n nsu-demo                     # services and their ports
kubectl delete -f k8s/                          # clean slate
```

**Teach `describe` explicitly.** 90% of "my pod is broken" questions are answered by
the Events section at the bottom of `kubectl describe pod`.

## Compose vs Kubernetes, same idea, different words

| Docker Compose | Kubernetes |
|---|---|
| service | Deployment + Service |
| `docker compose up` | `kubectl apply -f` |
| container | Pod (which holds containers) |
| service name DNS | Service name DNS |
| named volume | PersistentVolumeClaim |
| `environment:` | env / ConfigMap / Secret |
| — | replicas, self-healing, rolling updates |
