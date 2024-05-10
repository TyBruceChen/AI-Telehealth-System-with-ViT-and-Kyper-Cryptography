from flask import Flask,url_for,render_template,request
import Crypto
from PIL import Image
from blob_storage import *
from server_model_test import *
from text_modification import *
from GradCAM import GradCAM
import os,time,random, shutil

WORK_FOLDER = '/home/piko/Documents/Flask_2/'    #change the work folder to absolute path for command line execute 
os.chdir(WORK_FOLDER)

temp_img_path = 'temp_imgs'
#temp_img_path = 'home/site/temp_imgs'   #when it's uploaded to Azure server.
cypher_zip_folder = 'cypher_zips'
client_key_folder = 'temp_client_pub_key'
cypher_viz_folder = 'cypher_Vizs'
model_folder = 'models/' #blob folder for model saving
model_path = os.path.join(model_folder,'Diagnosis_Model.pt') 
model_storage_folder = model_folder
storage_path = os.path.join(model_storage_folder,'Diagnosis_Model.pt') 

sample_folder = 'imgs/'  #blob folder for sample imgs
sample_database_name_list = os.listdir('static/sample_imgs')  #the samples images contained in local should be exact same as in the blob server

result_visualization_replace_frame = "id=\"resultViz\" src=\"static/Confusion Matrix.png\" style=\"display: none;"

import sys #import encryption parts
sys.path.append(os.path.join(WORK_FOLDER,'Encryp_Kyber'))  #path of Kyber related path
from encry_decry import *
from cyphertext_proc import *
sys.path.append(os.path.join(WORK_FOLDER,'Encryp_Kyber/Kyber'))
from kyber import  Kyber512 #you should also try Kyber768 and Kyber 1024 (not tested in this code)

app = Flask(__name__)

if os.path.exists(temp_img_path) != True:
        os.mkdir(temp_img_path) #create the local server to temporarily store the imgs

if os.path.exists(model_storage_folder) != True:
        os.mkdir(model_storage_folder) #create the local server to temporarily store the imgs

blob_server_client = blob_server_client()   #build the connection to the azure storage service
if os.path.isfile(storage_path) != True:
    blob_server_client.download_file_blob(filename = model_path, storage_name = storage_path)

try:
    server_model = load_model(model_path)   #load the model
except:
    blob_server_client.download_file_blob(filename = model_path, storage_name = storage_path) 
    server_model = load_model(model_path)   #load the model

#generate a new pair of token for this server cryptography
keyPaire_folder = os.path.join(WORK_FOLDER,'static','kyber_tokens')
try:
     keyID = int(random.random()*10000)
     pub,sec = key_gen()
except:
     print('Failed Key Generation!')
save_keys(pub,sec, keyPaire_folder, keyID)

#keyID = ""  #the key pair index for the tested package

@app.route('/temp/<var>')
def temp(var):
    # test page
    return '<!DOCTYPE html>\
            <html><head></head> \
            <body>This is a temp page</body>\
            </html>'

