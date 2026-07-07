# syntax=docker/dockerfile:1

# Pinned to the same Playwright version as package.json so the bundled
# browsers match the npm package exactly.
FROM mcr.microsoft.com/playwright:v1.61.1-noble

WORKDIR /app/test

COPY package*.json ./
RUN npm install

COPY . .

CMD ["npx", "playwright", "test"]
