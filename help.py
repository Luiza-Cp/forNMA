# -*- coding: utf-8 -*-
"""
Created on Tue Nov 17 09:37:01 2020

@author: Luiza

This will be responsable for having all functons I need to analyze my data and may
be not includded on the main code, it is just a tool to hel luiza
"""

import numpy as np
import cv2 as cv
import os
from initializing_functions2 import generate_cell_list
import re 
import pandas as pd        
from matplotlib import pyplot as plt 
import scipy
from scipy import stats
from analyze_folder import generate_dfs
from cell_class import cell
from foci_class import foci
import math
import seaborn as sns   
from matplotlib.patches import Ellipse

folder = 'C:\\Users\\Luiza Cherobini\\Documents\\Doutorado\\53BP1\\teste\\muitos definidos'
image_to_analyze = 'muitos pontos definidos.tif'
path_to_save ='C:\\Users\\Luiza Cherobini\\Desktop\\a.tif'
pixel_size = 0.1038
#pixel_size = 0.3025
magnification = 60
wants_foci = True
wants_ktr = False
wants_NMA = False
second_folder = False

os.chdir(folder)



def run_generate_cell_list (image, magnification, wants_foci, pixel_size):
    ''' this will just run the generate_cell_list function for one single image'''
    cell_list =  generate_cell_list(image, magnification, wants_foci, pixel_size = pixel_size )
    return cell_list
'''
cells = run_generate_cell_list(image_to_analyze, magnification, wants_foci,pixel_size)


image = cv.imread(image_to_analyze)
for c in cells:
    cv.drawContours(image, c.cnt, -1, (255,255,255), 2)
    cv.drawContours(image, c.foci_cnt_im, -1, (255,255,255), 1)
cv.namedWindow('image', cv.WINDOW_NORMAL)
cv.imshow('image', image)
cv.waitKey(0)
cv.destroyAllWindows()
cv.imwrite(path_to_save, image)

'''


def save_individual_marked_nucleus (cell_list, path_to_save, image_name, save_nucs =True):
    '''this function will save alll nuclei individually with its contours and
    foci contours. This wil generate an csv with features too. 
    If you do not want to save the images, jus want the csv file, pass False to save arg'''
    
    im_n = re.sub(r".tif", "", image_name)
    filext =path_to_save + im_n + '.csv'

    cells =  cell_list 

    im = cv.imread(image_name)
    im2 = im.copy()
    im3 = im.copy()
    fs = cv.getFontScaleFromHeight(2,11,3)
    fs2 = cv.getFontScaleFromHeight(2,20,5)

    #aqui escreve as coisas nas 3  imagens só
    for c in cells:
        cv.drawContours(im, c.foci_cnt_im, -1, (255,255,0), 1)
        cv.drawContours(im, c.cnt, -1, (255,255,255), 2)
        cv.putText(im, str(c.n), (c.bbox_x, c.bbox_y), 2, fs2, (255,255,255), 1)
    
        for i in range(len(c.foci_cnt_im)):
            pos = c.foci_cnt_im[i][0][0]
            cv.putText(im, str(i), (pos[0], pos[1]), 2, fs, (0,255,255), 1)
            cv.putText(im2, str(i), (pos[0], pos[1]), 2, fs, (0,255,255), 1)


    col_list = [ 'nuc', 'dot', 'nuc_mean', 'nuc_mean_no_dot', 'area', 'perimeter', 'mean_int',
                    'mean_int_th', "cent_int", 'cent_int_th', 'bright', 'bright_th', 'mean_cnt',
                    'mean_cnt_th', 'ext', 'ext4', 'ext_th', 'extr4_th', 'kurtosis', 'kurtosis_th',
                    'laplacian_var', 'laplacian_var_th', 'sec_deriv', 'sec_deriv_th', 'inertia',
                    'bright_cnt_ratio']
    df_foci_int =  pd.DataFrame(columns =col_list)


    for c in cells:
        um = im[c.bbox_y:c.bbox_y + c.bbox_h,  c.bbox_x:c.bbox_x + c.bbox_w]
        dois = im2[c.bbox_y:c.bbox_y + c.bbox_h,  c.bbox_x:c.bbox_x + c.bbox_w]
        tres = im3[c.bbox_y:c.bbox_y + c.bbox_h,  c.bbox_x:c.bbox_x + c.bbox_w]
        d = cv.hconcat([um,dois,tres])
        d = cv.copyMakeBorder(d, 40,0,0,0,cv.BORDER_CONSTANT)
        cv.putText (d,str(c.n), (round(d.shape[1]/2), 33), 2, fs2, (50,0,255), 2)
        filen = (path_to_save + im_n +  '_nuc' + str(c.n) + '.tif')
        dfc = c.df_foci_ints()
        if save_nucs == True:
             cv.imwrite(filen, d)
   
        df_foci_int = pd.concat([df_foci_int, dfc])


    df_foci_int.to_csv(filext)

    cv.namedWindow('image', cv.WINDOW_NORMAL)
    cv.imshow('image', im)
    cv.waitKey(0)
    cv.destroyAllWindows()
    cv.imwrite(filen, im)
    
    return print('done')


