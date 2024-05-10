import os, sys,io
from PIL import Image


#################### #Stuff that is required to modify for first time use
WORK_FOLDER = 'C:/Users/tc922/Downloads/CLIENT-Side'    #change the work folder to absolute path for command line execute (absolute path of the current folder) 
current_folder = './'
pub_K_path = current_folder + 'token/pub466.key'  #dowloaded public key requested from website
####################

#just for testing, you can input from terminal after running the program for normal use
image_path = current_folder + 'Viral Pneumonia-1254.png'  #(image name (path in current folder) )
Viz_cypherzip_path = current_folder+ 'Grad-CAM-Viz413.zip'

key_pair_path = current_folder + ''
enc_path = current_folder + 'Image2cyphertexts' 
client_keys_index = '-client'


import sys #import encryption parts
sys.path.append(os.path.join(WORK_FOLDER,'Encryp_Kyber'))  #path of Kyber related path
print('Modify the system paht of encry_decry is also necessary')
#Modify the system paht of encry_decry is also necessary
from encry_decry import *
from cyphertext_proc import *
sys.path.append(os.path.join(WORK_FOLDER,'Encryp_Kyber/Kyber'))
from kyber import  Kyber512 #you should also try Kyber768 and Kyber 1024 (not tested in this code)

print('Input number to choose client mode: \n\
      1. Encrypt the chest X-ray image \n\
      2. Generate the client key pair \n\
      3. Decrypt the Grad-CAM Viz cypher texts\n')
      
print('Instruction: You should request the public from website first, then copy \
it into /token folder and modify the \'pub_K_path\' to its name. \n\
Then specify the image you want to upload in \'image_path\'. \n\
Next run this program with input 1 to generate cypher text and the zipped file\n\
Run the program again with inputting 2 to generate key pair for client. (you can run one time) \n\
Upload the cypher package with public key from client side \n\
Download the encrypted Grad-CAM visualization from website \n\
Specify the package name at \'Viz_cypherzip_paht\' before run the program with inputting 3')
print('Press Ctrl + C to exit the program\n')

while True:
    mode = input('Select 1/2/3 to input:  ')
    try:
        if mode == '1':
            image_path = './' + str(input('Please input image file name (inside current path):  '))
            ###encrypt the image for uploading
            image = Image.open(image_path)
        
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='JPEG')
            img_bytes = image_bytes.getvalue()
        
            with open (pub_K_path,'rb') as pub:
                    pub_k = pub.read()
        
            enc_data = kyber_encryption(public_key = pub_k, image_bytes = img_bytes)
                
            #Save data for transmission
            if os.path.exists(enc_path) != True:
                os.mkdir(enc_path)
                #enc_path = enc_path + '/Image2cyphertexts'
                #os.mkdir(enc_path)
            for i,data_chunk in enumerate(enc_data):
                data_path = os.path.join(enc_path,'enc_data-'+str(i))
                with open (data_path,'wb') as data:
                    data.write(data_chunk)
        
            compress_cypher(enc_path, 'Encrypted_Image', zip_folder = current_folder)
            print(f'Location of the cypher package is {enc_path}/Encrypted_Image.zip')
            print('Done with step 1\n')
        
        elif mode == '2':
            ###generate key pairs: pub -> server  sec -> client
            pub, sec = key_gen()
            save_keys(pub,sec, key_pair_path, index = client_keys_index)
            print('Done with step 2\n')
        
        elif mode == '3':
            Viz_cypherzip_path = './' + str(input('Please input name of Grad-CAM Viz cypher package downloaded from website:  '))
            with ZipFile(Viz_cypherzip_path,'r') as zipf:
                zipf.extractall(path = './Grad-CAM-cypher')
            ##decrypt Grad-CAM Viz:
            sec_K_path = os.path.join(key_pair_path, 'sec-client.key')
            print(f'Use key for decryption: {sec_K_path}')
            with open (sec_K_path,'rb') as sec:
                sec_k = sec.read()
            print('You need to unzip this Grad-CAM-Viz cyphertext package first')
            enc_data_list = read_cyphertexts2list('./Grad-CAM-cypher')
        
            #decrypt the cyphertexts into img
            dec_img = kyber_decryption(sec_k,enc_data_list)
            dec_img.save('Grad-CAM-Viz.png')
            print('Done with step 3\n')
        else:
            print('Invalid! Plese input proper the mode (1~3)')
    
    except:
        pass