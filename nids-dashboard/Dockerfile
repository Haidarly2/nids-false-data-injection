# TAHAP 1: Proses Build menggunakan Node.js
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# TAHAP 2: Proses Production menggunakan Nginx
FROM nginx:alpine
# Menyalin hasil build React ke folder publik Nginx
COPY --from=build /app/dist /usr/share/nginx/html
# Membuka port standar web
EXPOSE 80
# Menyalakan Nginx
CMD ["nginx", "-g", "daemon off;"]