FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --omit=dev

COPY . .

# مجلد الصور إذا لم يكن موجوداً
RUN mkdir -p uploads

EXPOSE 10000

ENV NODE_ENV=production

CMD ["node", "index.js"]
