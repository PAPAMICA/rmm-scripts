#!/usr/bin/env bash

# Calcul du %CPU utilisé en utilisant /proc/stat (natif Linux, pas de dépendances externes)
# Format: cpu user nice system idle iowait irq softirq steal guest guest_nice

# Vérification que /proc/stat existe
if [ ! -f /proc/stat ]; then
    exit 3
fi

# Lecture des stats CPU à deux moments différents
stats1=$(head -n 1 /proc/stat)
sleep 1
stats2=$(head -n 1 /proc/stat)

# Calcul du pourcentage CPU utilisé avec awk (disponible par défaut sur Linux)
cpu_percent=$(awk -v s1="$stats1" -v s2="$stats2" '
BEGIN {
    split(s1, a1);
    split(s2, a2);
    # user, nice, system, idle, iowait
    idle1 = a1[5];
    idle2 = a2[5];
    total1 = a1[2] + a1[3] + a1[4] + a1[5] + a1[6];
    total2 = a2[2] + a2[3] + a2[4] + a2[5] + a2[6];
    idle_diff = idle2 - idle1;
    total_diff = total2 - total1;
    if (total_diff == 0) {
        print 0;
    } else {
        idle_percent = (idle_diff * 100) / total_diff;  
        cpu_percent = 100 - idle_percent;
        printf "%.0f", cpu_percent;
    }
}')

cpu_int=$cpu_percent

echo "$cpu_int"

if [ "$cpu_int" -gt 90 ]; then
    exit 1   # Alarm
elif [ "$cpu_int" -gt 75 ]; then
    exit 2   # Warning
else
    exit 0   # OK
fi
