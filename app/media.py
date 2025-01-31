""" media.py

Usage:
	media.py <filename>

"""

import docopt
import subprocess
import threading
import logging
import os
import signal

import app.led as led
import app.dimmer as dimmer

video_thread_obj = None
audio_thread_obj = None

stop_media_flag = False

def get_logger():
	return logging.getLogger(__name__)

def setup_logging(handler):
	get_logger().setLevel(logging.INFO)
	get_logger().addHandler(handler)

def video_thread(args):
	global stop_media_flag

	with open("/home/pi/cave-escape-share/dim.txt", 'r') as f:
		dimmer_value = int(f.readline().strip())
		get_logger().info("Setting dimmer to {}%".format(dimmer_value))

	current_dimmer_value = dimmer.dimmer_get("192.168.0.57", "1")
	dimmer.dimmer_set("192.168.0.57", "1", dimmer_value)
	led.control(True)
	p = subprocess.Popen(args)
	get_logger().info("Process ID {}".format(p.pid))
	while p.poll() is None:
		if stop_media_flag:
			get_logger().info("Terminating video (thread {})".format(p.pid))
			subprocess.check_call(["sudo", "kill", "-9", str(p.pid)])
			get_logger().info("Terminating mplayer".format(p.pid))
			subprocess.check_call(["sudo", "killall", "mplayer"])
			p.wait()
			get_logger().info("Terminated")

	led.control(False)
	dimmer.dimmer_set("192.168.0.57", "1", current_dimmer_value)

	stop_media_flag = False

def audio_thread(args):
	subprocess.call(args)

def stop_media():
	global stop_media_flag
	stop_media_flag = True

def play_video(filename, player):

	global video_thread_obj
	global stop_media_flag

	if video_thread_obj is None or not video_thread_obj.isAlive():

		stop_media_flag = False

		get_logger().info("Firing video thread to play {}".format(filename))

		if player == "spitft":
			args = ["sudo", "SDL_VIDEODRIVER=fbcon", "SDL_FBDEV=/dev/fb1", "mplayer", "-vo", "sdl", "-framedrop", filename]
		elif player == "vlc":
			args = ["vlc", filename, "vlc://quit"]

		video_thread_obj = threading.Thread(target=video_thread, args=(args, ))
		video_thread_obj.start()
	else:
		get_logger().info("Video already playing, could not play {}".format(filename))

def play_audio(filename):

	global audio_thread_obj

	args = ["sudo", "mplayer", "-ao", "alsa:device=hw=1.0", filename]
	t = threading.Thread(target=audio_thread, args=(args, ))
	t.start()

if __name__ == "__main__":
	args = docopt.docopt(__doc__)
	play_video(args["<filename>"], "spitft")
