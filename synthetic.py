import os, glob
import pandas as pd
from sdv.single_table import GaussianCopulaSynthesizer, CTGANSynthesizer, TVAESynthesizer
from sdv.metadata import SingleTableMetadata
from rich.console import Console
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
import warnings

warnings.filterwarnings("ignore")

console = Console()


def get_cleaned_files():
    if not os.path.exists("Cleaned"):
        return []
    
    return [f for f in os.listdir("Cleaned") if os.path.isdir(f"Cleaned/{f}")]


def find_tabular_files(ds_folder):
    extensions = ["*.csv", "*.json", "*.xlsx", "*.parquet"]

    files = []

    for ex in extensions:
        files.extend(glob.glob(f"Cleaned/{ds_folder}/**/{ex}", recursive=True))
    
    return files

def synthetic_data_pipeline():
    clean_ds = get_cleaned_files()

    if not clean_ds:
        return

    table = Table(box=box.DOUBLE_EDGE, border_style="magenta", header_style="bold magenta", show_lines=True)
    table.add_column("【 SN 】", style="pink1", justify="center")
    table.add_column("【 DATASET 】", style="white")

    for i, ds in enumerate(clean_ds, 1):
        table.add_row(f"#{i}", ds)

    console.print(table)

    while True:
        choice = Prompt.ask("\n[bold magenta] Enter SN of Datasets to Synthesize: [/bold magenta]")
        if choice.lower() == "skip":
            return
        try:
            index = [int(x.strip()) for x in choice.split(",")]
            if any(i < 1 or i > len(clean_ds) for i in index):
                raise ValueError
            break
        except:
            console.print(Panel("[magenta] Invalid Input [/magenta]", border_style="bold red", box=box.DOUBLE))

    while True:
        console.print(Panel(f"[magenta]Choose Synthetic Data Generation Model\n (1) GaussianCopulaSynthesizer \n (2) CTGANSynthesizer \n (3) TVAESynthesizer[/magenta]",subtitle="Press the Correlating Number of the Model", border_style="bold magenta", box=box.DOUBLE))
        try:

            model = int(Prompt.ask("\n[bold magenta]Choose While Model You want to use to Make Synthetic Data: [/bold magenta]"))

            if model not in [1,2,3]:
                raise ValueError
            
            break
        except:
            console.print(Panel("[magenta] Invalid Input [/magenta]", border_style="bold red", box=box.DOUBLE))

            continue
    
    epoche = 300

    if model in [2, 3]:

        while True:
            try:
                epochs = int(Prompt.ask("\n[bold magenta]Enter number of epochs (default 300): [/bold magenta]") or 300)

                if epochs < 1:
                    raise ValueError
                break
            except:
                console.print(Panel("[magenta] Invalid Input [/magenta]", border_style="bold red", box=box.DOUBLE))

    for i in index:
        ds_folder = clean_ds[i - 1]
        files = find_tabular_files(ds_folder)
        for f in files:
            generate_synthetic(f, model, epoche)
    

def generate_synthetic(f, model, epoche):

    try:
        dataset = "Unknown"

        if f.endswith(".csv"):
            df = pd.read_csv(f)
            dataset = "csv"

        elif f.endswith(".json"):
            df = pd.read_json(f)
            dataset = "json"
        elif f.endswith(".xlsx"):
            df = pd.read_excel(f)
            dataset = "xlsx"

        elif f.endswith(".parquet"):
            df = pd.read_parquet(f)
            dataset = "par"

        metadata = SingleTableMetadata()

        metadata.detect_from_dataframe(df)

        df = df.sample(n=min(10000, len(df)), random_state=42)
        
        if model == 1:

            synthesizer = GaussianCopulaSynthesizer(metadata=metadata)
        
        elif model == 2:
            synthesizer = CTGANSynthesizer(metadata=metadata, epochs=epoche)
        
        elif model == 3:
            synthesizer = TVAESynthesizer(metadata=metadata, epochs=epoche)

        with console.status(f"[magenta]Generating Synthetic Data for {f}...[/magenta]", spinner="aesthetic"):

            synthesizer.fit(df)

            synthetic_df = synthesizer.sample(num_rows=40_000)

            synthetic_path = f.replace("Cleaned", "Synthetic")
            os.makedirs(os.path.dirname(synthetic_path), exist_ok=True)

            if dataset == "csv":
                synthetic_df.to_csv(synthetic_path, index=False)
            elif dataset == "json":
                synthetic_df.to_json(synthetic_path)
            elif dataset == "xlsx":
                synthetic_df.to_excel(synthetic_path, index=False)
            elif dataset == "par":
                synthetic_df.to_parquet(synthetic_path)
        
        console.print(Panel(f"[magenta] Synthetic Data Saved to {synthetic_path} [/magenta]", border_style="magenta", box=box.DOUBLE))

        
    except Exception as e:
        console.print(Panel(f"[magenta] Failed: {str(e)[:100]} [/magenta]", border_style="bold red", box=box.DOUBLE))
        return


