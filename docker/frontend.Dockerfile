FROM node:lts-slim

WORKDIR /usr/src/app

# Install Node dependencies first to leverage Docker layer caching.
COPY src/frontend/package.json src/frontend/package-lock.json ./
RUN npm ci

# Copy the frontend application source.
COPY src/frontend/ .

EXPOSE 5173

# Development server bound to all interfaces so Docker can publish the port.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
