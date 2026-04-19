FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci --legacy-peer-deps
COPY . .
RUN npm run build

FROM nginx:1.27-alpine

RUN addgroup -S querymind && adduser -S querymind -G querymind
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/querymind-frontend/browser /usr/share/nginx/html
RUN chown -R querymind:querymind /usr/share/nginx/html /var/cache/nginx /var/run /var/log/nginx

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
