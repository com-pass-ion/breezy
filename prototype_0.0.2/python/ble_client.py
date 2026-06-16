"""
Prototype 2: Live Visualization of the Heart Beat

- Sensor: Polar H10 (130Hz)
- Parser: ecg_sdk (self-written)
- bleak: Communication via Bluetooth
- pingpong: Unihiker -> Microcontroller (20-30Hz)
- asyncio: Concurrency


-> Frequenz anpassen
"""

from __future__ import annotations
import asyncio
from collections import deque
from typing import Awaitable, Callable, AsyncIterator, Tuple
import time
from bleak import BleakScanner, BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from ecg_sdk import ECG
from pinpong.board import Board, Pin, PWM


NAME = "Polar H10"
PARTIAL_NAME = "Polar"
ADDRESS = "24:AC:AC:14:D4:93"

QUEUE = deque(maxlen=73)

PIN = Pin.P23
FREQUENCY = 1023
ABS_MAX_DUTY = 1023
MIN_DUTY = 20
MAX_DUTY = ABS_MAX_DUTY - MIN_DUTY



DELAY = 0.03
TIME_PER_LOOP = 0.030000063164062674
TIME_PER_CYCLE = 30.54

async def init_pwm() -> PWM:
    """
    Initialize the Unihiker board and return a configured PWM
    instance.
    """
    Board("UNIHIKER").begin()
    led_pwm = PWM(Pin(PIN))
    led_pwm.freq(FREQUENCY)
    led_pwm.duty(0)
    await asyncio.sleep(1)
    return led_pwm

async def exit_gracefully(pwm: PWM | None) -> None:
    """
    Stop PWM and clean up the board.
    """
    if pwm is not None:
        try:
            pwm.duty(0)
            pwm.deinit()
        except Exception as e:
            print("[Shutdown] PWM already shut down. o.O", e)
    print("See you next time! =)")


async def scan_for_available_devices(sc: BleakScanner,
                                     default_address: str = ADDRESS,
                                     backup_name: str = PARTIAL_NAME
                                     ) -> Tuple[BLEDevice, ...]:
    """
    Returns tuple with addresses of backup devices
    chosen by partial name *backup_name* in device's
    name.
    """
    devices = await sc.discover()

    available_default = tuple(filter(lambda dev: dev.address == default_address, devices))

    if available_default:
        return available_default

    return (tuple(dev for dev in devices
                  if dev.name is not None
                  and backup_name in dev.name))


def cp_callback(sender: BleakGATTCharacteristic, data: bytearray) -> Awaitable[None] | None:
    """
    Callback for Control Point.
    """
    r = ECG.response(bytes(data))
    print(f"[Control Point:] {r.op_code}: {r.error_code}")

def data_callback(sender: BleakGATTCharacteristic, data: bytearray) ->  Awaitable[None] | None:
    """
    Callback for data processing.
    """
    _, samples = ECG.samples(bytes(data))  # _ holds timestamp
    global QUEUE
    QUEUE.extend(samples)
    # print(str(timestamp) + "," +  ",".join(str(sample) for sample in samples))


### READ:
def make_auto_mapper(min_duty: int = 0,
                     max_duty: int = 1023,
                     smoothing_rate: float = 0.01) -> Callable:
    """
    Takes *value* and maps it to a [0, 1023] with a weighted-average.
    """
    min_ecg: float = float("inf")
    max_ecg: float = float("-inf")
    alpha: float = smoothing_rate
    min_val: int = min_duty
    max_val: int = max_duty
    last_val: int = min_val


    def linear_mapper(val: int | None) -> int:
        nonlocal min_ecg,  max_ecg, alpha, min_val, max_val, last_val
        if val is not None:
            min_ecg = min(min_ecg * (1 - alpha) + alpha * val, val)
            max_ecg = max(max_ecg * (1 - alpha) + alpha * val, val)

            if max_ecg - min_ecg < 1e-6:
                last_val = min_val
                return min_val

            mapped = min_val + \
                int((val - min_ecg) / (max_ecg - min_ecg) * (max_val - min_val))
            
            clamped = max(min(mapped, max_val), min_val)
            last_val = clamped
            return clamped
        
        return last_val


    return linear_mapper

mapping = make_auto_mapper()


def reduce_freq(inp_freq_hz: int, out_freq_hz: int , data: deque = QUEUE) -> deque:
    """
    Reduces list of *data* points, f.e. 130 to 4 Hz, by calculating arithmetic mean.
    Maybe use a more moving/factor approach. =)
    """
    if not data:
        return deque()

    step = max(1, round(inp_freq_hz / out_freq_hz))
    acc = []
    data_list= list(data)
    
    for i in range(0, len(data), step):
        data_points = data_list[i:i+step]
        mean_dp = int(sum(data_points) / len(data_points))
        acc.append(mean_dp)

    return deque(acc)


async def timed_iterator(queue: deque, inp_freq: int = 130, out_freq: int = 20) -> AsyncIterator[int | None]:
    """Combining samples and sample rate."""
    interval = 1.0/out_freq

    while True:
        q = reduce_freq(inp_freq, out_freq, queue)
        queue.clear()
        
        if not q:
            yield None
            await asyncio.sleep(interval)
            continue
        
        for val in q:
            yield val
            await asyncio.sleep(interval)



async def main():
    """
    main
    """
    pwm = await init_pwm()

    sc = BleakScanner()
    available_devices: Tuple[BLEDevice, ...] = await scan_for_available_devices(sc)

    if available_devices:
        print("Available Devices:\n", "".join(f"{av.name}: {av.address} \n" for av in available_devices))
        chosen = available_devices[0]
        print("Chosen Device:\n", f"{chosen.name}: {chosen.address} \n")


        try:
            server = BleakClient(chosen)
            print("[Init] Trying to connect...")
            await server.connect(timeout=20.0)
            print("[Init] Connected.")

            await server.start_notify(ECG.DATA_STREAM_UUID, data_callback)
            await server.start_notify(ECG.CONTROL_POINT_UUID, cp_callback)

            await server.write_gatt_char(ECG.CONTROL_POINT_UUID, ECG.START_CMD, response=True)

            it = timed_iterator(QUEUE, 130, 20)  ### hier skalieren über deque und dann logik vereinfachen
            start_time = time.time()
            last_update = start_time - 0.05
            async for val in it:
                # print(val)
                current_time = time.time()
                if current_time - last_update > 0.05:
                    pwm.duty(mapping(val))
                    last_update = current_time
                if current_time - start_time > 60:
                    break
            # 5 minutes recording time?
            # CSV output
            await asyncio.sleep(300)

            await server.write_gatt_char(ECG.CONTROL_POINT_UUID, ECG.STOP_CMD , response=True)

            await server.stop_notify(ECG.DATA_STREAM_UUID)
            await server.stop_notify(ECG.CONTROL_POINT_UUID)

            await asyncio.sleep(1)
            await server.disconnect()
            print("[ShutDown] Server disconnected.")
            
        except Exception as e:
            print(e)
            
        finally:
            await asyncio.sleep(1)  
            await exit_gracefully(pwm)


if __name__ == "__main__":
    asyncio.run(main())
