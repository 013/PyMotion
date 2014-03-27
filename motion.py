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
		self.commands = []
		self.FNULL = open(os.devnull, 'w')
		self.kill = False # If true exit processes

	def takeImages(self, ip):
		cid = ip.split('.')[-1] # Get last octet and use as an id
		self.commands.append('ffmpeg -i rtsp://admin:linnit@{0}/Streaming/Channels/2 -t 120 -r 1 -f image2 image_{1}-%3d.jpg'.format(ip, cid))
		
		# Take stream of images
		processes = [subprocess.Popen(cmd, shell=True, stdout=self.FNULL, stderr=subprocess.STDOUT) for cmd in self.commands]
		#processes = [subprocess.Popen(cmd, shell=True) for cmd in self.commands]
		# Wait for the process to finish
		for p in processes: p.wait()

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
		
		for i in range(1,120,2):
			if self.kill == True: return 0
			time.sleep(2)
			imgno1, imgno2 = "%03d" % (i,), "%03d" % (i+1,)
			print imgno1, imgno2			

			img1 = Image.open('image_{0}-{1}.jpg'.format(cam_ip.split('.')[-1], imgno1) )
			img2 = Image.open('image_{0}-{1}.jpg'.format(cam_ip.split('.')[-1], imgno2) )
	
			img = ImageChops.difference(img1,img2)
			#img.save('{0}_diff.png'.format(cam_ip.split('.')[-1])) 
			image_ent = self.image_entropy(img)
			if image_ent < 1.5:
				colour = green
			else:
				colour = red
				img.save('{0}_{1}.png'.format(cam_ip.split('.')[-1], int(time.time()) ))
				print 'Motion detected - saving image to {0}_{1}.png'.format(cam_ip.split('.')[-1], int(time.time()) )
			print "IP: {0}\t Entropy: {1}{2}{3}".format(cam_ip, colour, image_ent, reset)
			# Remove images
			os.unlink('image_{0}-{1}.jpg'.format(cam_ip.split('.')[-1], imgno1))
			os.unlink('image_{0}-{1}.jpg'.format(cam_ip.split('.')[-1], imgno2))
		

def main():
	d = detect()
	det = True	
	while det == True:
		try:
			threads = []
			for ip in d.ips:
				t = Thread(target=d.takeImages, args=(ip,))
				threads.append(t)
				t = Thread(target=d.compare, args=(ip,))
				threads.append(t)
			
			[x.start() for x in threads]
			
			[x.join() for x in threads]
			#det = False
		except KeyboardInterrupt:
			print "Keyboard Interrupt received"
			det = False
			d.kill = True
			for x in threads:
				x.kill_received = True 
			sys.exit()

if __name__ == "__main__":
	main()

