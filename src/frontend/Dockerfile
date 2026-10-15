FROM node:22-alpine

WORKDIR /app

COPY .yarnrc.yml ./
COPY package.json yarn.lock ./

RUN yarn install --immutable


# Copia o código do frontend
COPY . .

# Exposição da porta interna
EXPOSE 3000

CMD ["yarn", "dev", "--host", "0.0.0.0", "--port", "3000"]