@app.route('/',methods = ['GET','POST'])
def file_handle():
    #wait_time = 0  #let the thread to run 10s
    if request.method == 'POST':
        print(request.files)
        print(request.form)
        ################system experience:
        ###request public key for encryption
        if 'keyRequest' in request.form:
             print('Received Key request')
             html_update = text_modification()
             pubkey_path = f"<a href=\"/static/kyber_tokens/pub{keyID}.key\" download=\"pub1618.key\">Download Public Key</a>"
             return html_update.replace_content(pubkey_path,'Please Request Public Key Download First')
        
        ###decryption and prediction
        if 'cypher_zip' in request.files:
            print('Cypher zip received')
            cfile = request.files['cypher_zip']    #get information with cypher package
            cypherPackId = int(random.random()*1000)  #file id (name) for saving the received package
            cypher_zip_path = os.path.join(cypher_zip_folder,str(cypherPackId)+'.zip')
            cfile.save(cypher_zip_path) #save file

            try:
                extract_cypher(cypher_zip_path,seed = str(cypherPackId)) #extract the cyphertexts from package and store inside ./cypher_zips/id/id
            except:
                 print('Please Upload Properly Formatted Package!')

            #read the secret key
            #try:
            sec_K_path = os.path.join(keyPaire_folder, 'sec' + str(keyID) + '.key')
            print(f'Use key for decryption: {sec_K_path}')
            with open (sec_K_path,'rb') as sec:
                sec_k = sec.read()
            enc_data_list = read_cyphertexts2list(os.path.join(cypher_zip_folder,str(cypherPackId)))
            print(f'Received cypher list leng is {len(enc_data_list)}')
            #decrypt the cyphertexts into img
            dec_img = kyber_decryption(sec_k,enc_data_list)
            try:
                pass
            except:
                print('Error!')
                print('The error is most due to mis-pairing of encrypt-decrypt content matching')
                print('e.x.: use different pairs of keys for encrypting the image and decrypting the cyphertexts')

            #save img.png:
            img_name = 'decrypted_img' + str(int(random.random()*10000)) + '.png'
            img_path = os.path.join(temp_img_path,img_name)
            dec_img.save(img_path)
            
            ###analyze the image with proposed FTViT(save as AI Diagnose Experience part):
            try:
                img = img_process(img_path = img_path)
                y = server_model(img)   #prediction

                html_update = text_modification()

                if 'pubkey_enc' in request.files:  #generating visualization
                    cam = GradCAM(server_model,img_path,layer_idx=6,model_type = 'ViT')
                    cam()
                    Viz_save_path = os.path.join('static','temp_viz',img_name)
                    cam.imposing_visualization(Viz_save_path)
                    print('Finish Grad-CAM images generating')

                    #save the public key from clients:
                    try:
                        kfile = request.files['pubkey_enc']
                        clientKeyId = int(random.random()*10000)  #file id (name) for saving the received package
                        clientKey_path = os.path.join(client_key_folder, str(clientKeyId) + '.key')
                        print(f'Client Key path:{clientKey_path}')
                        kfile.save(clientKey_path)  #save the key
                        #read the key:
                        with open (clientKey_path,'rb') as pub:
                            pub_k = pub.read()
                        
                        viz_img = Image.open(Viz_save_path).convert('RGB')
                        img_bytes = img2bytes(viz_img)
                        #encrypt the Grad-CAM image
                        enc_data = kyber_encryption(public_key = pub_k, image_bytes = img_bytes)
                        print(f'The length of encrypted cypher text from Grad-CAM map is: {len(enc_data)}')

                        #save cyphertexts:
                        cypher_viz_path = os.path.join(cypher_viz_folder,'Grad-CAM-Viz')
                        save_cypher(enc_data,cypher_viz_path,seed = str(clientKeyId))

                        #compress (zip) cyphertexts:
                        compress_cypher(mpath = cypher_viz_path + str(clientKeyId), zip_name = "Grad-CAM-Viz", seed = str(clientKeyId))
                        print(clientKeyId)

                        #update html content to client
                        html_update.replace_content(new_element = "id=\"viz-encrypt\" style=\"display: display;",replaced_element = "id=\"viz-encrypt\" style=\"display: none;")
                        viz_cypher_zip_path = f"id=\"viz-cypher-download\" href=\"static/Viz_cyphers/Grad-CAM-Viz{str(clientKeyId)}.zip\"> Download Encrypted Grad-CAM Viz by Kyber-512"
                        html_update.replace_content(viz_cypher_zip_path ,"id=\"viz-cypher-download\">")
                        try:
                            shutil.rmtree(cypher_viz_path + str(clientKeyId))  #delete the saved cyphertexts folder of Grad-CAM Viz
                            os.remove(clientKey_path)   #delete the saved client public key
                            print(f'Save Grad-CAM path: {Viz_save_path}')
                            os.remove(Viz_save_path)    #delete the Grad-CAM visualization from server, only keep the cyphertext package
                            print('Viz items deleted, client key deleted, viz cypher packa keeped')
                        except:
                            print('Failed to delete Grad-CAM Viz related items/ client public key')
                    except:
                        print('Failed to encrypt the Grad-CAM Viz through client public key')

                try:    #delete the cypher texts folder
                    shutil.rmtree(os.path.join(cypher_zip_folder,str(cypherPackId))+'/')
                    #os.rmdir(os.path.join(cypher_zip_folder,str(cypherPackId))+'/')
                    os.remove(os.path.join(cypher_zip_folder,str(cypherPackId)+'.zip'))
                    os.remove(img_path)
                    print('Server File deleted.')
                except:
                    print('Failed to delete server file!')

                result = int(y.argmax())
                print(lung_type(result))

                html_update.replace_content("id=\"decry-predict-result\" style=\"display: block;","id=\"decry-predict-result\" style=\"display: none;")
                return html_update.replace_content("id=\"result-from-system\">" + lung_type(result),replaced_element= "id=\"result-from-system\">")

            except:
                print('Fail to loaad the image')
                print('Please don not upload empty file!')
                html_update =  text_modification()
                return html_update.replace_content('id=\"result-from-system\">Error! Please Follow the instruction!',replaced_element= "id=\"result-from-system\">")

        ###############AI diagnose experience
        if 'pic' in request.files:  
            file = request.files['pic']
            try:
                upload_name = file.filename
                print(upload_name) #see the name of uploaded file
                upload_name = upload_name.split('.')[0]

                img_name = str(upload_name) + str(int(random.random()*10000)) + '.png'
                file_name = os.path.join( temp_img_path,img_name)    #temperaryly save the img on local
                file.save(file_name)
                # the initial idea is to save the file then read as binary type
                """
                with open(file_name,'rb') as bin_file:
                    blob_server_client.store_file_blob(bin_file = bin_file, filename = img_name)
                print('Upload Finish.')
                """
                try:
                    img = img_process(file_name)    #read the img, reshape, and normalize
                    y = server_model(img)   #prediction
                    cam = GradCAM(server_model,file_name,layer_idx=6,model_type = 'ViT')
                    cam()
                    Viz_save_path = os.path.join('static','temp_viz',img_name)
                    print(Viz_save_path)
                    cam.imposing_visualization(Viz_save_path)
                    updateViz = f"id=\"resultViz\" src=\"{Viz_save_path}\" style=\"display: block;"
                    try:
                        os.remove(file_name)
                        print('Server File deleted.')
                    except:
                        print('Fail to delete server file!')

                    result = int(y.argmax())
                    print(lung_type(result))

                    html_update = text_modification()
                    html_update.replace_content(updateViz,result_visualization_replace_frame)
                    return html_update.replace_content(lung_type(result),replaced_element= 'waiting to be uploaded')
                except:
                    print('Fail to loaad the image')
                    print('Please don not upload empty file!')
                    html_update =  text_modification()
                    return html_update.replace_content('Error! Please don not upload empty file! ',replaced_element= 'waiting to be uploaded')

            except:
                pass
                print('Error!')           
    return render_template('/index.html', name = None)


if __name__ == '__main__':
    app.run(port = '5000')


