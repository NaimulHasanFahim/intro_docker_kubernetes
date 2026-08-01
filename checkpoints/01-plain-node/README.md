# Checkpoint 1 — Run it the old way (≈8 min)

**Goal:** feel the pain before we sell the cure. Nobody appreciates Docker until they
have spent ten minutes installing a database.

## What the app is

A guestbook with a dashboard. You type a name, it is saved in a Postgres database, and
the page shows the last 10 names plus **which machine answered your request**
(`os.hostname()` in Node — the computer's name).

Right now that name will just be your laptop. That one field is the most useful thing
in this repo: in Checkpoint 2 it becomes a container ID, and in Checkpoint 5 it changes
every time you refresh, which is how we will *see* load balancing without a diagram.

## Steps

```bash
cd checkpoints/01-plain-node

# 1. You need the right Node version. Not "a" Node version.
node --version          # must be >= 18

# 2. Install dependencies (needs npm and a working network)
npm install

# 3. Now you need a Postgres server. On your own machine. Right now.
#    Ubuntu/Debian:
sudo apt-get install -y postgresql
sudo -u postgres psql -c "CREATE USER nsu WITH PASSWORD 'nsu_password';"
sudo -u postgres psql -c "CREATE DATABASE nsu_demo OWNER nsu;"

# 4. Tell the app where the database is
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=nsu
export DB_PASSWORD=nsu_password
export DB_NAME=nsu_demo

# 5. Finally
npm start
```

Open <http://localhost:3000>. (`localhost` = this computer. `3000` = the port the app
is listening on.)

## What you should see

A page that says **This page was answered by** followed by your laptop's name, an empty
guestbook, and the settings you exported in step 4. Sign it once, then stop the app with
`Ctrl-C` and start it again — the name is still there, because it lives in Postgres, not
in the app.

Keep that page in mind. It is the same app for the rest of the session; only what runs
it keeps changing.

## Debrief — write these on the whiteboard

Count what a new teammate must get right before this app runs:

1. Node 18+ installed (not 16, not 20-with-a-broken-build)
2. `npm install` succeeded — same dependency versions as yours
3. Postgres installed, matching major version
4. Postgres service actually running
5. Database + user + password created
6. Five environment variables exported, spelled correctly
7. Port 3000 free
8. Same OS, or at least a compatible one

Eight ways to fail, and that is for a 100-line app. A real one has fifty.
**Docker's promise: turn all eight into one command.**

> If Postgres install is slow on the workshop wifi, do not fight it. Say
> "this is the point" and move on to Checkpoint 2 — the failure *is* the lesson.
