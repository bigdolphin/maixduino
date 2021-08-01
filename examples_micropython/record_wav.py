import time
from fpioa_manager import fm
from Maix import I2S
import audio

###################################
print('\n-----------------------------')
# Check frequencies and overclock
import gc, micropython
from Maix import freq, GPIO, utils
from machine import reset
import os

cpu_frq, kpu_frq=freq.get()
print("\nCPU Frq = %d MHz" % (cpu_frq))
print("KPU Frq = %d MHz" % (kpu_frq))

if cpu_frq != 546 or kpu_frq != 450:
    print("Removing old frequency...")
    os.remove("freq.conf")
    print("Overclocking CPU to 546 MHz and KPU to 450 MHz...")
    # kpu frequency is pll1/kpu_div
    freq.set (cpu=546, pll1=450, kpu_div=1)

gc.enable()
gc.collect()
gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
micropython.mem_info()
mem_heap = utils.gc_heap_size()
heap_free = utils.heap_free()
print("Heap size: %d bytes, free: %d bytes" % (mem_heap,heap_free))
if mem_heap != 393216:
    print("Decreasing GC heap size...")
    utils.gc_heap_size(393216)
    reset()
print('-----------------------------')
###################################

# Register i2s(i2s0) pin
fm.register(20,fm.fpioa.I2S0_IN_D0, force=True)
fm.register(19,fm.fpioa.I2S0_WS, force=True)
fm.register(18,fm.fpioa.I2S0_SCLK, force=True)

# Function to record wav file
def recorder(filepath,duration=5):
    # user setting
    record_rate   = 16000
    # in seconds, maximum 10s
    if duration > 10:
        duration = 10
    # default seting
    record_points = 2048
    record_ch     = 2
    # Init i2s(i2s0)
    rec_dev = I2S(I2S.DEVICE_0)
    rec_dev.channel_config(rec_dev.CHANNEL_0, rec_dev.RECEIVER, align_mode=I2S.STANDARD_MODE)
    rec_dev.set_sample_rate(record_rate)
    print(rec_dev)
    try:
        # init audio
        wav_recorder = audio.Audio(path=filepath, is_create=True, samplerate=record_rate)
        queue = []
        record_frame_cnt = record_time*record_rate//record_points
        # Record and save
        print("[REC WAV] Recording in %d seconds..." %(record_time))
        for i in range(record_frame_cnt):
            tmp = rec_dev.record(record_points*record_ch)
            if len(queue) > 0:
                ret = wav_recorder.record(queue[0])
                queue.pop(0)
            rec_dev.wait_record()
            queue.append(tmp)
            #print("[REC] " + str(i) + ":" + str(time.ticks()))
        # Done
        print("[REC WAV] Done!")
        wav_recorder.finish()
    except Exception as e:
        print("[Exception] %s" % (e))

# Record in 5s
recorder("/sd/record.wav",5)