def show_lbp_and_nuc (cell_list):
    
    for c in cell_list:
        plt.figure()
        f, axarr = plt.subplots(2,2)
        axarr[0,0].imshow(c.tophat, cmap = 'gray')
        axarr[0,1].imshow(c.lbp, cmap = 'gray')
        axarr[1,0].imshow(c.lbp < 18, cmap = 'gray')
        axarr[1,1].imshow(c.nuc, cmap = 'gray')
        plt.title(str(c.n))
    
    return print('done')

'''
#editar aqui quando eu for efetivamente rodar

#COISAS IMPORTANTES AQUI
#FIltro de convexidade
#Filtro tamanho e intensidade pontos
#ajustar as coisas em micrômetros ao fina
#garatir que as imagens sejam medidas em uint8


folder1 = 'D:\\Análises\\Controle vs tratamentos\\Minhas coisas\\Estático\\controle sem branco'
folder2 = 'D:\\Análises\\Controle vs tratamentos\\Minhas coisas\\Estático\\cisplatina sem branco'

folder_list = [folder1, folder2]


pixel_size = 0.1038
#pixel_size = 0.3025
magnification = 60
wants_foci = True
wants_ktr = False
wants_NMA = True
second_folder = False

'''

def folders_dict_of_all(folder_list):
    everything_dict = {}
    for fol in folder_list:
        files = os.listdir(fol)
        os.chdir(fol)
        df_foc, df_nuc, df_cat, cell_list = generate_dfs(files, wants_foci, wants_ktr, magnification,
                                                          pixel_size =pixel_size, folder2_items = second_folder)
        folder_items_list = [df_foc, df_nuc, df_cat, cell_list]
        name = fol
        everything_dict[name]= folder_items_list
    return everything_dict        






'''


folder_lista = ['C:\\Users\\Luiza Cherobini\\Desktop\\Nucear detection validation\\60x\\']

everydict = folders_dict_of_all(folder_list)

everydf = pd.DataFrame(columns = ['Image', 'Nucleus', 'Area', 'Perimeter', "NII",'Aspect',
                                  'Extent','Roundness','Radius_ratio', "Mean_int" ])
fs = cv.getFontScaleFromHeight(2,20,7)
path1 = 'C:\\Users\\Luiza Cherobini\\Desktop\\Nucear detection validation\\contour_equalization\\'
path2 = 'C:\\Users\\Luiza Cherobini\\Desktop\\Nucear detection validation\\fill_equalization\\'
for every_key , every_value in everydict.items():
    nucs = every_value[3]
    for key, value in nucs.items():
        im = value[0].image
        im2= np.zeros(im.shape, np.uint8)
        for c in value:
            new_line = [key, c.n, c.area,c.perimeter, c.NII, c.aspect, c.extent, c.roundness, 
                        c.radius_ratio, c.mean_intensity]
            everydf.loc[len(everydf)] = new_line
            cv.drawContours(im, c.cnt, -1, (255,255,255), 2)
            cv.drawContours(im2, c.cnt, -1, (255,255,255), 3)
            cv.putText(im, str(c.n), (c.bbox_x, c.bbox_y), 2, fs, (255,255,255), 2)
        cv.imwrite(path1 + key, im)
        cv.imwrite(path2 + key, im2)
       
everydf.to_csv(path1+ 'data60.csv')        
       
        
    
        
       
        

    
dic1 = everydict[list(everydict.keys())[0]]

nucs = dic1[3]
for key, value in nucs.items():
    im = value[0].image
    for c in value:
        lista = [key, c.area, c.NII]
        cv.drawContours(im, c.cnt, -1, (255,255,255), 2)
    cv.namedWindow('image', cv.WINDOW_NORMAL)
    cv.imshow('image', im)
    cv.waitKey(500)
    cv.destroyAllWindows()
    

   '''    


folderlist = ['D:\\Análises\\Controle vs tratamentos\\Minhas coisas\\Estático\\controle sem branco']
folderlist2 = ['D:\\Análises\\Controle vs tratamentos\\Minhas coisas\\Estático\\cisplatina sem branco']

for folder in folderlist:
    os.chdir(folder)
    files = os.listdir(folder)
    foc_c, nuc_c, cat_c, cells_c =generate_dfs(files, True, False, 60,  pixel_size =0.1083, folder2_items = None )
#df_foci, df_nuc, df_cat, cells = generate_dfs(fitems, True, False, False, 60)

for folder in folderlist2:
    os.chdir(folder)
    files = os.listdir(folder)
    foc_cddp, nuc_cddp, cat_cddp, cells_cddp =generate_dfs(files, True, False, 60,  pixel_size =0.1083, folder2_items = None )

'''
'''
#path= "C://Users//Luiza Cherobini//Documents//Doutorado//"

#name = re.sub(r".tif", "", fitems[0], flags=re.I) + ".xlsx"
#writer = pd.ExcelWriter(name, engine='xlsxwriter')


