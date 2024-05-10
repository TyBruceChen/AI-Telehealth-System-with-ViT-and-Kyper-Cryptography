from torch import nn
import torch
from timm import create_model
import numpy as np
from PIL import Image
from torchvision import transforms
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import math

class GradCAM:
  def __init__(self,model,
               img_path:str,
               layer_idx: int = 2,
               input_shape = (224,224),
               model_type: str = 'Normal'
               ):
    """
    params:
    layer_idx: the index of the layer where you want to visulize (it count
      from classifier to input layer).
    input_shape: the image shape to put into the model
    model: the model you want to visualize
    img_path: the path of the tested image
    model_type: some special model need addtional method to process the activations
      in order to get Grad-CAM. Currently, there's only function to handel vision
      transformer.
    """
    self.model = model
    self.layer_idx = -layer_idx
    self.img_path = img_path
    self.input_shape = input_shape
    self.model_type = model_type
    print('The model types you can select from are \'Normal\', \'ViT\'')

  def __call__(self):
    model = self.model

    extractor = nn.Sequential(*list(model.children())[:self.layer_idx]) #truncate the model from where your specified idx
    classifier = nn.Sequential(*list(model.children())[self.layer_idx:])
    #print(extractor)

    img = Image.open(self.img_path).convert('RGB').resize(self.input_shape)
    transform = transforms.Compose([transforms.ToTensor()])
    img = transform(img)
    img = torch.unsqueeze(img, 0) #preprocess the image to tensor: (1,C,H,W)
    img.requires_grad = True

    result_ = model(img)

    result = result_.argmax()  #get the prediction category
    class_Idx = result  #the grad-cam will visualize the prediction towards a specific category. (Here is the model's prediction)
    self.result_class = class_Idx #make the result accessible from outside

    softmax = nn.Softmax(dim = -1)  #convert the logits into probabiliries
    self.confidence = round(float(softmax(result_)[0][class_Idx])*100,2)  #make the model's confidence to the prediction accessible

    activations = extractor(img)  #get the activations (output features) from target layer
    activations.retain_grad() #pytorch will automatically free the parameters' gradients that are not provided by user
                                #so here it needs to be specified to keep the gradient of activation w.r.t prediction logits

    print(f'Activation Shape:{activations.shape}')

    prediction_logits = classifier(activations) #the activation is fed into rest layers to get the prediction tensor
    print(f'Prediction_logits Shape:{prediction_logits.shape}')
    print(f'The Grad-CAM will be plotted based on model prediction result: {class_Idx}')

    if self.model_type == 'Normal':
      prediction_logits = prediction_logits[:,class_Idx]  #only use the specific class to back propagate
    elif self.model_type == 'ViT':
      prediction_logits = prediction_logits[:,:,class_Idx]

    grad_output = torch.ones_like(prediction_logits)
    print(grad_output.shape)

    prediction_logits.backward(gradient = grad_output)  #according to pytorch, backward() should specify
                                                          #with a tensor which its length is the same as backward tensor
                                                            #when the tensor contains more than one number
    d_act = activations.grad  #get the gradient of activation from target layer w.r.t. the specified category

    if self.model_type == 'Normal':
      print(f'Specified activation shape:{d_act.shape}')
      d_act = d_act.permute(0,2,3,1)  #(1,C,H,W) -> (1,H,W,C)
      activations = activations.permute(0,2,3,1)
    elif self.model_type == 'ViT':
      d_act = self.output_decompose_vit_grad_cam(d_act)
      activations = self.output_decompose_vit_grad_cam(activations[:,:,:])

    print(f'gradient shape (predictioin logti(s) w.r.t. feature logits: ){d_act.shape}')
    pooled_grads = torch.mean(d_act,dim = (0,1,2))  #according to the paper, the pooling happens all axis except the channel dim
    print(f'pooled activation layer\'s gradient shape (predictioin logti(s) w.r.t. feature logits: ){pooled_grads.shape}')

    heatmap = activations.detach().numpy()[0] #for tensors where its requires_grad = True, need detach() function to convert to ndarray
    pooled_grads = pooled_grads.numpy()

    #back propagate
    for  i in range(d_act.shape[-1]):
      heatmap[:,:,i] *= pooled_grads[i]
    print(f'producting pooled gradient factor and activations to get heatmap: {heatmap.shape}')
    heatmap = np.mean(heatmap, axis = -1) #here the heatmap shapes as (H,W,1)
    print(f'pooling on heatmap: {heatmap.shape}')

    print(f'Maximum pixel value of heatmap is {heatmap.max()}')
    threshold = np.median(heatmap)
    #threshold = 0
    heatmap_filtered = np.maximum(heatmap,threshold)
    heatmap_filtered[heatmap_filtered == threshold] = threshold * 0.55
    heatmap_filtered[heatmap_filtered <= threshold/2] = 0
    #print(f'Minimum value of heatmap{heatmap_filtered.min()}')
    self.heatmap = np.uint8(255*heatmap_filtered/np.max(heatmap))  #keep the logits that are greater than specific value
      #in the paper, that is to say, only keep the positive influence with the specific class.
        #then normalize the heatmap and recale its value range from 0 to 255.


  def origin_cam_visualization(self,save_path = None):
    #this function needed to be modified in server implementation
    #display the orignal size heatmap (H,W,1)
    plt.rcParams.update({'font.size': 14})
    plt.matshow(self.heatmap)
    plt.title('Original generated heatmap')
    plt.show()
    if save_path != None:
      plt.savefig(save_path)


  def imposing_visualization(self,save_path = None):
    #this function needed to be modified in server implementation
    alpha = 0.5 #how much CAM will overlap on original image
    plt.figure(figsize = (5,5))
    plt.rcParams.update({'font.size': 8})

    jet = cm.get_cmap('jet')  #create the color map object
    jet_colors = jet(np.arange(256))[:,:3]
    print(f'jet_color shape: {jet_colors.shape}')
    jet_colors = (jet_colors*256).astype(np.uint8)  #generate a color (RGB) image which has small H and W
                                                      # and maps the intensity to color from red to blue

    #jet_heatmap = (jet_colors[self.heatmap] * alpha).astype(np.uint8)
    #print(jet_heatmap.shape)
    #jet_heatmap = Image.fromarray(jet_heatmap).resize(self.input_shape)

    self.heatmap = Image.fromarray(self.heatmap).resize(self.input_shape)
    jet_heatmap = (jet_colors[np.uint8(self.heatmap)] ).astype(np.uint8)

    img = Image.open(self.img_path).convert('RGB').resize(self.input_shape)

    jet_heatmap = np.asarray(jet_heatmap)

    img_cam = np.uint8(np.asarray(img)*(1-alpha)*1.2) + np.uint8(np.asarray(jet_heatmap* alpha))

    plt.subplot(2,2,1)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(img)
    plt.title('Original Image')


    plt.subplot(2,2,2)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(img_cam)
    plt.title('Overlapped Colormap Image')

    plt.subplot(2,2,3)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(self.heatmap)
    plt.title('Heatmap (2-D Magnitude)')

    plt.subplot(2,2,4)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(jet_heatmap/255)
    plt.title('Projected Colormap (3-D)')

    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=-0.05, hspace=0.1)

    if save_path != None:
      plt.savefig(save_path,bbox_inches = 'tight', pad_inches = 0.1)



  def output_decompose_vit_grad_cam(self, vit_input):
    #decompose on vit's sequence dimension
    _, HW, C = vit_input.shape
    print(HW)
    HW = int(math.sqrt(HW))
    print(HW)
    vit_output = torch.reshape(vit_input,(1,HW,HW,C))

    #vit_output = vit_output.permute(0,3,1,2)
    return vit_output