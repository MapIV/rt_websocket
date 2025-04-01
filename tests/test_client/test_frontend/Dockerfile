FROM node:lts-alpine
WORKDIR /vue
COPY ./vue ./
RUN apk update
RUN npm install
CMD ["yarn", "dev", "--host"]