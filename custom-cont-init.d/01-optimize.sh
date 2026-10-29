#!/bin/bash
echo '[optimize] Enxugando servicos desnecessarios...'

# 1. Desativar PulseAudio substituindo o binario por um stub silencioso
if [ ! -f /usr/bin/pulseaudio.bak ]; then
  mv /usr/bin/pulseaudio /usr/bin/pulseaudio.bak
fi
cat << 'PA_EOF' > /usr/bin/pulseaudio
#!/bin/sh
touch /defaults/pid
touch /dev/shm/audio.lock
exec sleep infinity
PA_EOF
chmod +x /usr/bin/pulseaudio
pkill -9 -f pulseaudio.bak 2>/dev/null || true
pkill -9 -f /usr/bin/pulseaudio 2>/dev/null || true

# 2. Desativar AT-SPI
rm -f /etc/xdg/autostart/at-spi-dbus-bus.desktop 2>/dev/null || true
chmod 0000 /usr/libexec/at-spi-bus-launcher /usr/libexec/at-spi2-registryd 2>/dev/null || true

# 3. Desativar UDisks2 e GVFS volume monitor
chmod 0000 /usr/libexec/udisks2/udisksd /usr/libexec/gvfs-udisks2-volume-monitor 2>/dev/null || true

# 4. Desativar CUPS
chmod 0000 /usr/sbin/cupsd 2>/dev/null || true
rm -rf /config/.XDG/selkies-cups 2>/dev/null || true

# 5. Reduzir workers do Nginx para 1
sed -i 's/worker_processes auto;/worker_processes 1;/g' /etc/nginx/nginx.conf 2>/dev/null || true

echo '[optimize] Otimizacoes aplicadas com sucesso.'
