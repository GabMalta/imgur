import time
from requests import Response
from requests_policy.http import http
from core import settings

import os
from PIL import Image

class Imgur():
  
  def __init__(self, client_id, client_secret):  
    
    self.client_id = client_id
    self.client_secret = client_secret
    self.refresh_token = self.get_refresh_token()
    
    self.generate_credentials()
  
  def set_alternative_client_id_and_secret(self):
    
    if settings.ALTERNATIVE_CLIENT_SECRET and settings.ALTERNATIVE_CLIENT_ID:
      self.client_id = settings.ALTERNATIVE_CLIENT_ID
      self.client_secret = settings.ALTERNATIVE_CLIENT_SECRET
    else:
      raise ValueError('ALTERNATIVE_CLIENT_ID e ALTERNATIVO_CLIENT_SECRET não configurados')

    
  def get_refresh_token(self, alternative_token=False):
    
    if alternative_token:
      path_refresh_token = r'./tokens/refresh_token2.txt'
    else:
      path_refresh_token = r'./tokens/refresh_token.txt'
    
    with open(path_refresh_token, 'r') as rt:
      refresh_token = rt.read()
      
    return refresh_token

  def get_access_token(self):
    
    with open(r'./tokens/access_token.txt', 'r') as at:
      access_token = at.read()
      
    return access_token

  def set_access_token(self, access_token):
    
    with open(r'./tokens/access_token.txt', 'w') as at:
      access_token = at.write(access_token)

  def set_refresh_token(self, refresh_token):
    
    with open(r'./tokens/refresh_token.txt', 'w') as rt:
      refresh_token = rt.write(refresh_token)
      
  def generate_credentials(self):

    url = 'https://api.imgur.com/oauth2/token'

    payload={
      'refresh_token': self.refresh_token,
      'client_id': self.client_id,
      'client_secret': self.client_secret,
      'grant_type': 'refresh_token'
    }
    
    files=[]
    
    headers = {}

    response = http.post(url, headers=headers, data=payload, files=files).json()
    
    self.access_token = response['access_token']
    self.refresh_token = response['refresh_token']
    self.username = response['account_username']
    self.account_id = response['account_id']
    
    self.set_access_token(self.access_token)
    self.set_refresh_token(self.refresh_token)

  def get_tuple_image_name(self, path: str):
    name = os.path.basename(path)
    
    
    if not self.path_is_image(path):
      raise ValueError('Caminho informado em path tem que ser uma imagem válida')
    else:
      with open(path, 'rb') as img:
        image = img.read()
      return ('image', (name, image, 'image/jpeg'))
      
  def get_path_image(self, path: str | list) -> list :
    
    if type(path) == list:
      files = [self.get_tuple_image_name(sub_path) for sub_path in path]
      
    elif type(path) == str:
      
        
      files = [self.get_tuple_image_name(path)]
    
    else:
      
      raise 'Parametros devem ser do tipo str ou list'

    return files
  
  def path_is_image(self, path):
    
    try:
      with Image.open(path) as img:
        img.verify()
      return True
    
    except:
      return False
  
  def get_list_of_folder(self, folder):
    
    files = os.listdir(folder)
    
    if 'desktop.ini' in files:
      files.remove('desktop.ini')
    
    paths = []
    
    for file in files:
      
      path = os.path.join(folder, file)
      
      if os.path.isfile(path):
        
        if self.path_is_image(path):
          paths.append(path)
        else:
          print(f'Este arquivo não é uma imagem válida: {file}')
    
    return paths

  def upload_image(self, path: str, album_id:str='') -> dict:
    
    title = os.path.splitext(os.path.basename(path))[0]
    
    url = "https://api.imgur.com/3/upload"

    payload={'type': 'image',
    'album': album_id,
    'title': title,
    'description': title}
    
    files = self.get_path_image(path)
    
    headers = {
      'Authorization': f'Bearer {self.access_token}'
    }

    try:
      response = http.post(url, headers=headers, data=payload, files=files)
      
      self.set_rates_limits(response)
      
      if response.status_code != 200:
        return response.text
      
      response = response.json()['data']
      
      data = {
        'id': response['id'],
        'title': response['title'],
        'width': response['width'],
        'height': response['height'],
        'size': response['size'],
        'link': response['link'],
      }
      
      print(f'{data['title']} adicionado com sucesso!')
      
      return data
    
    except Exception as ex:
      print(ex)
  
  def upload_images(self, paths: list | str, is_folder=True, album_id:str='') -> dict:
    
    if is_folder:
      
      if type(paths) == str:
        paths = self.get_list_of_folder(paths)
        
      elif type(paths) == list:
        raise 'Defina is_folder como False se deseja passar uma lista de caminhos como parametro'
    
      else:
        raise 'Para passar uma pasta de imagens você deve informar uma string com o caminho'
      
    
    else:
      if type(paths) == str:
        raise 'Para passar uma pasta de imagens você deve informar uma string com o caminho e is_folder deve ser True'
      
    
    images = []
    
    print('Iniciando Upload de arquivos...')
    
    if len(paths) <= 25:
      for path in paths:
        
        try:
          images.append(self.upload_image(path, album_id))
        except:
          print(f'{path} não cadastrado.')

    else:
      
      total_images = len(paths)
      for i in range(0, total_images, 20):
        batch = paths[i:i+20]
        
        for img_batch in batch:
          images.append(self.upload_image(img_batch, album_id))

        time.sleep(10)
    
    data = {
      'quantity': len(images),
      'data': images
    }
    
    return data
      
  def create_album(self, title, images:list=[]):
    
    url = "https://api.imgur.com/3/album"

    payload={'ids[]': images,
    'title': title,
    'description': '',
    'cover': ''}
    files=[

    ]
    headers = {
      'Authorization': f'Bearer {self.access_token}'
    }

    response = http.post(url, headers=headers, data=payload, files=files)

    return response.json()
  
  def create_album_with_images(self, title, folder_path:str):
    
    album = self.create_album(title)
    
    album_id = album['data']['id']
    
    images = self.upload_images(folder_path, album_id=album_id)['data']
    
    data = {
      'album': album,
      'images': images
    }
    
    return data
  
  def verify_credits(self):
        url = "https://api.imgur.com/3/credits"

        payload={}
        headers = {
          'Authorization': f'Bearer {self.access_token}'
        }

        response = http.get(url, headers=headers, data=payload)

        print(response.text)
  
  def account_base(self):
    
    url = f"https://api.imgur.com/3/account/{self.username}/settings"

    payload={}
    files={}
    headers = {
      'Authorization': f'Bearer {self.access_token}'
    }

    response = http.get(url, headers=headers, data=payload, files=files)

    print(response.text)    
  
  def set_rates_limits(self, response:Response) -> None:
    
    client_limit = response.headers.get('X-RateLimit-ClientLimit')
    client_remaining = response.headers.get('X-RateLimit-ClientRemaining')
    user_limit = response.headers.get('X-RateLimit-UserLimit')
    user_remaining = response.headers.get('X-RateLimit-UserRemaining')
    user_reset = response.headers.get('X-RateLimit-UserReset')
    
    with open('./rate_limits_api/rate_limit.txt', 'w') as res:
      res.write(client_limit)
    with open('./rate_limits_api/rate_client_remaining.txt', 'w') as res:
      res.write(client_remaining)
    with open('./rate_limits_api/rate_user_limit.txt', 'w') as res:
      res.write(user_limit)
    with open('./rate_limits_api/rate_user_remaining.txt', 'w') as res:
      res.write(user_remaining)
    with open('./rate_limits_api/rate_user_reset.txt', 'w') as res:
      res.write(user_reset)