#nuc.to_excel(writer, sheet_name='Nuc')
#foc.to_excel(writer, sheet_name='Foci')
#categories.to_excel(writer, sheet_name='Categories')


#writer.save()


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

def find_df_NMA(cell_list):
    dfNMA = pd.DataFrame(columns = ['Nucleus', 'Area',
                                    "NII" , "Foci Count"])
    for cel in cell_list:
        a= cel.n
        b= cel.area
        c= cel.NII
        d= cel.foci
        #e= cel.CN_ratio
        #f = cel.NC_ratio
        row = [a,b,c,d]
        dfNMA.loc[len(dfNMA)] = row
    return dfNMA
 
       
def plot_NMA(df, ellipse):
    fig,ax = plt.subplots(1)
    sns.scatterplot(data=df, x="NII", y="Area", hue="Foci Count", 
                    palette='magma', ax=ax) 
    el = Ellipse(ellipse[0], ellipse[1], ellipse[2],color='#E04B66', fill=False)
    ax.add_patch(el)
    label = "Control"
    plt.title(label)
    plt.savefig(label + '.jpeg', dpi = 250, quality=95)
 
df_nma_list = []    
dfnma_c = pd.DataFrame(columns = ['Nucleus', 'Nucleus Area',
                                    "NII" , "Foci Count"])
for key, value in cells_c.items():
    df_nma = find_df_NMA(value)
    df_nma_list.append(df_nma)
dfnma_c = dfnma_c.append(df_nma_list, ignore_index = True)    
ellipse = thresh_NMA(dfnma_c)
plot_NMA(dfnma_c, ellipse)




ellipse = thresh_NMA(nuc_c)




folderlist = ['D:\\Análises\\Controle vs tratamentos\\Minhas coisas\\Overtime\\19h - 3 em 3 h\\CDDP\\imagens\\18hsem']

for folder in folderlist:
    os.chdir(folder)
    files = os.listdir(folder)
    foc_18h, nuc_18h, cat_18h, cells_18h =generate_dfs(files, True, False, 60,  pixel_size =0.1083, folder2_items = None )

'''

def convex_hull_and_deffects (cell_list, image_to_analyze):
    image = cv.imread(image_to_analyze)
    fs2 = cv.getFontScaleFromHeight(2,20,5)
    for c in cell_list:
        hull = cv.convexHull(c.cnt)
        hull2 = cv.convexHull(c.cnt,returnPoints=False)
        cv.drawContours(image, c.cnt, -1, (255,255,255), 1)
        cv.drawContours(image, hull, -1, (0,0,255), 1)
        cv.putText(image, str(c.n), (c.bbox_x, c.bbox_y), 2,fs2, (255,255,255), 1)
        defects = cv.convexityDefects(c.cnt, hull2)
        print ('deffects', defects)
        coordinate_far_list = []
        for i in range(defects.shape[0]):
            s,e,f,d = defects[i,0]
            start = tuple(c.cnt[s][0])
            end = tuple(c.cnt[e][0])
            far = tuple(c.cnt[f][0])
            if d>300:
                cv.circle(image,far,4,[0,0,255],-1)
                coordinate_far_list.append(far)
        pos, radius, degree =   cv.fitEllipse(c.cnt)
        if len(coordinate_far_list) == 2:
            distt = math.sqrt((coordinate_far_list[0][0]-coordinate_far_list[1][0])**2 + 
                              (coordinate_far_list[0][1]-coordinate_far_list[1][1])**2)
            print (c.n, radius, distt)
            if radius[0]*0.7 > distt:
                cv.line(image,coordinate_far_list[0],coordinate_far_list[1],[0,255,0],2)            
                
        if len(coordinate_far_list)>2:
            coordinate_far_list2 = coordinate_far_list.copy()
            
            line_coord_list = []
            for coord1 in coordinate_far_list:
                dist_list = []
                for coord2 in coordinate_far_list2:
                    if coord1 != coord2:
                        dist = math.sqrt((coord1[0]-coord2[0])**2 + (coord1[1]-coord2[1])**2)
                        dist_list.append(dist)
            
                if len(dist_list) > 0:            
                    index = dist_list.index(min(dist_list))
                    line_coord = (coordinate_far_list[index],coord1)
                    line_coord_list.append(line_coord)
                     
            final_coord_dist = []
            for coord1, coord2 in line_coord_list:
                dist = math.sqrt((coord1[0]-coord2[0])**2 + (coord1[1]-coord2[1])**2)
                final_coord_dist.append(dist)
            f = np.array(final_coord_dist)
            i= np.where(f==np.min(f[np.nonzero(f)]))[0][0]
            dis = final_coord_dist[i]
            final = line_coord_list[i]
            
            if radius[0]*0.7 > dis:
                cv.line(image, final[0], final[1] ,[0,255,255],2)

    cv.namedWindow('image', cv.WINDOW_NORMAL)
    cv.imshow('image', image)
    cv.waitKey(0)
    cv.destroyAllWindows()
    return print("done")
'''