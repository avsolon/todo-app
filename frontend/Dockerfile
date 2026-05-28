FROM nginx:alpine

# Копируем конфиг Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем статические файлы
COPY ./site /usr/share/nginx/html/spisok-del-todo-app

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]