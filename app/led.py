import sys

try:
	import RPi.GPIO as GPIO
except ImportError:
	print("Warning: could not import RPi.GPIO. Faking it!")
	from app.gpio_faker import GPIOFake
	GPIO = GPIOFake()


LED_PIN = 33

GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN, GPIO.OUT)

def control(enable):
	if enable:
		GPIO.output(LED_PIN, GPIO.HIGH)
	else:
		GPIO.output(LED_PIN, GPIO.LOW)

if __name__ == "__main__":
	if sys.argv[1] == "on":
		control(True)
	elif sys.argv[1] == "off":
		control(False)

	try:
		while True:
			pass
	finally:
		GPIO.cleanup()

