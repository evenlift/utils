
# coding: utf-8

import os
import sys
import cv2 as cv
import shutil
import datetime
import imagehash
from PIL import Image
import platform
import random
import argparse
#Custom libraries
import PyGYM
import normalization
import split

validExtensions = ['.jpg','.jpeg','.png','.JPG']

def RepresentsInt(s):
	try: 
		int(s)
		return True
	except ValueError:
		return False

def isImage(file_name):
	filename, file_ext = os.path.splitext(file_name)
	return file_ext in validExtensions


class Renamer:
	
	def __init__(self, validExtensions=validExtensions):
		self.validExtensions = validExtensions
	
	def get_name(self, extension):
		if platform.system() == "Windows":
			splitChar = "\\"
		elif platform.system() == "Linux":
			splitChar = "/"
		else:
			print("Sorry man.  No current support for this function on the {} platform".format(platform.system()))
			sys.exit()

		return os.getcwd().split(splitChar)[-1].replace(" ","") + str(random.randint(1,100000000)) + extension

	def renameImage(self, imgName):
		filename, file_ext = os.path.splitext(imgName)
		if file_ext not in validExtensions:
			print("Warning: Found non-image file. " + imgName)
		else:
			while True:
				try:
					os.rename(imgName, self.get_name(file_ext))
					break
				except FileExistsError as e:
					continue
		return 
			
	def recursiveRename(self,directoryName):
		os.chdir(directoryName)

		for x in os.listdir():
			if os.path.isdir(x):
				self.recursiveRename(x)
			else:
				self.renameImage(x)
		os.chdir("..")




class Preprocessor:
	
	def __init__(self, resolution=256, aspect_method="scale", valid_extensions=[".jpg",".png"]):
		self.resolution = resolution
		self.aspect_method = aspect_method
		self.valid_extensions = valid_extensions
		self.attempt_count = 0
		self.success_count = 0
		self.delete_count = 0
	
	def preprocess(self, srcName):
		#First we copy the directory into a new one of the same name.
		
		newDirectory = shutil.copytree(srcName, self.new_name(srcName))
		
		#Then we launch the recursive preprocessing 
		self.recursive_preprocess(newDirectory)
		
		print("Preprocessing complete.  {} attempted conversions. {} succesful conversions.".format(self.attempt_count, self.success_count))
		
	def new_name(self, srcName):
		return "Preprocessed {} {} {} {}".format(srcName, self.resolution, self.aspect_method, str(datetime.datetime.now())[:16].replace(":","-"))
	
	def recursive_preprocess(self,directoryName):
		os.chdir(directoryName)
		for x in os.listdir():
			if os.path.isdir(x):
				self.recursive_preprocess(x)
			else:
				self.process_image(x)
		os.chdir("..")   
		
	def process_image(self, img_name):
		filename, file_ext = os.path.splitext(img_name)
		if file_ext not in self.valid_extensions:
			print("Warning: Found non-standard file. Deleting.   " + img_name)
			os.remove(img_name)
			self.delete_count += 1
			return
		else:            
			self.attempt_count += 1
			
			try:
				if self.aspect_method == "scale":
					self.process_using_stretching(img_name)
					self.success_count += 1
				elif self.aspect_method == "crop:center":
					self.process_using_cropping(img_name)
					self.success_count += 1
				elif ("top" in self.aspect_method or "bottom" in self.aspect_method) and ("left" in self.aspect_method or "right" in self.aspect_method) and "crop" in self.aspect_method:
					self.process_using_edge_cropping(img_name)
					self.success_count += 1
				else:
					print("Aspect method '{}'  is not recognized.".format(self.aspect_method))
					sys.exit()
			except Exception as e:
			   print("Failure processing image: {}".format(img_name))
			   print(e)
	
	def process_using_edge_cropping(self, img_name):
		img = cv.imread(img_name,1)

		if img.shape[0] > img.shape[1]:

			if "top" in self.aspect_method:
				img = img[:img.shape[1],:]
			else:
				img = img[img.shape[0] - img.shape[1]:,:]
		else:
			#Wider than it is tall
			if "left" in self.aspect_method:
				img = img[:,:img.shape[0]]
			else:
				img = img[:,img.shape[1] - img.shape[0]:]

		if img.shape[1] < self.resolution:
			interpolation_method = cv.INTER_CUBIC
		else:
			interpolation_method = cv.INTER_AREA
			img = cv.resize(img, (self.resolution, self.resolution), interpolation=interpolation_method)
			
		filename, file_ext = os.path.splitext(img_name)
		
		if not cv.imwrite("{}f.jpg".format(filename), img):
			raise "{} not able to be written.".format(img_name)
		
		os.remove(img_name)

	def process_using_cropping(self, img_name):
		img = cv.imread(img_name, 1)
			
		if img.shape[0] > img.shape[1]:
			offset = int((img.shape[0] - img.shape[1])/2)
			img = img[offset:offset + img.shape[1],:]
		else:
			offset = int((img.shape[1] - img.shape[0])/2)
			img = img[:,offset:offset + img.shape[0]]
		
		if img.shape[1] < self.resolution:
			interpolation_method = cv.INTER_CUBIC
		else:
			interpolation_method = cv.INTER_AREA
			img = cv.resize(img, (self.resolution, self.resolution), interpolation=interpolation_method)
			
		filename, file_ext = os.path.splitext(img_name)
		
		if not cv.imwrite("{}f.jpg".format(filename), img):
			raise "{} not able to be written.".format(img_name)
		
		os.remove(img_name)
		
		
	def process_using_stretching(self, img_name):
		img = cv.imread(img_name,1)
		if img.shape[1] < self.resolution:
			interpolation_method = cv.INTER_CUBIC
		else:
			interpolation_method = cv.INTER_AREA
		
		img = cv.resize(img, (self.resolution, self.resolution), interpolation=interpolation_method)
			
		filename, file_ext = os.path.splitext(img_name)
		
		if not cv.imwrite("{}f.jpg".format(filename), img):
			raise "{} not able to be written.".format(img_name)
		
		os.remove(img_name)


