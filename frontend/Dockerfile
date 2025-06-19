# Use the official Nginx image from Docker Hub
FROM nginx:alpine

# Copy the static content (HTML, CSS, JS) into the Nginx server directory
COPY ./index.html /usr/share/nginx/html/
COPY ./style.css /usr/share/nginx/html/
COPY ./script.js /usr/share/nginx/html/

# Copy our custom Nginx configuration
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for the web server
EXPOSE 80
