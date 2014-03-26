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
		self.commands_1 = []
		self.commands_2 = []
		self.FNULL = open(os.devnull, 'w')

	def takeImages(self, ip):
		cid = ip.split('.')[-1] # Get last octet and use as an id
		#self.commands_1.append('avconv -i rtsp://admin:linnit@{0}/Streaming/Channels/2 -f image2 -vframes 1 1_{1}.jpg'.format(ip, cid))
		self.commands.append('ffmpeg -i rtsp://admin:linnit@{0}/Streaming/Channels/2 -ss 00:00:01.500 -t 10 -r 1 -f image2 image_{1}-%2d.jpg'.format(ip, cid))
		#self.commands_2.append('avconv -i rtsp://admin:linnit@{0}/Streaming/Channels/2 -f image2 -vframes 1 2_{1}.jpg'.format(ip, cid))
		
		# Take 10 images
		#processes = [subprocess.Popen(cmd, shell=True, stdout=self.FNULL, stderr=subprocess.STDOUT) for cmd in self.commands]
		processes = [subprocess.Popen(cmd, shell=True) for cmd in self.commands]
		# Take first image
		#processes_1 = [subprocess.Popen(cmd, shell=True, stdout=self.FNULL, stderr=subprocess.STDOUT) for cmd in self.commands_1]
		# Sleep 1 seconds
		#time.sleep(1)
		# Take the second image
		#processes_2 = [subprocess.Popen(cmd, shell=True, stdout=self.FNULL, stderr=subprocess.STDOUT) for cmd in self.commands_2]
		
		# Wait for the process to finish
		for p in processes: p.wait()
		#for p in processes_1: p.wait()
		#for p in processes_2: p.wait()

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
		self.takeImages(cam_ip)
		
		for i in range(1,10,2):
			if i < 9:
				imgno1 = '0'+str(i)
				imgno2 = '0'+str(i+1)
			elif i == 9:
				imgno1 = '0'+str(i)
				imgno2 = '10'
			
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
			#os.unlink('1_{0}.jpg'.format(cam_ip.split('.')[-1]))
			#os.unlink('2_{0}.jpg'.format(cam_ip.split('.')[-1]))
		

def main():
	d = detect()
	det = True	
	while det == True:
		try:
			threads = []
			for ip in d.ips:
				t = Thread(target=d.compare, args=(ip,))
				threads.append(t)
			
			[x.start() for x in threads]
			
			[x.join() for x in threads]
			#det = False
		except KeyboardInterrupt:
			print "Keyboard Interrupt received"
			for x in threads:
				x.kill_received = True 
			sys.exit()

if __name__ == "__main__":
	main()

