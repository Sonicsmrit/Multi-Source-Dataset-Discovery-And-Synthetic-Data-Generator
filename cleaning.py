import os, glob, shutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt
import pandas as pd


console = Console()

def get_download_files():
    if not os.path.exists("Downloads"):
        return []
    
    return [f for f in os.listdir("Downloads") if os.path.isdir(f"Downloads/{f}")]

def get_cleaned_files():
    if not os.path.exists("Cleaned"):
        return []
    
    return [f for f in os.listdir("Cleaned") if os.path.isdir(f"Cleaned/{f}")]


def find_tabular_files(ds_folder):
    extensions = ["*.csv", "*.json", "*.xlsx", "*.parquet"]

    files = []

    for ex in extensions:
        files.extend(glob.glob(f"Downloads/{ds_folder}/**/{ex}", recursive=True))
    
    return files

def cleaning_pipeline():

    skip = False
    datasets = get_download_files()
    if not datasets:
        console.print(Panel("[magenta] No downloaded datasets found [/magenta]", border_style="bold red", box=box.DOUBLE))
        return
    
    table = Table(box=box.DOUBLE_EDGE,
                border_style="magenta",
                header_style="bold magenta",
                show_lines=True
                )
    table.add_column("【 SN 】", style="pink1", justify="center")
    table.add_column("【 DATASET 】", style="white")


    for i, ds in enumerate(datasets, 1):
        table.add_row(f"#{i}",ds)

    console.print(table)

    console.print(Panel("[magenta] CLEANING DATASETS [/magenta]",subtitle="Enter Numbers (ex: 1,2,3...) or type 'skip' to skip it" ,  border_style="bold magenta", box=box.DOUBLE))


    
    while True:
        choice = Prompt.ask("\n[bold magenta] Enter SN of Datasets to Clean: [/bold magenta]")

        if choice.lower() == "skip":
            skip = True

            break
        else:
            try:
                index = [int(x.strip()) for x in choice.split(",")]

                if any(i<1 or i>len(datasets) for i in index):
                    raise ValueError
                break
            except:
                console.print(Panel("[magenta] Invalid Input [/magenta]", border_style="bold red", box=box.DOUBLE))
    
    if not skip:
        for i in index:
            dataset_folder = datasets[i - 1]

            files = find_tabular_files(dataset_folder)
            for f in files:
                clean_files(f)
    
    cleanup()
    

