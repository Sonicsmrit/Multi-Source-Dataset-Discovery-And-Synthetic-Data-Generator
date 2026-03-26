
import os


os.environ['KAGGLE_USERNAME'] = 'mrsonic'
os.environ['KAGGLE_KEY'] = 'KGAT_dc1b1cf301ffced3195e37514eb32090'


from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()

datasets = api.dataset_list(search="anime")
for d in datasets[:5]:
    print(d.title)