# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 13:39:24 2024

@author: tc922
"""

from zipfile import ZipFile
import os
import time
import io

def img2bytes(img):
    """
    convert the PIL img into bytpes for encryption
    """
    image_bytes = io.BytesIO()
    img.save(image_bytes, format='JPEG')
    img_bytes = image_bytes.getvalue()
    return img_bytes

def save_cypher(enc_data, enc_path, seed = ""):
    """
    generate a bunch of files which contain binary cypher information
    
    enc_data: list of binaries, containing cyphertexts
    enc_path: the folder where files will be stored
    """
#generate cyphertext files

    os.makedirs(enc_path + seed)
    
    for i,data_chunk in enumerate(enc_data):
        data_path = os.path.join(enc_path + seed,'enc_data-'+str(i))
        with open (data_path,'wb') as data:
            data.write(data_chunk)

def compress_cypher(mpath, zip_name, zip_folder = './static/Viz_cyphers', seed = ""):
    """
    mpath : string
        Where the cypher files are stored.
    zip_file_name : string
        the path + zip file name (no '.zip')
    seed : string
        the suffix of files name.
    """
#compress to zip file
    #ts = time.time()

#mpath = './encrypted_data'
#zip_file_name = 'temp_cyphertexts.zip'

    cyphertext_list = os.listdir(mpath)
    cyphertext_path_list = []
    for cyphertext in cyphertext_list:
        cyphertext_path_list.append(os.path.join(mpath,cyphertext))
        
    zip_name = zip_name + seed
    with ZipFile(os.path.join(zip_folder,zip_name) + '.zip','w') as zipf:
        for i,cypher_path in enumerate(cyphertext_path_list):
            zipf.write(cypher_path,arcname=cyphertext_list[i])
    
            
    #print(time.time() - ts)

def extract_cypher(zip_path, seed = "", extraction_path = "./cypher_zips"):
    """
    zip_name: string
        the path + zip file name (no '.zip')
    extraction_path: string
        the folder that zip file will be extract to
    seed: string
        the suffix of files name (should be the same as cypher_folder_suffix for same client)
    """
    
    cyphertext_folder = os.path.join(extraction_path,str(seed))
    os.mkdir(cyphertext_folder)
    
    #extract files
    with ZipFile(zip_path,'r') as zipf:
        zipf.extractall(path = cyphertext_folder)
    
    #rename
    original_folder_name = os.path.join(extraction_path,str(seed),os.listdir(cyphertext_folder)[0])
    os.rename(original_folder_name,os.path.join(extraction_path,str(seed),str(seed)))
        
def delete_files(file_name):
    """
    delete the specified file
    """
    os.remove(file_name)
    print(f'Successfully delete file: {file_name}')
    
    
def delete_folder(file_name):
    """
    delete the specified folder
    """
    os.rmdir(file_name)
    print(f'Successfully delete folder: {file_name}')

def save_keys(pub_key,sec_key,key_path ='.',index = ''):
    """
    keypath: folder for key-pairss
    index: id for key-pairs
    """
    pub_K_path = os.path.join(key_path, 'pub'+str(index)+'.key')
    with open (pub_K_path,'wb') as pub:
        pub.write(pub_key)
              
    sec_K_path = os.path.join(key_path, 'sec'+str(index)+'.key')
    with open (sec_K_path,'wb') as sec:
        sec.write(sec_key)

def read_cyphertexts2list(cypher_folder_path):
    list_enc_data = []
    print('The name of each cypher text should be: enc_data-index')
    for i,data_chunk in enumerate(os.listdir(cypher_folder_path)):
        data_path = os.path.join(cypher_folder_path,'enc_data-'+str(i))
        with open (data_path,'rb') as data:
            chunk_info = data.read()
        list_enc_data.append(chunk_info)
    return list_enc_data