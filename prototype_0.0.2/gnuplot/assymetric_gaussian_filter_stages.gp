set terminal svg font "Segoe UI:Bold,16" size 1920,1080 rounded;
set output "Assymetric_Gaussian_Stages.svg"

set border lw 3 lc rgb "#30363d";
set tics nomirror tc rgb "#e6edf3";          
set grid xtics ytics lc rgb "#21262d" lw 1;
set key tc rgb "#e6edf3";                   
set tics scale 0.0;
set style line 102 lc rgb "#21262d" lw 0.5 dt 1;
set grid back ls 102;                 


set style line 1 lc rgb "#58a6ff" lw 2 pt 7 ps 0.8  # Blue
set style line 2 lc rgb "#3fb950" lw 2 pt 7 ps 0.8  # Green
set style line 3 lc rgb "#d29922" lw 2 pt 7 ps 0.8  # Gold
set style line 4 lc rgb "#f85149" lw 2 pt 7 ps 0.8  # Red
set style line 5 lc rgb "#bc8cff" lw 2 pt 7 ps 0.8  # Purple
set style line 6 lc rgb "#ffa657" lw 2 pt 7 ps 0.8  # Orange
set style line 7 lc rgb "#76e3ea" lw 2 pt 7 ps 0.8  # Cyan
set style line 8 lc rgb "#ff7b72" lw 2 pt 7 ps 0.8  # Coral
set style line 9 lc rgb "#a5d6ff" lw 2 pt 7 ps 0.8  # Sky Blue
set style line 10 lc rgb "#54ae69" lw 2 pt 7 ps 0.8 # Dark Green
set style line 11 lc rgb "#db61a2" lw 2 pt 7 ps 0.8 # Pink
set style line 12 lc rgb "#8b949e" lw 2 pt 7 ps 0.8 # Gray


# set title "Designing an Assymetric Gaussian Filter" tc rgb "#e6edf3" font "Segoe UI:Bold,18";

set sample 5000

set xrange [0:1];
set yrange [-0.1:1.2];

# ### DESIGN STAGES:
# ##############################

# CONSTANTS:

PHYS_PEAK = 1.0 / 2.8  # Physiological Ratio: 1 to 1.8
PWM_RESOLUTION_IN_BIT = 10
MAX_PWM_VALUE = 2 ** PWM_RESOLUTION_IN_BIT - 1

# PARAMETERS:

dt_hold_in = 0.05
dt_hold_ex = 0.15


# 1 LINEAR BREATH CURVE:
################################
x1 = PHYS_PEAK - dt_hold_in
x2 =  PHYS_PEAK
x3 = 1 - dt_hold_ex


breath_linear(x) = (x < x1) \
    ? x / x1 \
    : (x < x2) \
    ? 1 \
    : (x < x3) \
    ? 1 - (x - x2) / (x3 - x2) \
    : 0;




#2 ADDED PASSIVE EXHALE:
################################
passive_exhale(x) = (x < x1) \
    ? x / x1 \
    : (x < x2) \
    ? 1 \
    : exp(-6.0 * (x - x2));



# 3 BREATH CURVE (GAUSS)
###################################################
# PARAMETERS:
peak_at = PHYS_PEAK  

normed_gauss(x, mue, sigma) = exp(-0.5 * ((x - mue)/sigma)**2)
sigma(mue) = mue / sqrt(log(MAX_PWM_VALUE))




# 4 ASSYMMETRIC GAUSS WITH BUILD-IN BREATH RATIO
###################################################

# INHALATION:
mue_in = peak_at - dt_hold_in
sigma_in = sigma(mue_in)

f_in(x) = normed_gauss(x, mue_in, sigma_in)
f_hold_in(x) = 1


# EXHALATION:
mue_ex = peak_at
sigma_ex = (x3 - x2) / sqrt(-2.0 * log(f_in(0)))

f_ex(x) = normed_gauss(x, mue_ex, sigma_ex)
f_hold_ex(x) = f_ex(x3) # f_in(0) # f_ex(1 - dt_hold_ex)


breath_gauss(x) = (x < mue_in) ? f_in(x) \
		: (x < peak_at) ? f_hold_in(x) \
		: (x < 1 - dt_hold_ex) ? f_ex(x) \
		: f_hold_ex(x)


# CORRECT OFFSET:
# offset = 0.0312652699740361  # at 0 & 1
breath_wave(x) = (breath_gauss(x) - breath_gauss(0)) \
	       / (breath_gauss(peak_at) - breath_gauss(0))

# NO OFFSET:
# if (breath_wave(0) == breath_wave(1)){
#     plot breath_wave(x) ls 1
# }



# COMBINED PLOTS:
###############################################
# plot breath_linear(x) ls 12 dt 2 title "Linear", \
#      breath_wave(x) ls 9 dt 2 title "Assymetric Gauss", \
#      breath_linear(x) * breath_wave(x) ls 2 title "Multiplied";

# plot passive_exhale(x) ls 12 dt 2 title "Passive Exhale", \
#      breath_wave(x) ls 9 dt 2 title "Asymmetric Gauss", \
#      passive_exhale(x) * breath_wave(x) ls 2 title "Multiplied";



# VISUALIZING THE STAGES:
###############################################

set multiplot layout 3,2 title "Assymetric Gaussian Filter" font "Segoe UI:Bold,20" tc rgb "#e6edf3"

set title "1. Linear Breath Model" tc rgb "#e6edf3"
plot breath_linear(x) ls 12 title "Linear Model"

set title "2. Added Exponential Exhale" tc rgb "#e6edf3"
plot passive_exhale(x) ls 12 title "Exponential Model"

set title "3. Switching to a Bell Curve" tc rgb "#e6edf3"
plot normed_gauss(x, PHYS_PEAK, 0.18) ls 3 title "Normed Gaussian"

set title "4. Linear x Bell" tc rgb "#e6edf3"
plot breath_linear(x) ls 12 dt 2 title "Linear", \
     normed_gauss(x, PHYS_PEAK, 0.18) ls 3 dt 2 title "Gauss", \
     breath_linear(x) * normed_gauss(x, PHYS_PEAK, 0.18) ls 1 title "Multiplied"

set title "5. Exponential x Bell" tc rgb "#e6edf3"
plot passive_exhale(x) ls 12 dt 2 title "Passive Exhale", \
     normed_gauss(x, PHYS_PEAK, 0.18) ls 3 dt 2 title "Gauss", \
     passive_exhale(x) * normed_gauss(x, PHYS_PEAK, 0.18) ls 1 title "Multiplied"

set title "6. Asymmetric Bell Curve"
plot breath_wave(x) ls 2 title "Final"

unset multiplot
set output