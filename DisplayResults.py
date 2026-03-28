import json, time, os, sys, re
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"


from CLI import *
from datasets import load_dataset
import datasets, logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import box
import pandas as pd
from huggingface_hub import snapshot_download


datasets.logging.disable_progress_bar()
datasets.logging.set_verbosity_error()

logging.getLogger("datasets").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

console = Console()

scores, query = scoring()

##Displays the dataset in a table format 
def display_result():
    top_thirty = []
    
    console.print(Panel(
        f"[bold magenta]「 QUERY 」[/bold magenta] [bold bright_cyan]{query.upper()}[/bold bright_cyan]",
        border_style= "magenta",
        subtitle= "[pink1]HERES WHAT WE FOUND[/pink1]",
    ))

    table = Table(
        box= box.DOUBLE_EDGE,
        border_style="magenta",
        header_style="bold magenta",
        show_lines=True
    )

    table.add_column("【 SN 】", style="pink1", justify="center")
    table.add_column("【 NAME 】", style="white")
    table.add_column("【 SCORE 】", style="bold yellow", justify="center")
    table.add_column("【 SOURCE 】", style="cyan", justify="center")
    table.add_column("【 SIZE 】", style="cyan", justify="center")

    for i, dataset in enumerate(scores[:30], 1):

        source = "🤗 HF" if dataset["from"] == "Hugging Face" else "📊 Kaggle"

        score = dataset["score"]

        score_color = "green" if score >= 7 else "yellow" if score >= 4 else "red"
        
        table.add_row(
            f"[pink1]#{i}[/pink1]",
            dataset["name"],
            f"[{score_color}]{score:.2f}[/{score_color}]",
            source,
            str(dataset["size"])


        )
        top_thirty.append({
            "index": i,
            "name": dataset["name"],
            "source": dataset["from"],
            "size": dataset["size"]
        })

    console.print(table)
    console.print(Panel("[magenta]・・・ Search Completed・・・[/magenta]", border_style="magenta"))

    return top_thirty



##Previewing the Datasets 
def preview():

    dataset = display_result()
    skip_preview = False


    time.sleep(3)

    console.print(Panel(
        "[magenta]PREVIEW WHAT YOU LIKE OR SKIP PV BY TYPING 'skip' [/magenta]",
        border_style="magenta",
        subtitle="[pink1]Enter Like This(Enter SN For Preview: 1, 2, 3, ...)[/pink1]"
    ))

    while True:

        with console.status("[magenta]Setting Up...[/magenta]", spinner="aesthetic"):
            time.sleep(1.5)

        user_choice = Prompt.ask("\n [bold magenta]Enter SN For Preview: [/bold magenta]")

        if user_choice == "skip":
            skip_preview = True
            break
        else:
            try:
                indexes = [int(x.strip()) for x in user_choice.split(",")]
                if any(i<1 or i>len(dataset) for i in indexes):
                    raise ValueError
                
                break
                
            except:
                console.print(Panel("[magenta] Error! Invalid Input. Try Again! [/magenta]", border_style="bold red", box=box.DOUBLE))

    if not skip_preview:

        for i in indexes:
            for data in dataset:
                with console.status("[magenta]loading dataset preview...[/magenta]", spinner="aesthetic"):

                    if i == data["index"]:
                        
                        if data["source"] == "Hugging Face":

                            try:
                                dataset_hugging =  load_dataset(data["name"], split="train", streaming=True, token=hf_api_key)

                            except Exception as e:

                                error = str(e)

                                if "Config name is missing" in error:
                                    configs = re.findall(r"'(\w+)'", error)

                                    if configs:

                                        try:
                                            dataset_hugging = load_dataset(data["name"], configs[0], split="train", streaming=True, token=hf_api_key)
                                        except:
                                            console.print(Panel(f"[magenta] Cannot Preview [/magenta]", border_style="bold red", box=box.DOUBLE))
                                            break

                                else:
                                    console.print(Panel(f"[magenta] Cannot Preview: {str(e)[:100]} [/magenta]", border_style="bold red", box=box.DOUBLE))
                                    break
                            
                            try:
                                df = pd.DataFrame(list(dataset_hugging.take(10)))

                            except Exception as e:

                                console.print(Panel(f"[magenta] Cannot preview {str(e)[:100]} 【 unsupported or compressed file 】[/magenta]", border_style="bold red", box=box.DOUBLE))
                                console.print(Panel(
                                    f"[magenta] Preview not available for this dataset type.\nVisit: https://huggingface.co/datasets/{data['name']} [/magenta]",
                                    border_style="cyan",
                                    box=box.DOUBLE
                                ))

                                break


                            table = Table(
                                title = f"「 Preview 」 {data['name']} | First 10 rows of HF Dataset",
                                box = box.DOUBLE_EDGE,
                                border_style= "cyan",
                                header_style= "bold bright_cyan",
                                show_lines=True
                            )

                            for col in df.columns:
                                table.add_column(f"【{col}】", style= "white", overflow="fold")
                            
                            for _, row in df.iterrows():
                                table.add_row(*[str(val)[:50] + "..." if len(str(val)) > 50 else str(val) for val in row])
                            
                            console.print(table)

                        elif data["source"] == "Kaggle":
                            try:
                                files = api.dataset_list_files(data["name"]).files
                            except Exception as e:
                                console.print(Panel(f"[magenta] Cannot Preview: {str(e)[:100]} [/magenta]", border_style="bold red", box=box.DOUBLE))
                                break

                            table = Table(
                                title=f"「 Files 」 {data['name']}",
                                box=box.DOUBLE_EDGE,
                                border_style="cyan",
                                header_style="bold bright_cyan",
                                show_lines=True
                            )

                            table.add_column("【 FILE 】", style="white")
                            table.add_column("【 SIZE 】", style="magenta", justify="right")

                            for f in files:
                                size = f"{f.total_bytes / 1024:.1f} KB" if f.total_bytes < 1_000_000 else f"{f.total_bytes / 1_000_000:.1f} MB"
                                table.add_row(f.name, size)

                            console.print(table)
                            
                        break

    return dataset

