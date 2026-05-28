reset;

set terminal qt \
    font "Segoe UI:Bold,16" \
    size 1280,720 \
    # background rgb "#0d1117" \
    replotonresize \
    antialias \
    rounded;


set border lw 3 lc rgb "#30363d";
set tics nomirror tc rgb "#e6edf3";          
set grid xtics ytics lc rgb "#21262d" lw 1;  
set key tc rgb "#e6edf3";                   
# set object 1 rectangle from screen 0,0 to screen 1,1 fillcolor rgb "#0d1117" behind;
set tics scale 0.0;
set style line 102 lc rgb "#21262d" lw 0.5 dt 1;
set grid back ls 102;                 


set style line 1 lc rgb "#58a6ff" lw 2 pt 7 ps 0.8; # Blue
set style line 2 lc rgb "#3fb950" lw 2 pt 7 ps 0.8; # Green
set style line 3 lc rgb "#d29922" lw 2 pt 7 ps 0.8; # Gold

set style line 4 lc rgb "#f85149" lw 2 pt 7 ps 0.8; # Red
set style line 5 lc rgb "#bc8cff" lw 2 pt 7 ps 0.8; # Purple
set style line 6 lc rgb "#ffa657" lw 2 pt 7 ps 0.8; # Orange

set style line 7 lc rgb "#76e3ea" lw 2 pt 7 ps 0.8; # Cyan
set style line 8 lc rgb "#ff7b72" lw 2 pt 7 ps 0.8; # Coral
set style line 9 lc rgb "#a5d6ff" lw 2 pt 7 ps 0.8; # Sky Blue

set style line 10 lc rgb "#54ae69" lw 2 pt 7 ps 0.8; # Dark Green
set style line 11 lc rgb "#db61a2" lw 2 pt 7 ps 0.8; # Pink
set style line 12 lc rgb "#8b949e" lw 2 pt 7 ps 0.8; # Gray

set samples 2000;

set multiplot layout 2,2 title "{/:Bold=16 Wellen-Interaktionen}" tc rgb "#e6edf3" margins 0.1, 0.95, 0.1, 0.9 spacing 0.12


#set xlabel "t" tc rgb "#e6edf3" font "Segoe UI:Bold,16";
#set ylabel "E" tc rgb "#e6edf3" font "Segoe UI:Bold,16";
set xrange [0:0.07];
set yrange [-1.5:3];



# Amplituden-Modulation

set title "1. Amplituden-Modulation (Multiplikation):" tc rgb "#e6edf3" font "Segoe UI:Bold,18";

f_am(x) = sin(2*x*pi*450);                  
g_am(x) = sin(2*x*pi*15);
h_am(x) = g_am(x) * f_am(x);

plot f_am(x) ls 12 title "f(x) (450hz)", \
       g_am(x) ls 6 title "g(x) (15hz)", \
      -g_am(x) ls 6 lw 1.2 dt 3 title "-g(x)", \
       h_am(x) ls 1 title "f(x) * g(x)";



# Frequenz-Modulation

set title "2. Frequenz-Modulation (Verschachtelung):" tc rgb "#e6edf3" font "Segoe UI:Bold,18";

f_fm(x) = sin(2*x*pi*15);                  
h_fm(x) = f_fm(f_fm(x));


plot f_fm(x) ls 6 title "f(x) (15hz)", \
        h_fm(x) ls 1 title "f(f(x))";



# Additive Interferenz

set title "3. Additive Interferenz" tc rgb "#e6edf3" font "Segoe UI:Bold,18";

f_add(x) = 0.2 * sin(2*x*pi*300);                  
g_add(x) = sin(2*x*pi*15);
h_add(x) = f_add(x) + g_add(x);


plot f_add(x) ls 12 title "f(x) (300hz)", \
         g_add(x) ls 6 title "g(x) (15hz)", \
         h_add(x) ls 1 title "f(x) + g(x)";



# Phasenverschiebung (Destruktive Interferenz)

set title "4. Phasenverschiebung (Auslöschung)" tc rgb "#e6edf3" font "Segoe UI:Bold,18";

# Phasenverschiebung
phi = pi - 0.1

f_ph(x) = sin(2*x*pi*15);                  
g_ph(x) = sin(2*x*pi*15 + phi);
h_ph(x) = f_ph(x) + g_ph(x);


plot f_ph(x) ls 12 title "f(x)", \
         g_ph(x) ls 6 title "g(x + phi)", \
         h_ph(x) ls 1 title "f(x) + g(x + phi)";

unset multiplot
