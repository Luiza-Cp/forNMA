# -*- coding: utf-8 -*-
"""
Created on Tue May  4 14:09:06 2021

@author: Luiza
"""


from pystackreg import StackReg
from skimage import io
import tifffile
import os
import re
import gc
from pystackreg.util import to_uint16

#Add here the path to folders crerated in the previous step

folder_save = 'D:\\Triagem\\'
folder_save2 =  os.path.join(folder_save, "Red_Registered")
folder_save3 =  os.path.join(folder_save, "Green_registered")
#os.mkdir(folder_save2)
#os.mkdir(folder_save3)



def register(foldername1, foldername2):

    compound_name = os.path.basename(foldername1)
            
    filename1 = os.path.join(folder_save, 'red.tiff')
    filename2 = os.path.join(folder_save, 'green.tiff')
    file_list_r = os.listdir(foldername1)  
    file_list_g = os.listdir(foldername2)
    os.mkdir(os.path.join(folder_save2, compound_name))
    os.mkdir(os.path.join(folder_save3, compound_name)) 
    
    if 'red.tiff' in file_list_r: 
        file_list_r.remove('red.tiff')
    if 'green.tiff' in file_list_r: 
        file_list_g.remove('green.tiff')
                
    file_list2 = [s[1:-14] for s in file_list_r]
    fields_list = list(set(file_list2))
            
    for field in fields_list:
        files_to_stack_r1 = [i for i in file_list_r if re.search(field, i)]
        files_to_stack_r = [os.path.join(foldername1, i) for i in files_to_stack_r1]
        files_to_stack_g1 = [i for i in file_list_g if re.search(field, i)]
        files_to_stack_g = [os.path.join(foldername2, i) for i in files_to_stack_g1]
        
        os.chdir(foldername1)      
        with tifffile.TiffWriter(filename1) as stack:
            for filename in files_to_stack_r:
                stack.save(tifffile.imread(filename))
        os.chdir(foldername2)         
        with tifffile.TiffWriter(filename2) as stack:
            for filename in files_to_stack_g:
                stack.save(tifffile.imread(filename))
                
        img0 = io.imread(filename1, plugin='pil')
        img1 = io.imread(filename2, plugin='pil')
        print('ok')
        assert img0.shape == img1.shape
        
        out, out_previous = register_im(img0,img1)
                
           
        save_r = os.path.join(folder_save2, compound_name, field)
        save_g = os.path.join(folder_save3, compound_name, field)
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
            io.imsave(os.path.join(save_r, files_to_stack_r1[n]), stack_slice)
            n= n+1
        n=0
        for stack_slice in out:
                  io.imsave(os.path.join(save_g , files_to_stack_g1[n]), stack_slice)
                  n= n+1   
                   
        print(field, '---> Done')   
        gc.collect()
    
    print ('FEITO TIME')
  
    
def register_im(img0, img1):
    sr = StackReg(StackReg.RIGID_BODY)
    out_previous = sr.register_transform_stack(img0, reference='previous')
    tmats = sr.register_stack(img0, reference='previous')
    out = sr.transform_stack(img1)
    sr.transform_stack(img1, tmats=tmats)
    
    #out_previous = to_uint16(out_previous)
    #out = to_uint16(out)
    return out, out_previous
                    
    
#pastas = os.listdir('D:\\Triagem\\Green_registered')
pastas = [
    'DBS16_0.001_1000', 
    
    'DBS16_0.01_1000',
    
    'DBS16_0.1_1000',
   
    'DBS16_1_1000'

    
    
    ]
  
for a in pastas:  
    print('D:\\Triagem\\Red\\' + a)
    register('D:\\Triagem\\Red\\' + a, 'D:\\Triagem\\Green\\' + a)

#move

import shutil
red= 'D:\\Triagem\\Green_registered'
for pasta in pastas:
    subpastas = os.listdir(os.path.join(red,pasta))
    for subpasta in subpastas:
        print (subpasta)
        for file_name in os.listdir(os.path.join(red,pasta, subpasta)):
            #print (file_name)
            a = os.path.join(red, pasta, subpasta, file_name)
            b  =os.path.join(red, pasta)
            shutil.move(a, b)         
            
 # rename
'''          
red= 'D:\\Triagem\\Green_registered'
for pasta in pastas:
    subpastas = os.listdir(os.path.join(red,pasta))
    for subpasta in subpastas:
        for filename in os.listdir(os.path.join(red,pasta, subpasta)): 
            if 'GR' in filename:
                new_name = 'G' +filename[-19:]  
                velho = os.path.join(red,pasta,subpasta, filename)
                novo = os.path.join(red,pasta,subpasta, new_name)
                        
                os.rename(velho, novo)
'''            

''' Usar esse pra fazer registration de pastas especificas e tal
composto = 'DBS16_1_1000'
campos = [ '_B4_2']
for campo in campos:
 
    foldername1 = 'D:\\Triagem\\Red\\' + composto
    foldername2 = 'D:\\Triagem\\Green\\' + composto 
    filename1 = os.path.join(folder_save, 'red.tiff')
    filename2 = os.path.join(folder_save, 'green.tiff')
    
    file_list_r = os.listdir(foldername1)
    file_list_g = os.listdir(foldername2)
    #file_list2 = [s[1:-14] for s in file_list_r]
    file_list3 = [s for s in file_list_r if (campo in s)]
    fields_list = list(set(file_list3))
    
    file_listg = [s for s in file_list_g if (campo in s)]
    fields_listg = list(set(file_listg))
    
    
    
    files_to_stack_r = [os.path.join(foldername1, i) for i in fields_list]
    files_to_stack_g = [os.path.join(foldername2, i) for i in fields_listg]
    
    os.chdir(foldername1)      
    with tifffile.TiffWriter(filename1) as stack: 
        for filename in files_to_stack_r:
            stack.save(tifffile.imread(filename))
    os.chdir(foldername2)         
    with tifffile.TiffWriter(filename2) as stack:
         for filename in files_to_stack_g:
            stack.save(tifffile.imread(filename))
                        
    img0 = io.imread(filename1, plugin='pil')
    img1 = io.imread(filename2, plugin='pil')
    print('ok')
    assert img0.shape == img1.shape
                
    out, out_previous = register_im(img0,img1)
                  
     
                   
    save_r = 'D:\\Triagem\\Red_Registered\\' + composto + '\\' + campo
    save_g = 'D:\\Triagem\\Green_Registered\\' + composto + '\\' + campo
    if os.path.exists(save_r)  == False:
        os.mkdir(save_r)
    if os.path.exists(save_g) == False:
        os.mkdir(save_g)
    
                        
    n = 0
    for stack_slice in out_previous:
        io.imsave(os.path.join(save_r, file_list_r[n]), stack_slice)
        n= n+1
    n=0
    for stack_slice in out:
        io.imsave(os.path.join(save_g , 'G' +fields_list[n]), stack_slice)
        n= n+1   
    
    
 '''
    




         