FROM node:20-alpine AS build
WORKDIR /app
ARG VITE_API_URL=http://127.0.0.1:8000
ENV VITE_API_URL=${VITE_API_URL}
COPY frontend/package*.json /app/
RUN npm ci
COPY frontend /app
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
