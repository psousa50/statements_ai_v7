# --- Build Stage ---
  FROM node:18-alpine AS build

  # Enable corepack for pnpm and set workdir
  RUN corepack enable
  WORKDIR /app
  
  # Set env var for Vite
  ARG VITE_API_URL
  ENV VITE_API_URL=$VITE_API_URL
  
  # Install system dependencies needed for native modules
  RUN apk add --no-cache python3 make g++
  
  # Copy only dependency files to leverage Docker cache
  COPY package.json pnpm-lock.yaml ./
  
  # Install dependencies inside container (native binaries will match Linux)
  RUN pnpm install --frozen-lockfile && pnpm approve-builds
  
  # Copy the rest of the application
  COPY . .
  
  # Build the Vite app
  RUN pnpm run build
  
  # --- Production Stage ---
  FROM nginx:alpine
  
  # Copy built files from the build stage
  COPY --from=build /app/dist /usr/share/nginx/html
  
  # Optionally override default nginx config
  # COPY nginx.conf /etc/nginx/conf.d/default.conf
  
  EXPOSE 80
  
  CMD ["nginx", "-g", "daemon off;"]