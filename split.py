import random
import math
import shutil
import os

class Splitter:
	
	def __init__(self, directory):
		self.directory = directory
		self.test_share = 0.2
		self.directory_dict = {}

	def split(self, test_share):
		os.chdir(self.directory)

		for x in os.listdir():
			if os.path.isdir(x):
				self.profile_image_directory(x)
			
		os.chdir("..")

		# print(self.directory_dict)
		# print(self.directory_dict['bench press'])
		# print(len(self.directory_dict['bench press']))
		self.reduce_dict_into_train()
		train_directory = shutil.copytree(self.directory, self.directory + " train")
		test_directory = shutil.copytree(self.directory, self.directory + " test")

		self.delete_images(train_directory, train=True)
		self.delete_images(test_directory, train=False)


	def profile_image_directory(self, x):
		os.chdir(x)
		tmp = []

		for i in os.listdir():
			tmp.append(i)

		self.directory_dict[x] = tmp
		os.chdir("..")

	def reduce_dict_into_train(self):
		for d in self.directory_dict:
			ei = self.exclusion_index(self.directory_dict[d])
			tmp = self.directory_dict[d]

			for i in ei:
				tmp.remove(i)

			self.directory_dict[d] = tmp

	def exclusion_index(self, list):
		desired_size = int(len(list) * (1.0 - self.test_share))
		indices = []

		while True :
			tmp = random.randint(0,len(list)-1)
			if tmp not in indices:
				indices.append(tmp)

			if len(indices) == desired_size:
				break

		ret = []

		for i in indices:
			ret.append(list[i])
			
		return ret

	def delete_images(self, directory_name, train):
		os.chdir(directory_name)

		for d in self.directory_dict:
			os.chdir(d)

			for f in os.listdir():
				
				if train:
					if f in self.directory_dict[d]:
						os.remove(f)
				else:
					if f not in self.directory_dict[d]:
						os.remove(f)

			os.chdir("..")


		os.chdir("..")