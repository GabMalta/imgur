from imgur import Imgur
from requests_policy.http import http

client_id = 'e97daba7b37d28c'
client_secret = 'ae0d154069833d97e44f14ca50b41d58d5e5a3f4'

client = Imgur(client_id, client_secret)

images = client.create_album_with_images('CHITAO FLEX D531', r'D:\SITE LEGITIMA TEXTIL\CATÁLOGO DIGITAL\CHITAO FLEX D531\Fotos')

print(images)
