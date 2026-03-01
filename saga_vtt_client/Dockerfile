# Dockerfile for TALEWEAVERS VTT Client (React/Vite)
FROM node:20-slim

WORKDIR /app

# Copy package files and install dependencies
COPY saga_vtt_client/package*.json ./
RUN npm install

# Copy the rest of the frontend code
COPY saga_vtt_client/ .

EXPOSE 5173

# Vite defaults to localhost, need --host to be accessible from host
CMD ["npm", "run", "dev", "--", "--host"]
