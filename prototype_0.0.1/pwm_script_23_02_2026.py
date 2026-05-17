"""
Breathing LED Prototype for Unihiker
"""
from __future__ import annotations
from typing import Iterator, Tuple, Callable
from math import exp
from time import perf_counter, sleep
from pinpong.board import Board, Pin, PWM

PIN = Pin.P23
FREQUENCY = 1023
ABS_MAX_DUTY = 1023
MIN_DUTY = 20
MAX_DUTY = ABS_MAX_DUTY - MIN_DUTY

DELAY = 0.03
TIME_PER_LOOP = 0.030000063164062674
TIME_PER_CYCLE = 30.54

# STATE for *_measure_time*
COUNT = 0
MEASUREMENTS = []
LOOP_TIMES = []

# Adapts breathing frequency (int -> rounding error)
BREATH_LENGTH = 12
STEP = int(TIME_PER_CYCLE / BREATH_LENGTH)


def gaussian(time: float, mu: float = 0.357142857, sigma: float = 0.18) -> float:
    """
    Applies normalized Gaussian function to *time* with given *mu* and *sigma*.
    time: Normalized time [0, 1].
    mu: The peak position (typically 0.5 for a symmetric pulse).
    sigma: The width of the pulse (recommended 0.1 to 0.2).
    Defaults try to mimic physiological breathing.
    """
    return exp(-0.5 * ((time - mu) / sigma) ** 2)


def gamma_correction(value: float, gamma: float = 2.8) -> float:
    """
    Applies Gamma Correction with specified *gamma* to *value*.
    *gamma* < 1: Concave
    Small input values are greatly expanded, large ones are compressed.
    *gamma* > 1: Convex
    Large input values are greatly expanded, small ones are
    compressed.
    """
    return  value ** gamma


def init_pwm() -> PWM:
    """
    Initialize the Unihiker board and return a configured PWM
    instance.
    """
    Board("UNIHIKER").begin()
    led_pwm = PWM(Pin(PIN))
    led_pwm.freq(FREQUENCY)
    led_pwm.duty(0)
    sleep(1)
    return led_pwm


def exit_gracefully(pwm: PWM) -> None:
    """
    Stop PWM and clean up the board.
    """
    pwm.duty(0)
    pwm.deinit()
    print("See you next time! =)")


def _measure_time(t: str = "last") -> None:
    """
    Helper measuring times, calculating average and producing output.
    """
    global COUNT, MEASUREMENTS, LOOP_TIMES
    if t =="first":
        MEASUREMENTS += [perf_counter()]
        return
    if t == "loop":
        MEASUREMENTS += [perf_counter()]
        LOOP_TIMES += [MEASUREMENTS[-1] - MEASUREMENTS[-2]]
        COUNT += 1
        return
    if t == "last" and LOOP_TIMES:
        average = sum(LOOP_TIMES) / len(LOOP_TIMES)
        print(f"Average Loop Time:  {average}\n\n" +\
              f"Expected Loop Time: {DELAY}")
        print(f"Total Time since first measurement:  {MEASUREMENTS[-1] - MEASUREMENTS[0]}")


def yield_duty_cyclic(pattern: Tuple[int, ...], repeat: int = 2) -> Iterator[int]:
    """
    Yield duties repeatedly for *repeat* full cycles.
    """
    for _ in range(repeat):
        yield from pattern


def create_breath_pattern(fn: Callable[[float], float]) -> Tuple[int, ...]:
    """
    Convert a normalised waveform into PWM duties.
    """
    scale = MAX_DUTY - MIN_DUTY
    offset = MIN_DUTY
    return tuple(int((fn(x / FREQUENCY) * scale + offset))
                 for x in range(0, FREQUENCY, STEP))


def modulate_with(signal_fn: Callable[[float], float],
                  mod_fn: Callable[[float], float]) ->  Callable[[float], float]:
    """
    Return a new function that applies *mod_fn* to the output of *signal_fn*.
    """
    return lambda x: mod_fn(signal_fn(x))


def demo(repeat: int = 2, dry_run: bool = False) -> None:
    """Demo using a *gaussian* and *gamma_correction*
    to create a breathing pattern. """
    pattern = create_breath_pattern(modulate_with(gaussian, gamma_correction))
    lut = yield_duty_cyclic(pattern, repeat)
    if dry_run:
        print(list(lut))
        return

    led_pwm = init_pwm()
    last_duty = led_pwm.duty()
    _measure_time("first")
    try:
        target_time = perf_counter()
        for duty in lut:
            if last_duty != duty:
                led_pwm.duty(duty)
            target_time += DELAY
            while perf_counter() < target_time :
                pass
            last_duty = duty
            _measure_time("loop")
    except KeyboardInterrupt:
        pass
    finally:
        _measure_time("last")
        print("Time expected: ", TIME_PER_LOOP * MAX_DUTY / STEP * repeat)
        exit_gracefully(led_pwm)


if __name__ == "__main__":
    demo(repeat=4, dry_run=False)
