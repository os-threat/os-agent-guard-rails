FROM node:20-alpine

WORKDIR /app

COPY mock/package.json ./mock/
RUN cd mock && npm install --omit=dev

COPY openapi ./openapi
COPY mock ./mock
COPY seed ./seed
COPY web ./web

WORKDIR /app/mock
ENV OPENAPI_SPEC=/app/openapi/financial-planner.yaml
ENV SEED_SCRIPT=/app/seed/generate_data.js

EXPOSE 8082

CMD ["node", "server.js"]
