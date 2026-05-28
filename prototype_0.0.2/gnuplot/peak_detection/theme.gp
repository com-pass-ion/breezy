reset session;

set terminal qt \
    font "Segoe UI:Bold,16" \
    size 800,600 \
    replotonresize \
    antialias \
    rounded;


set border lw 3 lc rgb "#30363d";
set tics nomirror tc rgb "#e6edf3";          
set grid xtics ytics lc rgb "#21262d" lw 1;  
set key tc rgb "#e6edf3";                   
set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor rgb "#0d1117" behind;
set tics scale 0.0;
set style line 102 lc rgb "#21262d" lw 0.5 dt 1;
set grid back ls 102;                 



# --- GitHub Dark Palette (Styles 1-12) ---

# Your original three:
set style line 1 lc rgb "#58a6ff" lw 2 pt 7 ps 0.8  # Blue
set style line 2 lc rgb "#3fb950" lw 2 pt 7 ps 0.8  # Green
set style line 3 lc rgb "#d29922" lw 2 pt 7 ps 0.8  # Gold

# Additional suiting colors:
set style line 4 lc rgb "#f85149" lw 2 pt 7 ps 0.8  # Red
set style line 5 lc rgb "#bc8cff" lw 2 pt 7 ps 0.8  # Purple
set style line 6 lc rgb "#ffa657" lw 2 pt 7 ps 0.8  # Orange
set style line 7 lc rgb "#76e3ea" lw 2 pt 7 ps 0.8  # Cyan
set style line 8 lc rgb "#ff7b72" lw 2 pt 7 ps 0.8  # Coral
set style line 9 lc rgb "#a5d6ff" lw 2 pt 7 ps 0.8  # Sky Blue
set style line 10 lc rgb "#54ae69" lw 2 pt 7 ps 0.8 # Dark Green
set style line 11 lc rgb "#db61a2" lw 2 pt 7 ps 0.8 # Pink
set style line 12 lc rgb "#8b949e" lw 2 pt 7 ps 0.8 # Gray

