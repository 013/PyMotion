#!/usr/bin/python
import os, sys
import time
import subprocess
from PIL import Image, ImageChops
import math
import numpy as np
from threading import Thread

class detect:
	def __init__(self):
		self.ips = ['192.168.0.61']
		self.commands_1 = []
		self.commands_2 = []
		self.FNULL = open(os.devnull, 'w')

	def takeImage(self, ip):
		cid = ip.split('.')[-1] # Get last octet and use as an id
		self.commands_1.append('avconv -i rtsp://admin:linnit@{0}/Streaming/Channels/2 -f image2 -vframes 1 1_{1}.jpg'.format(ip, cid))
		self.commands_2.append('avconv -i rtsp://admin:linnit@{0}/Streaming/Channels/2 -f image2 -vframes 1 2_{1}.jpg'.format(ip, cid))
		
		# Take first image
		processes_1 = [subprocess.Popen(cmd, shell=True, stdout=self.FNULL, stderr=subprocess.STDOUT) for cmd in self.commands_1]
		
		# Sleep 1 seconds
		time.sleep(1)
		
		# Take the second image
		processes_2 = [subprocess.Popen(cmd, shell=True, stdout=self.FNULL, stderr=subprocess.STDOUT) for cmd in self.commands_2]
		
		# Wait for the process to finish
		for p in processes_1: p.wait()
		for p in processes_2: p.wait()

	def image_entropy(self, img):
		w,h = img.size
		a = np.array(img.convert('RGB')).reshape((w*h,3))
		h,e = np.histogramdd(a, bins=(16,)*3, range=((0,256),)*3)
		prob = h/np.sum(h) # normalize
		prob = prob[prob>0] # remove zeros
		return -np.sum(prob*np.log2(prob))

	def compare(self, cam_ip):
		red = '\033[91m'
		green = '\033[92m'
		reset = '\033[0m'
		self.takeImage(cam_ip)
		img1 = Image.open('1_{0}.jpg'.format(cam_ip.split('.')[-1]))
		img2 = Image.open('2_{0}.jpg'.format(cam_ip.split('.')[-1]))

		img = ImageChops.difference(img1,img2)
		#img.save('{0}_diff.png'.format(cam_ip.split('.')[-1])) 
		image_ent = self.image_entropy(img)
		if image_ent < 1.5:
			colour = green
		else:
			colour = red
		print "IP: {0}\t Entropy: {1}{2}{3}".format(cam_ip, colour, image_ent, reset)
		# Remove images
		os.unlink('1_{0}.jpg'.format(cam_ip.split('.')[-1]))
		os.unlink('2_{0}.jpg'.format(cam_ip.split('.')[-1]))
		

def main():
	d = detect()
	
	while True:
		try:
			threads = []
			for ip in d.ips:
				t = Thread(target=d.compare, args=(ip,))
				threads.append(t)
			
			[x.start() for x in threads]
			
			[x.join() for x in threads]
		except KeyboardInterrupt:
			print "Keyboard Interrupt received"
			for x in threads:
				x.kill_received = True 
			sys.exit()

if __name__ == "__main__":
	main()

