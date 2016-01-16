import os
api_token = os.environ['DO_API_TOKEN']

from dopy.manager import DoManager
do = DoManager(None, api_token, api_version=2)
imgs = do.all_images()
fbsd = [img for img in imgs if img['distribution'] == 'FreeBSD']
