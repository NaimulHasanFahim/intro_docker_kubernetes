# Checkpoint 5 — The three tricks that justify Kubernetes (≈15 min)

Scaling, self-healing, zero-downtime deploys. This is the payoff. Do all three live.

```bash
cd checkpoints/05-k8s-scale-update
kubectl apply -f k8s/
kubectl get pods -n nsu-demo -w
```

Keep <http://localhost:8080> open on the projector the entire time.

---

## Trick 1 — Scale (the "Served by" line does the teaching)

```bash
kubectl scale deploy/api --replicas=5 -n nsu-demo
kubectl get pods -n nsu-demo
```

Now refresh the browser repeatedly. **The "Served by" hostname changes** — you are
being load-balanced across 5 pods by the Service. Nobody configured a load balancer.

Sign the guestbook from different pods and watch the `served by` column fill with
different names, all writing to the one shared Postgres.

Scale back down:

```bash
kubectl scale deploy/api --replicas=3 -n nsu-demo
```

---

## Trick 2 — Self-healing (the crowd-pleaser)

```bash
# Terminal A: watch
kubectl get pods -n nsu-demo -w

# Terminal B: murder a pod
kubectl delete pod -n nsu-demo -l app=api --field-selector status.phase=Running \
  --wait=false | head -1
```

Or pick one by name and delete it. Within seconds a replacement appears.

> You said you wanted 3. There are 2. Kubernetes fixes that without asking you.
> That is the *entire* idea: **declare the desired state, the controller closes the gap.**

Try harder — delete all of them at once:

```bash
kubectl delete pods -n nsu-demo -l app=api
```

The site stays up (mostly) and the count returns to 3.

---

## Trick 3 — Rolling update and rollback

Trigger a new version. No rebuild needed — changing the env var changes the pod
template, and any pod-template change starts a rollout:

```bash
kubectl set env deploy/api APP_VERSION=v2 -n nsu-demo

kubectl rollout status deploy/api -n nsu-demo
kubectl get pods -n nsu-demo -w
```

Watch: new pods come up, pass their readiness probe, *then* old ones are removed.
`maxUnavailable: 0` means the site never dips below 3 healthy pods. Refresh the
browser through the whole rollout — the badge flips from v1 to v2 and it never 502s.

Broke it? One command:

```bash
kubectl rollout history deploy/api -n nsu-demo
kubectl rollout undo deploy/api -n nsu-demo
```

**Optional (if wifi is good):** do it with a real image instead of an env var —

```bash
docker build -t nsu-guestbook:v2 ../03-compose-db
kind load docker-image nsu-guestbook:v2 --name nsu
kubectl set image deploy/api api=nsu-guestbook:v2 -n nsu-demo
```

---

## Prove the Secret is not magic (30 seconds, and it sticks)

```bash
kubectl get secret db-secret -n nsu-demo -o jsonpath='{.data.DB_PASSWORD}' | base64 -d; echo
```

Base64, not encryption. The value of a Secret is *separation* — one image, different
credentials per environment — not secrecy by itself.

## Prove the data now survives

```bash
kubectl delete pod -n nsu-demo -l app=postgres   # kill the database
# wait for the new pod, refresh the browser -- guestbook entries are still there
```

Because the data lives in the PersistentVolumeClaim, not in the pod. Compare with
Checkpoint 4, where `emptyDir` meant killing the pod wiped everything.

---

## Clean up

```bash
kubectl delete namespace nsu-demo
kind delete cluster --name nsu
docker system prune -f            # reclaim disk from the workshop
```

## What we deliberately skipped

Ingress + TLS · Helm charts · StatefulSets (the *right* way to run databases) ·
HorizontalPodAutoscaler · RBAC · NetworkPolicy · resource quotas · GitOps ·
observability. Name them so students know the map is bigger than the tour.

**And the honest production note:** you usually should *not* run your database in
Kubernetes on day one. Use a managed Postgres (RDS, Cloud SQL, Neon). We ran it in the
cluster today because it teaches PVCs and Secrets in one demo.