class Counter:
	def __init__(self):
		self.list = []

	def count(self, directory_name):
		self.recursive_counter(directory_name)
		for x in self.list[::-1]:
			print(x)

	def recursive_counter(self, directory_name, tab_level=0):
		os.chdir(directory_name)
		counter = 0
		for x in os.listdir():
			if os.path.isdir(x):
				counter += self.recursive_counter(x, tab_level+1)
			else:
				counter += 1
		os.chdir("..")

		self.list.append("{}No. of objects in {}: {}".format("\t" * tab_level, directory_name, counter  ))
		return counter     

class Deduplicator:

	def __init__(self, hashmethod="all", delete=False):

		if hashmethod == 'average':
			self.hashfuncs = [imagehash.average_hash]
		elif hashmethod == 'perceptual':
			self.hashfuncs = [imagehash.phash]
		elif hashmethod == 'difference':
			self.hashfuncs = [imagehash.dhash]
		elif hashmethod == 'haar':
			self.hashfuncs = [imagehash.whash]
		elif hashmethod == 'wavelet':
			self.hashfuncs = [lambda img: imagehash.whash(img, mode='db4')]
		elif hashmethod == 'all':
			self.hashfuncs = [imagehash.average_hash, imagehash.phash, imagehash.dhash, imagehash.whash, lambda img: imagehash.whash(img, mode='db4')]
		else:
			raise 

		self.hashDict = {}
		self.duplicateDict = {}

	def dedup(self, directory_name, delete=False):
		for m in self.hashfuncs:
			self.recursive_dedup(m, directory_name)

		if len(self.duplicateDict) == 0:
			print("No duplicates.  Good job.")
		else:
			if not delete:	
				for x in self.duplicateDict:
					print(x, self.duplicateDict[x])
				print("We have {} duplicates".format(len(self.duplicateDict)))
			else:
				for x in self.duplicateDict:
					os.remove(x)
				print("We had {} duplicates but they were deleted".format(len(self.duplicateDict)))

	def recursive_dedup(self, hashfunc, directory_name):
		os.chdir(directory_name)
		for x in os.listdir():
			if os.path.isdir(x):
				self.recursive_dedup(hashfunc, x)
			else:
				if isImage(x):
					try:
						with Image.open(x) as tmp_img:
							hash = hashfunc(tmp_img)
					except OSError:
						print("Can't open image {}.  Maybe it's corrupt.".format(x))


					# print(x + "  " + str(hash))
					if hash in self.hashDict:
						self.duplicateDict[os.getcwd() + "\\"+ x] = 	self.hashDict[hash]		
					else:
						self.hashDict[hash] = os.getcwd()+x
					
		os.chdir("..")

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", 
		help="Renames data files according to standard format.  Ex. 'madmog.py -r datafile' in order to rename images in the folder (and subfolders) called 'datafile.'", 
		action="store")

	parser.add_argument("-c", 
		help="Counts how many images there are in each sub-directory.  Amount it cumulative with sub-directories.  Ex. 'madmog.py -c 'directory_name'",
		action="store")

	parser.add_argument("-p", 
		help="Preprocesses images in order to standardize size.  Expects source directory name, target resolution and scaling method args.  Ex. 'madmog.py -p raw_data -size 256 -scale_method crop' or 'mogmas.py -p raw_data -size 128 -scale_method scale'.  Accepts edge cropping methods such as crop-top-left or crop-bottom-left.",
		action="store")
	parser.add_argument("-size", help="Specifies target size of images.  Meant to be used with -p command.", action="store")
	parser.add_argument("-scale_method", help="Specifies method for creating square images. Meant to be used with -p command.", action="store")

	parser.add_argument("-d",
		help="Identifies duplicate images across entire directory according to a given hash method.  Ex. madmog.py -d 'directory_name' -detect_method average'. Supports 'average' 'difference' 'perceptual'  'haar' 'wavelet' and 'all' as default.  In order to directly delete duplicate images, include -delete arguement.", 
		action="store")
	parser.add_argument("-detect_method", help="Specifies algorithm to detect duplicate images.  Meant to be used with -d command.", action="store")
	parser.add_argument("-delete", help="Directly deletes all detected duplicate images. Meant to be used with -d command.", action="store_true")

	parser.add_argument("-v", help="Parses a video list sheet, downloading videos and creating images every x seconds.  Ex. madmog.py -v video_list.csv -seconds_between_frames 0.2 ", action="store")
	parser.add_argument("-seconds_between_frames", help="Specifies number of seconds between frames.  Should be float (e.g., 0.1).  Meant to be used with -v command.", action="store")
	parser.add_argument("-include_top_and_bottom", help="Specifies whether we should include 'top' and 'bottom' images.  Meant to be used with -v command.", action="store_true")

	parser.add_argument("-n", help="Calculates mean and std for RGB channels across all images in folder.  Robust to huge image sets, though slow.  Ex. madmog.py -n image_folder", action="store")
	parser.add_argument("-weigh_images_equally", help="Specifies that images should all be weighed similarly, with a simulated size equal to the average of the set.  Meant to be used with -n command. Ex. madmog.py -n -weigh_images_equally.", action="store_true")
	
	parser.add_argument("-s", help="Split image directory into test and training.  Only works with directory a single level deep and only consisting of images. Ex. madmog.py -s directory -test_percentage 0.2", action="store")
	parser.add_argument("-test_share", help="Specifies the %% of images going to test split.  Meant to be used with -s command.", action="store")

	args = parser.parse_args()

	if args.r != None:
		r = Renamer()
		r.recursiveRename(args.r)

	elif args.p != None:
		if args.size == None or args.scale_method == None:
			print("Missing size or scale method.")
			sys.exit()
		p = Preprocessor(int(args.size), args.scale_method)
		p.preprocess(args.p)

	elif args.c != None:
		c = Counter()
		c.count(args.c)

	elif args.d != None:
		if args.detect_method == None:
			d = Deduplicator()
		else:
			d = Deduplicator(args.detect_method)

		if args.delete:
			d.dedup(args.d, delete=True)
		else:
			d.dedup(args.d)

	elif args.v != None:
		cg = PyGYM.clipGetter(request_sheet=args.v, SECONDS_BETWEEN_STILLS=float(args.seconds_between_frames), include_top_and_bottom=args.include_top_and_bottom)
		cg.parseRequestSheet()
		cg.fillRequests()

	elif args.n != None:
		i = normalization.NormalizeStatsProfiler()
		i.calculate(args.n, weighImagesEqually=args.weigh_images_equally)
		print(i)

	elif args.s != None:
		s = split.Splitter(args.s)
		s. split(test_share=args.test_share)

	else:
		sys.exit() 