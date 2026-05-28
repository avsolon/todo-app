FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY ./site /usr/share/nginx/html/site
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]