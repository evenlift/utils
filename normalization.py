
import os
import numpy as np
from PIL import Image

import math


class NormalizeStatsProfiler:
    
    def __init__(self):
        self._c1mean_data = []
        self._c2mean_data = []
        self._c3mean_data = []
        self._c1var_data = []
        self._c2var_data = []
        self._c3var_data = []
        self._sample_size_data = []
        self.c1_mean = 0.0
        self.c2_mean = 0.0
        self.c3_mean = 0.0
        self.c1_var = 0.0
        self.c2_var = 0.0   
        self.c3_var = 0.0
        self.c1_std = 0.0
        self.c2_std = 0.0
        self.c3_std = 0.0

    def __str__(self):
        return "===Base 256===\nMeans: {} {} {}\nStandard Deviations: {} {} {}\n\n===Base 1===\nMeans: {} {} {}\nStandard Deviations: {} {} {}".format(self.c1_mean, self.c2_mean, self.c3_mean, 
            self.c1_std, self.c2_std, self.c3_std, self.c1_mean/255.0, self.c2_mean/255.0, self.c3_mean/255.0, 
            self.c1_std/255.0, self.c2_std/255.0, self.c3_std/255.0)

    def calculate(self, directoryName, weighImagesEqually=False):
        self.recursive_metrics_from_images(directoryName)
        
        if weighImagesEqually:
            averageSS = sum(self._sample_size_data) / len(self._sample_size_data)
            self._sample_size_data = [averageSS for x in self._sample_size_data]
            
        self.c1_mean, self.c1_var, _ = self.combineNDistributions(self._c1mean_data, self._c1var_data, self._sample_size_data)
        self.c2_mean, self.c2_var, _ = self.combineNDistributions(self._c2mean_data, self._c2var_data, self._sample_size_data)
        self.c3_mean, self.c3_var, _ = self.combineNDistributions(self._c3mean_data, self._c3var_data, self._sample_size_data)
        self.c1_std = math.sqrt(self.c1_var)
        self.c2_std = math.sqrt(self.c2_var)
        self.c3_std = math.sqrt(self.c3_var)
    
    def recursive_metrics_from_images(self,directoryName):
        os.chdir(directoryName)
        for x in os.listdir():
            if os.path.isdir(x):
                self.recursive_metrics_from_images(x)
            else:
                self.image_metrics(x)
        os.chdir("..") 

    def image_metrics(self, imageName):
        with Image.open(imageName) as i:
            x = np.array(i)
            if len(x.shape) == 2:
                i = i.convert("RGB")
                x = np.array(i)
        
        self._c1mean_data.append(x[:,:,0].mean())
        self._c2mean_data.append(x[:,:,1].mean())
        self._c3mean_data.append(x[:,:,2].mean())

        self._c1var_data.append(x[:,:,0].var(ddof=1))
        self._c2var_data.append(x[:,:,1].var(ddof=1))
        self._c3var_data.append(x[:,:,2].var(ddof=1))
        
        self._sample_size_data.append(x.shape[0] * x.shape[1])
        
    def combineNDistributions(self, means, variances, sample_sizes):
        currentMean = means[0]
        currentVar = variances[0]
        currentSS = sample_sizes[0]

        for i in range(1,len(means) - 1):
            currentMean, currentVar, currentSS = self.combineTwoDistributions(currentMean, currentVar, currentSS, means[i], variances[i], sample_sizes[i])

        currentMean, currentVar, currentSS = self.combineTwoDistributions(currentMean, currentVar, currentSS, means[-1], variances[-1], sample_sizes[-1], population=True) 

        return currentMean, currentVar, currentSS
    
    """
        Headrick, T. C. (2010). Statistical Simulation: Power Method Polynomials and other Transformations. Boca Raton, FL: Chapman & Hall/CRC.

        See page 137, Equation 5.38.  Custom modifications to handle population vs. sample logic.

        http://www.talkstats.com/threads/an-average-of-standard-deviations.14523/
    """
    def combineTwoDistributions(self, d1_mean, d1_var, d1_sample_size, d2_mean, d2_var, d2_sample_size, population=False):
        divisor = (d1_sample_size + d2_sample_size - 1)*(d1_sample_size+d2_sample_size)

        if population:
            divisor = (d1_sample_size + d2_sample_size)*(d1_sample_size+d2_sample_size)

        numerator_p1 = (d1_sample_size ** 2) * d1_var   +   (d2_sample_size ** 2)*d2_var  
        numerator_p2 =   -  d2_sample_size*d1_var  -  d2_sample_size*d2_var  -  d1_sample_size*d1_var  -  d1_sample_size*d2_var  
        numerator_p3 = d1_sample_size*d2_sample_size*d1_var  +  d1_sample_size*d2_sample_size*d2_var  +   d1_sample_size*d2_sample_size*((d1_mean - d2_mean)**2) 
        new_var = (numerator_p1 + numerator_p2 + numerator_p3) / divisor

        new_mean = (d1_sample_size*d1_mean + d2_sample_size*d2_mean) / (d1_sample_size + d2_sample_size)

        return new_mean, new_var, d1_sample_size + d2_sample_size
        

# class getInit:
    
#     def __init__(self):
#         self._height_data = []
#         self._width_data = []
        
    
#     def calculate(self, directoryName):
#         self.recursive_mean_calc(directoryName)
        
#         meanHeight = sum(self._height_data) / len(self._height_data)
#         meanWidth = sum(self._width_data) / len(self._width_data)
        
#         varHeight = sum([(x-meanHeight) **2 for x in self._height_data]) / len(self._height_data)
#         varWidth = sum([(x-meanWidth) **2 for x in self._width_data]) / len(self._width_data)
        
#         print("===Height===\nMean: {}   Std: {}\n\n====Width===\nMean: {}   Std:{}".format(meanHeight, math.sqrt(varHeight), meanWidth,math.sqrt(varWidth)))
    
#     def recursive_mean_calc(self,directoryName):
#         os.chdir(directoryName)
#         for x in os.listdir():
#             if os.path.isdir(x):
#                 self.recursive_mean_calc(x)
#             else:
#                 self.image_metrics(x)
#         os.chdir("..") 

#     def image_metrics(self, imageName):
#         with Image.open(imageName) as i:
#             x = np.array(i)
        
#         self._height_data.append(x.shape[0])
#         self._width_data.append(x.shape[1])

        

