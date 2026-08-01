# Checkpoint 5 — The three tricks that justify Kubernetes (≈15 min)

Scaling, self-healing, zero-downtime deploys. This is the payoff. Do all three live.

```bash
cd checkpoints/05-k8s-scale-update
kubectl apply -f k8s/                  # -f = these files; apply = "make it so"
kubectl get pods -n nsu-demo -w        # -n = namespace, -w = watch, keep printing changes
```

Keep <http://localhost:8080> open on the projector the entire time, with the **Live**
toggle in the top bar switched on — it re-asks the app "who are you?" every 1.5 seconds,
so everything below animates by itself while you talk.

---

## Trick 1 — Scale (the big name at the top does the teaching)

```bash
kubectl scale deploy/api --replicas=5 -n nsu-demo
kubectl get pods -n nsu-demo
```

Watch the browser. **The name under "This page was answered by" keeps changing** — your
requests are being spread across 5 pods by the Service. Nobody configured a load
balancer; you asked for 5 copies and got one address that reaches all of them.

> **Why the name changes at all.** A Service balances per TCP *connection*, and a
> browser keeps one connection open for minutes. So the app answers `/api/status` with
> `Connection: close`, forcing every poll to open a fresh connection and be balanced
> again. Without that one line the page sits on a single pod and the demo looks broken.
> Worth saying out loud — students hit exactly this in their own projects.

The **Who answered** panel makes it countable: one bar per pod, with each pod's share of
your requests. Click **Send 10 requests** and the bars fill out in a couple of seconds.

Then sign the guestbook a few times — each entry records the pod that wrote it, and they
are all writing into the one shared Postgres.

Scale back down:

```bash
kubectl scale deploy/api --replicas=3 -n nsu-demo
```

---

## Trick 2 — Self-healing (the crowd-pleaser)

```bash
# Terminal A: watch
kubectl get pods -n nsu-demo -w

# Terminal B: murder ONE pod
kubectl delete "$(kubectl get pods -n nsu-demo -l app=api -o name | head -1)" -n nsu-demo
```

(`-l app=api` = only pods labelled `app: api`; `-o name` prints just their names, and
`head -1` takes the first. Or read a name out of Terminal A and delete it by hand.)

Within seconds a replacement appears.

> You said you wanted 3. There are 2. Kubernetes fixes that without asking you.
> That is the *entire* idea: **declare the desired state, the controller closes the gap.**

Try harder — delete all of them at once:

```bash
kubectl delete pods -n nsu-demo -l app=api
```

The site stays up (mostly) and the count returns to 3.

### Break one from the browser instead

The **Break this copy** panel does the same thing without a terminal, and it is worth
doing because it shows the *probes* working rather than a plain delete:

| Button | What happens |
|---|---|
| **Make it report itself as sick** | That pod's `/healthz` starts answering 500 (an error). The *readiness* probe notices within ~5s and takes the pod out of the Service, so the browser stops getting replies from it — but `kubectl get pods` still says `Running`. A few seconds later the *liveness* probe gives up and restarts the container: `RESTARTS` goes to 1, and the pod comes back healthy, because the "be broken" flag only ever lived in that process's memory. |
| **Crash it** | The process exits immediately, like a real crash. Kubernetes sees the container die and starts a new one in seconds. |

Both are the same lesson from opposite ends: **you declared 3 healthy pods, and something
is working full-time to keep that true.** Under plain `docker run`, crashing means the
site is down until a human notices.

> With several replicas the button hits whichever pod the Service picked, which may not
> be the one currently shown. That is worth saying out loud — it is the point.

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
`maxUnavailable: 0` means the site never dips below 3 healthy pods.

Leave the browser on Live through the whole rollout and read the **Request log** — every
line is one reply, stamped with its version. You will see `v1` and `v2` interleaved
while both generations are serving, then `v2` only. The version badge flashes when it
flips, and not one request fails.

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

Base64, not encryption. Or click **Reveal the password** in the browser: the app simply
reads the env var it was given, and so can anything else running in that pod.

The value of a Secret is *separation* — one image, different credentials per environment
— not secrecy by itself.

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

---

← [Back: Same app, now on Kubernetes](../04-k8s-first-deploy/)  ·  Stuck? The [cheat sheet](../../CHEATSHEET.md) has a *When it breaks* table.
