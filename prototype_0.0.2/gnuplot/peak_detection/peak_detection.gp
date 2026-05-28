load "theme.gp"


set title "Peak Detection" tc rgb "#e6edf3" font "Segoe UI:Bold,18";

# set xlabel "x" tc rgb "#e6edf3" font "Segoe UI:Bold,16";
# set ylabel "y" tc rgb "#e6edf3" font "Segoe UI:Bold,16";

set samples 2000
set xrange [0:1]
set yrange [-0.1:1.1]


# BUILDING TEST FUNCTIONS FOR PEAK DETECTION:
#############################################

# HELPERS:

_modulo_1(x) = x - floor(x)
_modulo_2(x) = floor(x) % 2


# FUNCTIONS:

triangle(x) = (_modulo_2(2 * x) == 0) ? 2 * _modulo_1(x) : 2 * (1.0 - _modulo_1(x))


stair(x) = (_modulo_2(2 * (x + 0.05)) == 0) \
	 ? (floor(abs(_modulo_1(x + 0.05) * 10)) / 5.0) \
	 : (-floor(abs(_modulo_1(x + 0.05) * 10)) / 5.0 + 2)


noise(x) = (rand(0) - 1)/ 10.0


# COMPOSITIONS:

triangle_with_noise(x) = triangle(x) + noise(x)

stair_with_noise(x) = stair(x) + noise(x)

variable_max(x) = (int(x) % 2 == 0) ? triangle(x) : 0.5 * stair(x)


# HRV DATA:

unset xrange
unset yrange

HRV_DATA = "inverted_hrv_sample.csv"
set table $DATA
plot HRV_DATA using 1 with table
unset table

N = |$DATA|




# PEAK DETECTION:

inf_pos = +1e9
inf_neg = -1e9

min_x = 0
max_x = 0

min_y = inf_pos
max_y = inf_neg

min_thrsh = 0
max_thrsh = 500

# reset_max = 0.8
# reset_min = 0.8

resolution = 100.0
cycles = 4
#N = int(cycles * resolution)

is_min = 0
is_max = 0

last_y = 0
last_max_x = -1
last_min_x = -1

array maxima[N]
array minima[N]
array extrema[N]

do for [i=1:N] {
    
    # time
    x = i
    # / resolution
    # signal
    y = $DATA[i] * (-1)  # invertiertes Signal

    # filter max
    if (y < max_thrsh && last_y >= max_thrsh && x > last_max_x + 20) {
	# detects max the moment after the peak
	maxima[i] = max_y
	extrema[i] = max_y
	print "Max: (", max_x, " / ", max_y, ")"
	max_y = inf_neg
	last_max_x = max_x
    }

    # filter min
    if (y > min_thrsh && last_y <= min_thrsh && x > last_min_x + 20) {
	if (min_x > 110) {
	    minima[i] = min_y
	    extrema[i] = min_y
	    print "Min: (", min_x, " / ", min_y, ")"
	}
	min_y = inf_pos
	last_min_x = min_x
    }

    # detect max
    if (y >= last_y && y >= max_y){
	max_x = x
	max_y = y
    }
    
    # detect min
    if (y <= last_y && y <= min_y) {
	min_x = x
	min_y = y
    }

    last_y = y

}




plot HRV_DATA using 0:(-$1) with lines ls 1 notitle, \
     maxima ls 2 notitle, \
     minima ls 3 notitle
