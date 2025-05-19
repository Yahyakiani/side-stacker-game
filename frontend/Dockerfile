# Stage 1: Build the React application
FROM node:18-alpine AS build-stage

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the application (optional, if you want to serve static files in production)
# For development, Vite dev server is usually enough.
# RUN npm run build

# Stage 2: Serve the application (for development using Vite dev server)
# For a production build, you'd typically use a static server like Nginx
# and copy from the build-stage (e.g., COPY --from=build-stage /app/dist /usr/share/nginx/html)

# FROM node:18-alpine
# WORKDIR /app
# COPY --from=build-stage /app /app # Copies everything including node_modules

EXPOSE 5173

# Command to run the Vite development server
# Using --host ensures it's accessible from outside the container
CMD ["npm", "run", "dev", "--", "--host"]