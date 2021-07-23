# Note: model file must be transferred to board

import sensor, image, time, lcd
import KPU as kpu

###################################
# Check frequencies and overclock
import gc, micropython
from Maix import freq, GPIO, utils
from machine import reset

cpu_frq, kpu_frq=freq.get()
print("\nCPU Frq = %d MHz" % (cpu_frq))
print("KPU Frq = %d MHz" % (kpu_frq))

if cpu_frq != 546 or kpu_frq != 450:
    print("Removing old frequency...")
    os.remove("freq.conf")
    print("Overclocking CPU to 546 MHz and KPU to 450 MHz...")
    # kpu frequency is pll1/kpu_div
    freq.set (cpu=546, pll1=450, kpu_div=1)

gc.collect()
micropython.mem_info()
mem_heap = utils.gc_heap_size()
print("Heap size: %d bytes" % (mem_heap))
if mem_heap < 1000000:
    print("Increasing heap size...")
    utils.gc_heap_size(1048576)
    reset()
print('-----------------------------')
###################################

lcd.init(freq=15000000)
lcd.rotation(1)
lcd.clear(0,0,0)

lcd.draw_string(20,20, "------Big Dolphin-----", lcd.WHITE, lcd.BLACK)
lcd.draw_string(20,40, "----Digit Regconizing----", lcd.WHITE, lcd.BLACK)
lcd.draw_string(20,60, "- CPU Frq: " + str(cpu_frq) + " MHz", lcd.WHITE, lcd.BLACK)
lcd.draw_string(20,80, "- KPU Frq: " + str(kpu_frq) + " MHz", lcd.WHITE, lcd.BLACK)
lcd.draw_string(20,100, "- Loading model...", lcd.WHITE, lcd.BLACK)
task_mnist = kpu.load("mnist.kmodel")

lcd.draw_string(20,120, "- Loading Camera...", lcd.WHITE, lcd.BLACK)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
# set to 224x224 input
sensor.set_windowing((224, 224))
sensor.set_vflip(0)
sensor.set_hmirror(0)
sensor.run(1)
sensor.skip_frames(30)

time.sleep(1)
lcd.clear()

while True:
    # read camera
    img_mnist = sensor.snapshot()
    # Rotate image
    img_mnist.set(hmirror=True, vflip=False, transpose=True)
    # Convert to gray
    img_mnist1 = img_mnist.to_grayscale(1)
    # Resize to mnist input 28x28
    img_mnist1 = img_mnist1.resize(28,28)
    # Histogram equalization
    img_mnist1 = img_mnist1.histeq(adaptive=True)
    # Get histogram
    img_hist = img_mnist1.get_histogram()
    # Get optimal threshold
    otsu_th = img_hist.get_threshold()
    otsu_l = otsu_th.l_value()
    otsu_a = otsu_th.a_value()
    otsu_b = otsu_th.b_value()
    # Thresholding image
    img_mnist1 = img_mnist1.binary([(0, otsu_l), (-128, otsu_a),(-128, otsu_b)])
    # Preprocessing pictures, eliminate dark corner
    img_mnist1.strech_char(1)
    # Generate data for ai
    img_mnist1.pix_to_ai()
    # Run neural network model
    fmap_mnist = kpu.forward(task_mnist,img_mnist1)
    # Get result (10 digit's probability)
    plist_mnist = fmap_mnist[:]
    # Get max probability
    pmax_mnist = max(plist_mnist)
    # Get the digit
    max_index_mnist = plist_mnist.index(pmax_mnist)
    # Print results
    print("Detected number: %d " % (max_index_mnist) + ", confidence: %.1f%% " % (pmax_mnist*100))
    # Show large picture to LCD
    lcd.display(img_mnist,oft=(0,80))
    # Show small picture to LCD
    lcd.display(img_mnist1,oft=(0,50))
    # Draw results to LCD
    if pmax_mnist > 0.6:
        lcd.draw_string(8,8 ,"Detected number: %d " % (max_index_mnist),lcd.WHITE,lcd.BLACK)
        lcd.draw_string(8,24,"---> Confidence: %.1f%% " % (pmax_mnist*100),lcd.WHITE,lcd.BLACK)
    else:
        lcd.draw_string(8,8 ,"Detected number: NaN ",lcd.WHITE,lcd.BLACK)
        lcd.draw_string(8,24,"---> Confidence: %.1f%% " % (pmax_mnist*100),lcd.WHITE,lcd.BLACK)
    gc.collect()

kpu.deinit(task)
