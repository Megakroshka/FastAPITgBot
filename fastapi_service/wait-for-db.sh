#!/bin/sh
# wait-for-db.sh

set -e

host="$1"
shift
cmd="$@"

# Цикл, который ждет, пока TCP-соединение с хостом db на порту 3306 не станет доступным
until nc -z "$host" 3306; do
  >&2 echo "Database is unavailable - sleeping"
  sleep 1
done

>&2 echo "Database is up - executing command"
exec $cmd