def cleanup():
    datasets = get_download_files()
    cleaned = get_cleaned_files()
    stop = False

    while stop is False:

        while True:
            question = Prompt.ask("\n[magenta]Do you want to DELETE Downloads or Cleaned Datasets(Yes/No): [/magenta]")
            if question.lower() not in ["yes", "no"]:
                console.print(Panel("[magenta] Invalid Input [/magenta]", border_style="bold red", box=box.DOUBLE))
                continue
            
            break

        if question.lower() == "yes":
            while True:
                try:
                    whichone = Prompt.ask("\n[magenta]Downloads or Cleaned: [/magenta]")
                    

                    if whichone.lower() not in ["downloads", "cleaned"]:
                        raise ValueError
                    
                    break
                except:
                    console.print(Panel("[magenta] Invalid Input [/magenta]", border_style="bold red", box=box.DOUBLE))
                    continue


            if whichone.lower() == "downloads":
                if not datasets:
                    console.print(Panel("[magenta] No downloaded datasets found [/magenta]", border_style="bold red", box=box.DOUBLE))
                    
            
                table = Table(box=box.DOUBLE_EDGE,
                            border_style="magenta",
                            header_style="bold magenta",
                            show_lines=True
                            )
                table.add_column("【 SN 】", style="pink1", justify="center")
                table.add_column("【 DATASET 】", style="white")


                for i, ds in enumerate(datasets, 1):
                    table.add_row(f"#{i}",ds)

                console.print(table)

                while True:
                    ask = Prompt.ask("\n[magenta]Enter the SN you want to DELETE: [/magenta]")
                    try:
                        index = [int(x.strip()) for x in ask.split(",")]

                        if any(i<1 or i>len(datasets) for i in index):
                            raise ValueError
                        break
                    except:
                        console.print(Panel("[magenta] Invalid Input [/magenta]", border_style="bold red", box=box.DOUBLE))
                
                for i in index:
                    dataset_folder = datasets[i - 1]
                    shutil.rmtree(f"Downloads/{dataset_folder}")
                    console.print(Panel(f"[magenta] Removed Downloads/{dataset_folder} [/magenta]", border_style="bold red", box=box.DOUBLE))
                
                datasets = get_download_files()
            
            elif whichone.lower() == "cleaned":
                if not cleaned:
                    console.print(Panel("[magenta] No downloaded datasets found [/magenta]", border_style="bold red", box=box.DOUBLE))
                    
            
                table = Table(box=box.DOUBLE_EDGE,
                            border_style="magenta",
                            header_style="bold magenta",
                            show_lines=True
                            )
                table.add_column("【 SN 】", style="pink1", justify="center")
                table.add_column("【 DATASET 】", style="white")


                for i, ds in enumerate(cleaned, 1):
                    table.add_row(f"#{i}",ds)

                console.print(table)

                while True:
                    ask = Prompt.ask("\n[magenta]Enter the SN you want to DELETE: [/magenta]")
                    try:
                        index = [int(x.strip()) for x in ask.split(",")]

                        if any(i<1 or i>len(cleaned) for i in index):
                            raise ValueError
                        break
                    except:
                        console.print(Panel("[magenta] Invalid Input [/magenta]", border_style="bold red", box=box.DOUBLE))
                
                for i in index:
                    dataset_folder = cleaned[i - 1]
                    shutil.rmtree(f"Cleaned/{dataset_folder}")
                    console.print(Panel(f"[magenta] Removed Cleaned/{dataset_folder} [/magenta]", border_style="bold red", box=box.DOUBLE))
                
                cleaned = get_cleaned_files()
                
            while True:
                    stop_question = Prompt.ask("\n[magenta]Do you want to Clear Downloads or Cleaned Datasets AGAIN(Yes/No): [/magenta]")

                    if stop_question.lower() not in ["yes", "no"]:
                        console.print(Panel("[magenta] Invalid Input [/magenta]", border_style="bold red", box=box.DOUBLE))
                        continue
                    
                    if stop_question.lower() == "yes":
                        stop = False
                        break
                    
                    elif stop_question.lower() == "no":
                        stop = True
                        break
    
        elif question.lower() == "no":
            return


def clean_files(filepath):
    with console.status(f"[magenta]Cleaning Up {filepath}...[/magenta]", spinner="aesthetic"):

        try:
            if filepath.endswith(".csv"):
                df = pd.read_csv(filepath)
            elif filepath.endswith(".json"):
                df = pd.read_json(filepath)
            elif filepath.endswith(".xlsx"):
                df = pd.read_excel(filepath)
            elif filepath.endswith(".parquet"):
                df = pd.read_parquet(filepath)

            original_shape = df.shape

            df = df.drop_duplicates() ##removes duplicates

            df = df.dropna(axis=1, how="all") ##drops colums that are all empty

            df = df.dropna(axis=0, how="all") ##drops rows that are all empty

            for col in df.columns: ##fills remaining missing values 
                if df[col].dtype in ["float64", "int64"]:
                    df[col] = df[col].fillna(df[col].median())
                else:
                    df[col] = df[col].fillna("Unknown")
            
            for col in df.columns:
                if df[col].dtype == "object":
                    df[col] = df[col].str.strip()
            
            
            cleaned_path = filepath.replace("Downloads", "Cleaned") # save cleaned file
            os.makedirs(os.path.dirname(cleaned_path), exist_ok=True)

            if filepath.endswith(".csv"):
                df.to_csv(cleaned_path, index=False)

            elif filepath.endswith(".json"):
                df.to_json(cleaned_path, orient="records", indent=2)

            elif filepath.endswith(".xlsx"):
                df.to_excel(cleaned_path, index=False)

            elif filepath.endswith(".parquet"):
                df.to_parquet(cleaned_path, index=False)

            console.print(Panel(f"[magenta]SAVED CLEAN DATASET TO {cleaned_path} \n Cleaned from {original_shape} to {df.shape}.\nDuplicates + Empty Space Removed: {original_shape[0] - df.shape[0]} [/magenta]", border_style="bold magenta", box=box.DOUBLE))

            

        except Exception as e:
            console.print(Panel(f"[magenta]{str(e)}[/magenta]", border_style="bold red", box=box.DOUBLE_EDGE))
            return
        