###Downloads the datasets Kaggle downloads, HF tells the user to download it themselves 
def download_datasets():
    dataset = preview()
    skip = False

    console.print(Panel(
        "[magenta]DOWNLOAD WHAT YOU LIKE OR SKIP DOWNLOAD BY TYPING 'skip' [/magenta]",
        border_style="magenta",
        subtitle="[pink1]Enter Like This(Enter SN For Preview: 1, 2, 3, ...)[/pink1]"
    ))

    with console.status("[magenta]Setting up...[/magenta]", spinner="aesthetic"):
        time.sleep(1.5)

    while True:
        download_numbers = Prompt.ask("\n[magenta] Enter SN of Datasets You Want To Download: [/magenta]")
    
        if download_numbers.lower() == "skip":
            skip = True
            break
        else:

            try:
                numbers = [int(num.strip()) for num in download_numbers.split(",")]
                if any(i<1 or i>len(dataset) for i in numbers):
                    raise ValueError
                        
                break
                        
            except:
                console.print(Panel("[magenta] Error! Invalid Input. Try Again! [/magenta]", border_style="bold red", box=box.DOUBLE))
                continue
    
    if not skip:
        for n in numbers:
            for data in dataset:
                if n == data["index"]:
                    if data["source"] == "Hugging Face":

                        console.print(Panel(
                            f"[magenta] Visit to Download & Preview:\n https://huggingface.co/datasets/{data['name']} \n Sorry For The Inconvenience[/magenta]",
                            border_style="cyan",
                            box=box.DOUBLE
                        ))

                    elif data["source"] == "Kaggle":

                        try:
                            with console.status(f"[magenta]Downloading {data['name']}...[/magenta]", spinner="aesthetic"):
                                api.dataset_download_files(
                                    data["name"],
                                    path=f"Downloads/{data['name'].replace('/', '_')}",
                                    unzip=True,
                                    
                                )
                            console.print(Panel(
                                    f"[magenta]DOWNLOADED {data['name']} TO Downloads[/magenta]",
                                    border_style="magenta"
                                ))
                        except Exception as e:
                            console.print(Panel(f"[magenta] Download Failed: {str(e)[:100]} [/magenta]", border_style="bold red", box=box.DOUBLE))
                    
                    break





