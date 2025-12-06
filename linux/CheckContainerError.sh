#!/usr/bin/env bash

# Vérifie que docker est dispo
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is not installed"
    exit 0
fi

# Récupération des conteneurs arrêtés
container_ids=$(docker ps -a -f status=exited -q 2>/dev/null)
if [ $? -ne 0 ]; then
    exit 3
fi

# Compte des conteneurs arrêtés
num_failed=$(echo "$container_ids" | grep -c .)

echo "$num_failed"

if [ "$num_failed" -gt 0 ]; then
    exit 1   # Alarm
else
    exit 0   # OK
fi
