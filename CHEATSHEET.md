# Docker & Kubernetes — One Page Cheat Sheet

Print this. Hand it out at minute zero.

## Mental model

```
your code ──Dockerfile──► image ──registry──► container(s)
                                                  │
                              Kubernetes says how many, where, and what to do
                              when one dies
```

| Term | In one line |
|---|---|
| **Image** | Frozen, read-only recipe result. Like a class. |
| **Container** | A running instance of an image. Like an object. |
| **Layer** | One cached build step. Order your Dockerfile to reuse them. |
| **Registry** | Where images live. Docker Hub, GHCR, ECR. |
| **Volume** | Storage that outlives the container. |
| **Pod** | Smallest K8s unit: 1+ containers sharing network + storage. |
| **Deployment** | "Keep N pods alive, and update them safely." |
| **Service** | Stable name + IP that load-balances to matching pods. |
| **ConfigMap / Secret** | Config / credentials injected as env vars. |
| **PVC** | "I need 1Gi of disk" — the K8s volume. |

---

## The demo app (<http://localhost:8080>)

| Panel | Watch it when |
|---|---|
| **This page was answered by** | Always. Container ID under Docker, pod name under Kubernetes. |
| **Who answered** | You scale — one bar per copy, with its share of your requests. |
| **Request log** | You do a rolling update — v1 and v2 interleave, then only v2. |
| **Guestbook** | You delete containers — the data is in Postgres, so it survives. |
| **Settings this copy was given** | You want to see what a ConfigMap and Secret actually become: env vars. |
| **Break this copy** | You want probes and self-healing to happen on a button. |

`Live` in the top bar re-checks every 1.5s so all of the above updates by itself.

---

## Docker

```bash
docker build -t myapp:v1 .        # build an image from ./Dockerfile
docker run -p 8080:3000 myapp:v1  # run it, laptop:8080 -> container:3000
docker run -d --name app myapp:v1 # detached, named
docker ps                         # running containers
docker ps -a                      # ...including stopped
docker logs -f app                # stream logs
docker exec -it app sh            # shell inside a running container
docker stop app && docker rm app  # stop, delete
docker images                     # local images
docker image prune -a             # reclaim disk
docker system prune -af           # reclaim more disk
```

### Dockerfile skeleton

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json ./      # manifest first...
RUN npm install --omit=dev  # ...so this layer stays cached
COPY . .                  # ...then the source
EXPOSE 3000
USER node
CMD ["node", "server.js"]
```

### Compose

```bash
docker compose up --build   # build + start everything
docker compose up -d        # detached
docker compose ps
docker compose logs -f api
docker compose down         # stop + remove containers
docker compose down -v      # ...and delete the volumes (data gone)
```

Inside a Compose network, **the service name is the hostname**: `DB_HOST: db`.

---

## Kubernetes

```bash
kind create cluster --config kind-config.yaml
kind load docker-image myapp:v1 --name nsu   # cluster cannot see laptop images!

kubectl apply -f k8s/                 # make reality match these files
kubectl get all -n nsu-demo           # what exists
kubectl get pods -n nsu-demo -w       # watch them change
kubectl describe pod <name> -n nsu-demo   # ← WHY it is broken (read Events)
kubectl logs -f deploy/api -n nsu-demo    # app output
kubectl exec -it <pod> -n nsu-demo -- sh  # shell inside

kubectl scale deploy/api --replicas=5 -n nsu-demo
kubectl set env deploy/api APP_VERSION=v2 -n nsu-demo
kubectl rollout status deploy/api -n nsu-demo
kubectl rollout undo deploy/api -n nsu-demo
kubectl delete -f k8s/
```

### Every manifest has the same four keys

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: nsu-demo
spec:
  ...        # what you WANT
```

### The wiring is labels, never IPs

```yaml
# Deployment
selector:
  matchLabels: { app: api }
template:
  metadata:
    labels: { app: api }    # ← must match

# Service
selector: { app: api }      # ← and match here too
```

---

## When it breaks

| Symptom | First thing to check |
|---|---|
| `ErrImagePull` / `ImagePullBackOff` | Image not in the cluster → `kind load docker-image` |
| `CrashLoopBackOff` | `kubectl logs <pod>` — your app is exiting |
| `Pending` forever | `kubectl describe pod` — no node fits, or PVC unbound |
| Service returns nothing | Labels do not match → `kubectl get endpoints <svc>` |
| `ECONNREFUSED 127.0.0.1` | `localhost` inside a container is the container. Use the service name |
| Works in Compose, not K8s | Env vars — check the ConfigMap/Secret is actually mounted |

**`kubectl describe pod <name>` and read the Events at the bottom.** That is the answer
to most questions you will have this week.

---

## Docker Compose → Kubernetes

| Compose | Kubernetes |
|---|---|
| service | Deployment + Service |
| `docker compose up` | `kubectl apply -f` |
| container | Pod |
| service name DNS | Service name DNS |
| named volume | PersistentVolumeClaim |
| `environment:` | env / ConfigMap / Secret |
| — | replicas, self-healing, rolling updates |
