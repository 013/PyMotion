import os
import time
import subprocess
from PIL import Image, ImageChops
import math
import numpy as np
from threading import Thread

class detect:
	def __init__(self):
		self.ips = ['192.168.0.61', '192.168.0.62']
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
		print cam_ip
		self.takeImage(cam_ip)
		img1 = Image.open('1_{0}.jpg'.format(cam_ip.split('.')[-1]))
		img2 = Image.open('2_{0}.jpg'.format(cam_ip.split('.')[-1]))

		img = ImageChops.difference(img1,img2)
		#img.save('{0}_diff.png'.format(cam_ip.split('.')[-1])) 
		print self.image_entropy(img)

def main():
	d = detect()
	
	threads = []
	
	for ip in d.ips:
		t = Thread(target=d.compare, args=(ip,))
		threads.append(t)
	
	[x.start() for x in threads]
	
	[x.join() for x in threads]

if __name__ == "__main__":
	main()

