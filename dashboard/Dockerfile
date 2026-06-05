FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json /app/
RUN npm install

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY src /app/src
COPY public /app/public
COPY index.html /app/index.html
COPY vite.config.js /app/vite.config.js
COPY postcss.config.js /app/postcss.config.js
COPY tailwind.config.js /app/tailwind.config.js
RUN npm run build

FROM nginx:alpine AS runner

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
