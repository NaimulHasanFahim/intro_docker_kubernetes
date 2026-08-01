# A Dockerfile is a recipe. Each line becomes a cached layer.

# 1. Start from someone else's work: Linux + Node 18, ~50 MB.
FROM node:18-alpine

# 2. Everything after this happens inside /app in the image.
WORKDIR /app

# 3. Copy ONLY the dependency manifest first.
#    Why: layers are cached. If server.js changes but package.json does not,
#    Docker reuses the npm install layer and the build takes 1s instead of 60s.
COPY package.json ./
RUN npm install --omit=dev

# 4. Now copy the rest of the source.
COPY . .

# 5. Documentation for humans + tooling. Does NOT publish the port by itself.
EXPOSE 3000
ENV PORT=3000

# 6. Do not run as root. Free security win, one line.
USER node

# 7. What to run when the container starts.
CMD ["node", "server.js"]
