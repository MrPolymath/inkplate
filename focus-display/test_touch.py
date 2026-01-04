# Touch test script
import time
from inkplate6FLICK import Inkplate

display = Inkplate(Inkplate.INKPLATE_1BIT)
display.begin()

print("=" * 40)
print("TOUCH TEST")
print("=" * 40)

print("\nInitializing touchscreen...")
display.tsInit(1)
print("Touchscreen initialized!")

print("\n>>> TAP THE SCREEN NOW! <<<")
print("Monitoring for 30 seconds...\n")

for i in range(300):
    try:
        data = display.tsGetData()
        if data:
            if len(data) >= 3 and data[0] > 0:
                print(f"TOUCH! Fingers: {data[0]}, X: {data[1]}, Y: {data[2]}")
    except Exception as e:
        if "NoneType" not in str(e):
            print(f"Error: {e}")
    time.sleep(0.1)

print("\nDone monitoring. Shutting down touch...")
display.tsShutdown()
print("Test complete!")
