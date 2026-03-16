#!/bin/sh
# Healthcheck for MariaDB
mysqladmin ping -h 127.0.0.1 -uroot -p"${MYSQL_ROOT_PASSWORD:-root_password}" >/dev/null 2>&1 || exit 1
