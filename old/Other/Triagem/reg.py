# -*- coding: utf-8 -*-
"""
Created on Tue May  4 00:06:41 2021

@author: Luiza
"""

from pystackreg import StackReg
from skimage import io
import tifffile
import glob  
import os
import re
import cv2 as cv
import gc
from tqdm import tqdm

#Add here the path to folders crerated in the previous step
path_red = 'D:\\Triagem\\Red'
path_green = 'D:\\Triagem\\Green'

folder_save = 'D:\\Triagem\\'


####Editar isso pra ele rodar uma pasta por vez pra
# eu poder rodar no meu pc de boa
# 
folder_save2 =  os.path.join(folder_save, "Red_Registered")
folder_save3 =  os.path.join(folder_save, "Green_registered")
os.mkdir(folder_save2)
os.mkdir(folder_save3)

with tqdm(total =100) as pbar:
    for pair in tqdm(zip(sorted(os.listdir(path_red)),sorted(os.listdir(path_green)))):
        print(pair)
        foldername1 = os.path.join(path_red, (pair[0]))
        foldername2 = os.path.join(path_green, (pair[1]))
        
        filename1 = os.path.join(foldername1, 'red.tiff')
        filename2 = os.path.join(foldername2, 'green.tiff')
        
        
        
        file_list_r = os.listdir(foldername1) 
        file_list_g = os.listdir(foldername2) 
        if 'red.tiff' in file_list_r: 
                file_list_r.remove('red.tiff')
        if 'green.tiff' in file_list_r: 
                file_list_g.remove('green.tiff')
            
        file_list2 = [s[1:-14] for s in file_list_r]
        fields_list = list(set(file_list2))
        
        for field in fields_list:
            files_to_stack_r = [i for i in file_list_r if re.search(field, i)]
            files_to_stack_r = [os.path.join(foldername1, i) for i in files_to_stack_r]
            files_to_stack_g = [i for i in file_list_g if re.search(field, i)]
            files_to_stack_g = [os.path.join(foldername2, i) for i in files_to_stack_g]
            
            with tifffile.TiffWriter(filename1) as stack:
                for filename in files_to_stack_r:
                    stack.save(tifffile.imread(filename))
            
            with tifffile.TiffWriter(filename2) as stack:
                for filename in files_to_stack_g:
                    stack.save(tifffile.imread(filename))
            
            img0 = io.imread(filename1, plugin='pil')
            img1 = io.imread(filename2, plugin='pil')
            print('ok')
            assert img0.shape == img1.shape
    
            sr = StackReg(StackReg.RIGID_BODY)
            out_previous = sr.register_transform_stack(img0, reference='previous')
            tmats = sr.register_stack(img0, reference='previous')
            out = sr.transform_stack(img1)
            sr.transform_stack(img1, tmats=tmats)
            
            
            
            save_r = os.path.join(folder_save2, pair[0])
            save_g = os.path.join(folder_save3, pair[0])
            if os.path.exists(save_r)  == False:
                os.mkdir(save_r)
            if os.path.exists(save_g) == False:
                os.mkdir(save_g)
            if 'red.tiff' in file_list_r: 
                file_list_r.remove('red.tiff')
            if 'green.tiff' in file_list_r: 
                file_list_g.remove('green.tiff')
            
            n = 0
            for stack_slice in out_previous:
                io.imsave(os.path.join(save_r, file_list_r[n]), stack_slice)
                n= n+1
            n=0
            for stack_slice in out:
               io.imsave(os.path.join(save_g , file_list_g[n]), stack_slice)
               n= n+1   
               
       
        gc.collect()
