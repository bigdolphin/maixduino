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

# Register i2s(i2s1) pin
fm.register(34,fm.fpioa.I2S1_OUT_D1, force=True)
fm.register(35,fm.fpioa.I2S1_SCLK, force=True)
fm.register(33,fm.fpioa.I2S1_WS, force=True)

# Function to record and playback
def recorder(filepath,duration=5,playback=False):
    # user setting
    record_rate   = 16000
    # in seconds, maximum 10s
    if duration > 10:
        duration = 10
    record_time   = duration
    # default seting
    record_points = 2048
    record_ch     = 2
    # Init i2s(i2s0)
    rec_dev = I2S(I2S.DEVICE_0)
    rec_dev.channel_config(rec_dev.CHANNEL_0, rec_dev.RECEIVER, align_mode=I2S.STANDARD_MODE)
    rec_dev.set_sample_rate(record_rate)
    print(rec_dev)
    # Init i2s(i2s1)
    wav_dev = I2S(I2S.DEVICE_1)
    if playback:
        # config i2s according to audio info
        wav_dev.channel_config(wav_dev.CHANNEL_1, I2S.TRANSMITTER,resolution = I2S.RESOLUTION_16_BIT ,cycles = I2S.SCLK_CYCLES_32, align_mode = I2S.RIGHT_JUSTIFYING_MODE)
        wav_dev.set_sample_rate(record_rate)
    try:
        # init audio
        wav_recorder = audio.Audio(path=filepath, is_create=True, samplerate=record_rate)
        queue = []
        record_frame_cnt = record_time*record_rate//record_points
        print("[PLAYBACK] Recording in %d seconds..." %(record_time))
        # Record and play
        for i in range(record_frame_cnt):
            tmp = rec_dev.record(record_points*record_ch)
            if playback:
                wav_dev.play(tmp)
            if len(queue) > 0:
                ret = wav_recorder.record(queue[0])
                queue.pop(0)
            rec_dev.wait_record()
            queue.append(tmp)
            #print("[REC] " + str(i) + ":" + str(time.ticks()))
        # Done
        print("[PLAYBACK] Done!")
        wav_recorder.finish()
    except Exception as e:
        print("[Exception] %s" % (e))

# Record and playback in 5s
recorder("/sd/record.wav",5,True)
