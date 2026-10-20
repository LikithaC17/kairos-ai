# Stage 1: Build the Vite production application
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci || npm install

COPY . ./
RUN npm run build

# Stage 2: Production Nginx web server
FROM nginx:alpine

# Custom Nginx configuration for SPA routing & /api proxying
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled production assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
