docker container create --name doccano -e "ADMIN_USERNAME=admin" -e "ADMIN_EMAIL=admin@admin.com" -e "ADMIN_PASSWORD=password" -p 8000:8000 doccano/doccano

docker container start doccano