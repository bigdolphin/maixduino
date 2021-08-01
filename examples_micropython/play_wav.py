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

# Register i2s(i2s1) pin
fm.register(34,fm.fpioa.I2S1_OUT_D1, force=True)
fm.register(35,fm.fpioa.I2S1_SCLK, force=True)
fm.register(33,fm.fpioa.I2S1_WS, force=True)

# Function to play wav file
def player(filepath,vol=80):
    # Init i2s(i2s1)
    wav_dev = I2S(I2S.DEVICE_1)
    ret = None
    try:
        # Init audio
        audio_player = audio.Audio(path = filepath)
        audio_player.volume(vol)
        # read audio info
        wav_info = audio_player.play_process(wav_dev)
        # config i2s according to audio info
        wav_dev.channel_config(wav_dev.CHANNEL_1, I2S.TRANSMITTER,resolution = I2S.RESOLUTION_16_BIT ,cycles = I2S.SCLK_CYCLES_32, align_mode = I2S.RIGHT_JUSTIFYING_MODE)
        wav_dev.set_sample_rate(wav_info[1])
        print("[PLAY WAV] Playing %s..." %(filepath))
        # loop to play audio
        while True:
            ret = audio_player.play()
            if ret == None:
                print("[ERROR] Audio format error!")
                break
            elif ret==0:
                break
        print("[PLAY WAV] Done!")
        audio_player.finish()
    except Exception as e:
        print("[Exception] %s" % (e))
    return ret

# Play wav file with volume = 100
player("/sd/record.wav",100)
