# Build giao diện React/Vite rồi phục vụ bằng nginx (kèm reverse proxy /api → backend).
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
ENV TZ=Asia/Ho_Chi_Minh
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
