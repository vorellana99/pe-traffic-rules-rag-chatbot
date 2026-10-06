FROM node:20-slim

WORKDIR /app

# Instala dependencias (capa cacheada). En dev, ./frontend se monta encima,
# pero node_modules queda en un volumen anónimo (ver docker-compose.yml).
COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
