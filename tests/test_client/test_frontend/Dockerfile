FROM node:lts-alpine
WORKDIR /vue
COPY ./vue ./
RUN apk update
CMD ["yarn", "dev", "--host"]