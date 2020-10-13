# -*- coding: utf-8 -*-
"""
Created on Tue Oct  6 09:31:46 2020

@author: Luiza 

vai ser o oficial 53bp1 py com aro arrumado

O RING SIZE DEVE SER PEGO DE ACORDO COM O AUMENTO DA IMAGEM QUE É INFORMADO
PELO USUÁRIO LEMBRAR ISSO PLMDDS
"""

from skimage import io, img_as_float, exposure,color
from matplotlib import pyplot as plt
from matplotlib.patches import Ellipse
#import matplotlib.image as mpimg
from skimage.filters import  threshold_triangle, threshold_yen
from skimage.measure import profile_line
from skimage.segmentation import clear_border
import cv2 as cv
import numpy as np
import math 
import pandas as pd 
import seaborn as  sns
from skimage.feature import local_binary_pattern
import copy
from scipy import stats
import os

class cell:
    def __init__(self, n, cnt, bbox, ring_size, rf):
        self.n = n
        self.rf = rf
        self.cnt = cnt
        self.bbox = bbox
        self.ring_size = ring_size
        self.area = cv.contourArea(cnt)
        self.fellipse = cv.fitEllipse(cnt)   #fitting ellipse
        self.perimeter=  cv.arcLength(cnt,True)
        self.moments =  cv.moments(cnt)
        self.aspect = self.calc_aspect()
        self.extent = self.calc_extent()
        self.roundness = (self.perimeter **2)/ (4* math.pi * self.area)
        self.centroid_x = int(self.moments['m10']/self.moments['m00'])
        self.centroid_y = int(self.moments['m01']/self.moments['m00'])
        self.radius_ratio = self.calc_radius_ratio()
        self.NII = self.calc_NII()
        self.nuc, self.mask = self.calc_nuc_mask()
        self.mean_intensity = self.calc_mean_intensity()
        self.bbox2= self.bbox2()
        self.expand_nuc = self.expand_nuc()
        self.ring, self.mean_ring = self.find_ring()
        self.NC_ratio = self.mean_intensity/ self.mean_ring[0]
        self.CN_ratio = self.mean_ring[0]/self.mean_intensity
        self.lbp = self.calc_lbp()
        self.foci_cnt, self.mask_foci = self.calc_foci_cnt()
        self.foci = len(self.foci_cnt)
        self.foci_cnt_im = self.find_cnt_at_image()
        self.foci_list = self.calc_nuc_foci()
        self.tot_foci_area = self.calc_tot_foc_area()
 

    def calc_aspect (self): #raio maior / raio menor da elipse
        if self.fellipse[1][0] > self.fellipse[1][1]:
            asp = self.fellipse[1][0]/self.fellipse[1][1]
        else:
            asp = (self.fellipse[1][1])/(self.fellipse[1][0])
        return asp 
        
    def calc_extent(self): #Object area/ bounding rectangle
        bbox_area = self.bbox[2] * self.bbox[3]
        return self.area / bbox_area
    
    def calc_radius_ratio(self):
        radius = []
        cx =self.centroid_x
        cy = self.centroid_y
        for i in range(len(self.cnt)):
            a = cx- self.cnt[i,0,0]
            b = cy - self.cnt[i,0,1]
            hipot = math.sqrt(a**2 + b **2)
            radius.append(hipot)
        return max(radius) / min(radius)
        
    def calc_NII(self):
        nii = self.aspect-self.extent + self.radius_ratio + self.roundness
        return nii
    
    def calc_nuc_mask(self):
        x = self.bbox[0] 
        y = self.bbox[1] 
        w = self.bbox[2] 
        h = self.bbox[3] 
        nuc = img1_2[y:y+h, x:x+w]
        mask = binary_img[y:y+h, x:x+w]
        return (nuc, mask)
    
    def calc_mean_intensity(self): 
        nuc = self.nuc
        mask = self.mask
        mean_I= cv.mean(nuc,mask =mask)
        return mean_I[0]
    
    def bbox2(self):
        factor = ring_size*2
        x2 = self.bbox[0] - factor
        y2 = self.bbox[1] - factor
        w2 = self.bbox[2] + 2*factor
        h2 = self.bbox[3] + 2*factor
        if x2 < 0:
            x2 = 0
        if y2 < 0:
            y2=0
        if w2 > img1.shape[1]:
            w2 = img1.shape[1]
        if h2 > img1.shape[0]:
            h2 = img1.shape[0]
        return (x2,y2,w2,h2)
        
    def expand_nuc(self):
        '''returns the integer mask (np.array) of the expanded nuc'''
        x2 = self.bbox2[0] 
        y2 = self.bbox2[1] 
        w2 = self.bbox2[2] 
        h2 = self.bbox2[3] 
        kernel = np.ones((3,3), np.uint8)
        nuc2 = binary_img[y2:y2+h2, x2:x2+w2]
        #nuc2 = clear_border(nuc2)
        nuc_mask = nuc2
        nuc_expanded = cv.dilate (nuc2, kernel, iterations=round(14*self.rf))
        nuc_expanded_mask = nuc_expanded
        return nuc_mask, nuc_expanded_mask
        
    def find_ring(self):
        '''returns the ring mask (int) and de mean intensity of it'''
        a= cv.bitwise_not(self.expand_nuc[0])
        b= self.expand_nuc[1]
        ring = cv.bitwise_and(a,b)
        x2 = self.bbox2[0] 
        y2 = self.bbox2[1] 
        w2 = self.bbox2[2] 
        h2 = self.bbox2[3] 
        nuc = img1_2[y2:y2+h2, x2:x2+w2]
        mean = cv.mean(nuc, mask= ring)
        return ring, mean
        
    def calc_lbp(self):
        '''no lbp esse radius depende do n pixels e magnificação
        devolve uma msk com lbp'''
        nuc = self.nuc
        mask = self.mask
        radius = 5
        n_points = 8 * radius
        METHOD = 'uniform'
        lbp = local_binary_pattern(nuc, n_points, radius, METHOD)
        lbp_masked =  np.ma.masked_where(mask==0, lbp)
        return lbp_masked
        
    def calc_foci_cnt(self):
        '''devolve a lista de cnt e a imagem dos dots para usar no objeto foci'''
        find_dots = self.lbp < 18
        dots_binary = find_dots.astype('uint8')
        kernel = np.ones((3,3), np.uint8)
        dots = cv.morphologyEx(dots_binary, cv.MORPH_OPEN, kernel, iterations=1)
        dots = cv.morphologyEx(dots, cv.MORPH_CLOSE, kernel, iterations=1)
        dots =  cv.dilate (dots, kernel, iterations=1)
        for i in range(6):
            dots = cv.GaussianBlur(dots,(3,3),2)
        
        mask = self.mask
        dots = clear_border(dots)
        dots = dots==0
        dots = np.ma.masked_where(mask==0, dots)
        dots = dots.astype('uint8')
        
        contours_foci, hierarchy_foci = cv.findContours(dots, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        contours_foci  = [a for a in contours_foci if len(a)>4]
        
        if len(contours_foci) >0:
            areas = []
            for cnt in contours_foci:
                areas.append(cv.contourArea(cnt))
            min_a = max(areas)/5
            contours_foci = [b for a, b in zip(areas, contours_foci) if a > min_a]  
        return (contours_foci, dots)
    
    def find_cnt_at_image(self):
        cnts = copy.deepcopy(self.foci_cnt)
        value_x = self.bbox[0]
        value_y = self.bbox[1]
        for cnt in cnts:
            for pix in cnt:
                pix[0][0] = pix[0][0] + value_x
                pix[0][1] = pix[0][1] + value_y
        return cnts
     

    def calc_nuc_foci(self):
        mask = self.mask
        nuc = self.nuc
        nuc_masked = np.ma.masked_where(mask==254, nuc)
        foci_list = []
        if len(self.foci_cnt) == 0: 
              foci_list = []           
        else:
            for i in range(len(self.foci_cnt)):
                new_foci = foci( i, self.foci_cnt[i], nuc_masked, self.mask_foci)
                foci_list.append (new_foci)           
        return foci_list
    
       
    def calc_tot_foc_area(self):
        tot_area= 0
        if len(self.foci_list) > 0:
            for foci in self.foci_list:
                tot_area = tot_area + foci.area  
        return tot_area


class foci:
    def __init__(self, n, cnt, orig_nuc, mask_foci):
        self.n = n
        self.cnt = cnt
        self.orig_nuc = orig_nuc
        self.mask_foci = mask_foci
        self.area = cv.contourArea(self.cnt)
        self.bx, self.by, self.bw, self.bh = cv.boundingRect(self.cnt)
        self.mean_int = self.calc_intensity()

    def calc_intensity(self):
        mask = self.mask_foci[self.by:self.by+self.bh, 
                              self.bx:self.bx+self.bw]
        nuc = self.orig_nuc[self.by:self.by+self.bh, 
                            self.bx:self.bx+self.bw]
    
        mask = mask.astype('uint8')
        mean = cv.mean(nuc, mask= mask)
        return mean
        

    

       
        
'''------------------------------------------------------------'''       
        
def dot_count(cell_list):
    l = []
    for cell in cell_list:
        l.append(len(cell.foci_cnt))
    for n in range(11):
        z = len([x for x in l if x == n])
        print ( z)
    z = len([x for x in l if x > 10])
    print ("More than 10 dots: ", z)
     
    

def all_cnt(cell_list):
    '''cria uma lista com todos os contornos de todos os pontos'''
    all_cnt =  []   
    for cell in cell_list:
        for cnt in cell.foci_cnt_im:
            all_cnt.append(cnt)
    return all_cnt

def draw_all_cnt(cnt_foci, cnt_nuc):
    '''recebe a lista de todos os contornos + lista de contornos 
    do nucleo (contous)'''
    cv.drawContours(eq_img1,cnt_foci, -1,  (255,0,0),2)
    cv.drawContours(eq_img1,cnt_nuc,-1,  (255,0,0),2)
    cv.namedWindow('finalImg', cv.WINDOW_NORMAL)
    cv.imshow("finalImg",eq_img1)
    cv.waitKey(0)

def find_df_NMA(cell_list):
    dfNMA = pd.DataFrame(columns = ['Nucleus', 'Area',
                                    "NII" , "Foci Count", "c/n ratio", 'n/c ratio'])
    for cell in cell_list:
        a= cell.n
        b= cell.area
        c= cell.NII
        d= cell.foci
        e= cell.CN_ratio
        f = cell.NC_ratio
        row = [a,b,c,d,e,f]
        dfNMA.loc[len(dfNMA)] = row
    return dfNMA
        
def plot_NMA(df, ellipse):
    fig,ax = plt.subplots(1)
    sns.scatterplot(data=df, x="NII", y="Area", hue="n/c ratio", 
                    size= 'Foci Count', palette='rocket_r', ax=ax) 
    el = Ellipse(ellipse[0], ellipse[1], ellipse[2],color='red', fill=False)
    ax.add_patch(el)
    plt.show()

def thresh_NMA(df):
    means_NII = []
    means_area= []
    for i in range(1000):
        df2 = df.sample(replace=True).mean()
        means_NII.append(df2['NII'].mean())
        means_area.append(df2['Area'].mean())
    x_ax = stats.describe(means_NII)
    y_ax = stats.describe(means_area)
    sd_x = math.sqrt(x_ax[3])
    sd_y = math.sqrt(y_ax[3])
    ellipse = [(x_ax[2], y_ax[2]), 4*sd_x, 4*sd_y] 
    return ellipse

def find_df_dot(name, cells_list):
    df_foci = pd.DataFrame(columns = ['Image','Nucleus', 'Foci', "Foci area" , 
                                      "Foci Mean Intensity"])
    for cell in cells_list:
        for foci in cell.foci_list:
            info = [name, cell.n, foci.n, foci.area, foci.mean_int[0]]
            df_foci.loc[len(df_foci)] = info
    return df_foci

def find_df_nuc(name, cells_list):
     df_cell = pd.DataFrame(columns = ['Image','Nucleus', ' Area', 'Foci count', 
                                       "Foci area/Nuc area", 
                                       'NII', 'C/N ratio',"N/C ratio", 
                                       'Coordinate X', 'Coordinate Y'])
     for cell in cells_list:
         area_FN = cell.tot_foci_area/ cell.area
         row= [ name, cell.n, cell.area, cell.foci, area_FN, cell.NII,
               cell.CN_ratio, cell.NC_ratio, cell.centroid_x, cell.centroid_y]
         df_cell.loc[len(df_cell)] = row
     return df_cell


def watershed(imag, binary_im):
    binary2 = binary_im.astype('uint8') 
    imag = imag.astype('uint8') 
    kernel = np.ones((3,3), np.uint8)
    sure_bg = cv.dilate(binary2, kernel, iterations=round(14*rf))
    dist_transform = cv.distanceTransform(binary2,cv.DIST_L2,3)
    ret2, sure_fg = cv.threshold(dist_transform,0.3*dist_transform.max(),255, 0)
    sure_fg= np.uint8(sure_fg) 
    unknown= cv.subtract(sure_bg, sure_fg)
    ret3, markers = cv.connectedComponents(sure_fg)
    markers = markers+10
    markers[unknown==1] = 0
    img2 =cv.cvtColor(imag,cv.COLOR_GRAY2BGR)
    markers =cv.watershed(img2, markers)
    
    img2[markers == -1] = [0, 255, 255]
    img2 = color.label2rgb(markers, bg_label=0)
    markers1 = markers.astype(np.uint8)
    ret, imm2 = cv.threshold(markers1, 0, 255, cv.THRESH_BINARY|cv.THRESH_OTSU)
    for i in range(22):
         imm2 = cv.blur(imm2,(3,3))
    imm2 =  cv.erode (imm2, kernel, iterations=round(6*rf))
    contours, hierarchy = cv.findContours(imm2, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    #cv.drawContours(imag,contours,-1,  (255,0,0),1)
    #cv.namedWindow('finalImg', cv.WINDOW_NORMAL)
    #cv.imshow("finalImg",imag)
    #cv.waitKey(0)
    return (contours, hierarchy)



def adjust_cnt(contours_list,bin_img, img, rf):
    '''pega a lista de contours e aplica ws no que for necessário'''
    new_cnt_list = []
    for cnt in contours_list:
        x,y,w,h = cv.boundingRect(cnt)
        a = cv.contourArea(cnt)
        arbox = a/(h*w)
        if arbox > 0.57:
            new_cnt_list.append(cnt)
        else:
            x2 = x - round(30 *rf)
            y2 = y - round(30 *rf)
            w2 = w + round(60 *rf)
            h2 = h + round(60 *rf)
            if x2 < 0:
                x2 = 0
            if y2 < 0:
                y2=0
            if w2 > bin_img.shape[1]:
                w2 = bin_img.shape[1]
            if h2 > bin_img.shape[0]:
                h2 = bin_img.shape[0]
            
            roi_bin_img = bin_img[y2:y2+h2,x2:x2+w2]
            roi_bin_img = clear_border(roi_bin_img)
            roi_img = img[y2:y2+h2,x2:x2+w2]
           
            cnt2, hrc = watershed(roi_img, roi_bin_img)
            cnt_adjusted = [] 

            for i in range(len(cnt2)):
                if hrc[0,i,2] == -1:
                    cnt_adjusted.append(np.array(cnt2[i]))
                  
            if len(cnt_adjusted) < 2:
                new_cnt_list.append(cnt)
            else:
                
                for contour in cnt_adjusted:
                    for pix in contour:
                        pix[0][0] = pix[0][0] + x2
                        pix[0][1] = pix[0][1] + y2
                    new_cnt_list.append(contour)             
                    
                        
    #cv.drawContours(img,new_cnt_list,-1,  (255,0,0),2)
    #cv.namedWindow('finalImg', cv.WINDOW_NORMAL)
    #cv.imshow("finalImg",img)
    #cv.waitKey(0)

    return(new_cnt_list)
       

def filter_cell (contours_list):
    areas = []
    for cnt in contours_list:
        areas.append(cv.contourArea(cnt))
    area2 = copy.deepcopy(areas)
    i = round( len(areas)/2)
    area2.sort()
    median = area2[i]
    max_a = 15*median
    min_a = median/5
    contours_list2 = [b for a, b in zip(areas, contours_list) if a > min_a]  
    contours_list2 = [b for a, b in zip(areas, contours_list2) if a < max_a] 
    return (contours_list2)        

def adjust_binary_img (binary_img):
    binary_img = binary_img.astype(float)
    kernel = np.ones((3,3), np.uint8)
    erode =  cv.erode (binary_img, kernel, iterations=1)
    opening = cv.morphologyEx(erode, cv.MORPH_OPEN, kernel, iterations=round(2*rf))
    dilate =  cv.dilate (opening, kernel, iterations=round(6*rf))
    binary_img=  cv.erode (dilate, kernel, iterations=round(6*rf))
    binary_img = binary_img.astype(np.uint8)
    for i in range(12):
        binary_img = cv.blur(binary_img,(9,9))
    binary_img = binary_img <1 
    binary_img = clear_border(binary_img) 
    binary_img = binary_img.astype('uint8')
    return binary_img

def find_binary_img (eq_im):
    thresh = threshold_triangle(eq_im)
    binary_img = eq_im <= thresh 
    return binary_img


def find_binary_img_yen (eq_im):
    thresh = threshold_yen(eq_im)
    binary_img = eq_im <= thresh 
    return binary_img


'''--------------------------------------------------------------'''

im1 = "Sem pontos.tif"
im2 = "1 ou 2 pontos grandes.tif"
im3 = "muitos pontos definidos.tif"
im4 = 'muitos pontos pequenos.tif'
im6 ='a.tif'
im7 = 'b.tif'


folders = [('C:\\Users\\Luiza Cherobini\\Desktop\\tesste\\Sem pontos', True),
           ('C:\\Users\\Luiza Cherobini\\Desktop\\tesste\\1 ou 2 grandes', True),
           ('C:\\Users\\Luiza Cherobini\\Desktop\\tesste\\muitos pequenos', False),
           ('C:\\Users\\Luiza Cherobini\\Desktop\\tesste\\muitos definidos', False)]
###TRansformar todas as imagens em UINT 8?  


dict_NMA = {}

for folder in folders:
    a = folder[0]
    os.chdir(a)
   
    dict_cells ={}
    
    df_cells_list = []
    df_cells= pd.DataFrame(columns = ['Image','Nucleus', ' Area', 'Foci count', 
                                  "Foci area/Nuc area",  'NII', 'C/N ratio',
                                  "N/C ratio",'Coordinate X', 'Coordinate Y'])

    df_foci_list=[]
    df_foci = pd.DataFrame(columns = ['Image','Nucleus', 'Foci', "Foci area" , 
                                      "Foci Mean Intensity"])

    df_NMA_list=[]
    df_NMA = pd.DataFrame(columns = ['Nucleus', 'Area',"NII" , "Foci Count", 
                                 "c/n ratio", 'n/c ratio'])

    
    for folderName, subfolders, filenames in os.walk(a):
        for filename in filenames:
            im = filename

            try:
                img1= img_as_float(io.imread(im,  plugin='pil'))
                eq_img1 = exposure.equalize_adapthist(img1) 
                img1_2= cv.imread(im, 0)
                binary_img=  find_binary_img(eq_img1)
            except:
                img1 = cv.imread(im, 0)
                eq_img1 = exposure.equalize_adapthist(img1) 
                img1_2= cv.imread(im, 0)
                binary_img=  find_binary_img_yen(eq_img1)
  

            rf = img1.size/4194304
            '''RF == resolution factor'''


            binary_img = adjust_binary_img(binary_img)
            contours, hierarchy = cv.findContours(binary_img, cv.RETR_TREE, 
                                                  cv.CHAIN_APPROX_SIMPLE)
            #exclui o que for menor que 4 (quadrados perfeitos)
            contours = [a for a in contours if len(a)>4]

            contours = adjust_cnt(contours, binary_img, img1, rf)
            contours = filter_cell(contours) 

            bbox = [] # lista de todos o bbox da imagem
            for i in range (len(contours)):
                x,y,w,h = cv.boundingRect(contours[i]) #isso é o meu bbox
                bbox_i = (x,y,w,h) #x, y, width e height
                bbox.append(bbox_i)
    
            cells = []
            position = 1
            ring_size = round(14 * rf)
            '''esse ring size muda de acordo com a magnificação. é 14 para 40x
            vai mudar tbm de acordo com o n pixels da imagem, mas isso será convertido'''
            for i in range (len(contours)):
                new_cell = cell(position, contours[i], bbox[i], ring_size, rf)
                cells.append(new_cell)
                position = position + 1 
    
    
            dict_cells[filename] = cells


    for key, value in dict_cells.items():
        df1 = find_df_dot(key, value)
        df2 = find_df_nuc(key,value)
        df3 = find_df_NMA(value)
        
        df_foci_list.append(df1)
        df_cells_list.append(df2)
        df_NMA_list.append(df3)

    
    df_foci = df_foci.append(df_foci_list,ignore_index = True)
    df_cells = df_cells.append(df_cells_list, ignore_index = True)
    df_NMA = df_NMA.append(df_NMA_list, ignore_index = True)

    dict_NMA[folder] = df_NMA


df_NMA_ellipse= pd.DataFrame(columns = ['Nucleus', 'Area',"NII" , "Foci Count", 
                                     "c/n ratio", 'n/c ratio'])
for key,value in dict_NMA.items():
    if key[1]==True:
        df_NMA_ellipse= df_NMA_ellipse.append(value,ignore_index = True)



ellipse = thresh_NMA(df_NMA_ellipse)
plot_NMA(df_NMA_ellipse, ellipse)
for key,value in dict_NMA.items():
    if key[1]==False:  
        plt.figure()
        plot_NMA(value, ellipse)