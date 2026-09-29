FROM node:24-bookworm-slim AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM dependencies AS build
COPY . .
RUN npm run build

FROM node:24-bookworm-slim
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/build ./
RUN npm ci --omit=dev && npm cache clean --force
COPY start.sh ./start.sh
CMD ["bash", "start.sh"]
