FROM nginx

RUN mkdir /usr/share/nginx/html/storage
COPY nginx/nginx.conf.tmp /etc/nginx/nginx.conf

CMD nginx -g "daemon off;"
