#!/usr/bin/env bash

# Vérifie que docker est dispo
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is not installed"
    exit 0
fi

# Récupération des conteneurs en cours d'exécution
container_ids=$(docker ps -q 2>/dev/null)
if [ $? -ne 0 ]; then
    exit 0
fi

# Compte des conteneurs actifs
num_containers=$(echo "$container_ids" | grep -c .)

echo "$num_containers"
exit 0   # OK
