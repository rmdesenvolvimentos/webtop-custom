#!/bin/bash
PREV_FILE="/tmp/cpu_stat_prev.tmp"

# Read /proc/stat CPU
read -r _ u n s i w irq sirq st rest < /proc/stat
total=$((u + n + s + i + w + irq + sirq + st))
idle=$((i + w))

cpu_pct=0
if [ -f "$PREV_FILE" ]; then
    read -r p_total p_idle < "$PREV_FILE"
    d_total=$((total - p_total))
    d_idle=$((idle - p_idle))
    if [ "$d_total" -gt 0 ]; then
        cpu_pct=$(( (100 * (d_total - d_idle)) / d_total ))
    fi
fi
echo "$total $idle" > "$PREV_FILE"

# Read /proc/meminfo
mem_total=0
mem_avail=0
while IFS=': ' read -r key val _; do
    case "$key" in
        MemTotal) mem_total=$val ;;
        MemAvailable) mem_avail=$val ;;
    esac
    [ "$mem_total" -gt 0 ] && [ "$mem_avail" -gt 0 ] && break
done < /proc/meminfo

mem_used=$((mem_total - mem_avail))
mem_pct=$(( (100 * mem_used) / mem_total ))
used_gb=$(awk "BEGIN {printf \"%.1f\", $mem_used/1048576}")
total_gb=$(awk "BEGIN {printf \"%.1f\", $mem_total/1048576}")

echo "<txt><span size=\"small\" color=\"#a0a0a0\">CPU:</span> <b>${cpu_pct}%</b>
<span size=\"small\" color=\"#a0a0a0\">RAM:</span> <b>${mem_pct}%</b> <span size=\"small\" color=\"#888888\">(${used_gb}G)</span> </txt>"
echo "<tool>Uso do Sistema:
CPU: ${cpu_pct}%
RAM: ${used_gb} GB / ${total_gb} GB (${mem_pct}%)
Clique para abrir o Gerenciador de Tarefas</tool>"
echo "<click>win-taskmgr</click>"
