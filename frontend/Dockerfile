# ArtTouch NFC 互动视频系统
# Frontend Dockerfile - Nginx serving built Vue app

FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy source and build
COPY frontend/ ./
RUN npm run build

# Production stage - serve with nginx
FROM nginx:1.25-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy static NFC pages (if any)
COPY static/ /usr/share/nginx/html/static/

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
