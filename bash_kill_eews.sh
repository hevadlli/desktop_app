# Menutup program Python yang sedang berjalan
pids=$(ps aux | grep -E "python3 eews_part[1-5].py" | grep -v grep | awk '{print $2}')
if [ ! -z "$pids" ]; then
    kill -9 $pids
fi