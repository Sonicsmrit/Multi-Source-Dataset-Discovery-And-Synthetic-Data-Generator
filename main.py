from CLI import *
from DisplayResults import * 
from cleaning import *
from synthetic import *

if __name__ == "__main__":

    download_datasets()
    cleaning_pipeline()
    synthetic_data_pipeline()