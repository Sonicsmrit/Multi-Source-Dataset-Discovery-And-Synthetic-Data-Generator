from huggingface_hub import HfApi
import asyncio, os, json, time
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime, timezone
from rich.prompt import Prompt
from rich.console import Console
from rich.panel import Panel
from rich import box
import pyfiglet


load_dotenv()
os.environ['KAGGLE_USERNAME'] = os.environ.get("KAGGLE_USERNAME")
os.environ['KAGGLE_KEY'] = os.environ.get("KAGGLE_KEY")

from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()
hf_api_key = os.environ.get("HF_TOKEN")

hugging_api = HfApi()

ai = Groq(
    api_key= os.environ.get("GROQ_API_KEY")
)

console = Console()


class search():

    def startup_screen(self):
        ascii_art = pyfiglet.figlet_format("DATASET", font="big")
        ascii_art2 = pyfiglet.figlet_format("DISCOVERY", font="big")
        
        console.print(f"[bold magenta]{ascii_art}[/bold magenta]", justify="center")
        console.print(f"[bold pink1]{ascii_art2}[/bold pink1]", justify="center")

        console.print(Panel(
            "[magenta]・ Multi-Source Dataset Discovery & Synthetic Data Generator ・[/magenta]",
            border_style="magenta",
            box=box.DOUBLE
        ))

        time.sleep(1.5)
        


    def input_datasets(self):

        self.startup_screen()

        dataset = Prompt.ask("\n [bold magenta]🔍︎ Search Datasets: [/bold magenta]")
        return dataset


    def search_huggingface(self, query):
        datasets = hugging_api.list_datasets(
            search=f"{query}",
            sort= "downloads",
            direction=-1,
            limit=100
        )

        return list(datasets)
    
    def search_kaggle(self, query):

        all_results = []
        for page in range(1, 6):
            datasets = api.dataset_list(search=f"{query}", sort_by="hottest", page=page)

            all_results.extend(datasets)
    
        return all_results
        

    async def search_datasets(self):
        dataset = self.input_datasets()

        with console.status("[magenta]🌐 Searching Datasets...[/magenta]", spinner="aesthetic"):

            huggingface_results, kaggle_results = await asyncio.gather(asyncio.to_thread(self.search_huggingface, query=f"{dataset}"), asyncio.to_thread(self.search_kaggle, query=f"{dataset}"))

        return huggingface_results, kaggle_results, dataset





def scoring():

    json_data_for_ai = []
    score_all = []
    final_score = []


    hugging_data, kaggle_data, search_query = asyncio.run(search().search_datasets())

    with console.status("[magenta]Scoring Datasets...[/magenta]", spinner="aesthetic"):
        for hugs in hugging_data:
            json_data_for_ai.append({
                "from": "hugging face",
                "name": hugs.id,
                "downloads": hugs.downloads,
            })
        
        for kag in kaggle_data:
            json_data_for_ai.append(
                {
                    "from": "kaggle",
                    "name": kag.ref,
                    "downloads": kag.download_count,
                }
            )

        formats =  '[{{"name": "owner/dataset", "score": 7.5, "from": "kaggle/HuggingFace"}}, ...]'

        chat_completion = ai.chat.completions.create(
            messages=[{
                "role":"user",

                "content": f"""
                    You are a dataset quality and relevance evaluator. Rate the following datasets out of 10.

                    Consider:
                    - How relevant the dataset is to the search query: "{search_query}" (most important)
                    - How many downloads and likes it has (popularity = quality signal)
                    - Name clarity (does the name tell you what the dataset contains)
                    - Source credibility: HuggingFace likes and Kaggle votes are both popularity signals,
                    but Kaggle votes tend to be inflated so weight them slightly less than HuggingFace likes

                    Return ONLY a JSON array of objects with "name", "score" and "from" fields. Nothing else. No explanation.

                    Example format:
                    {formats}

                    Search Query: "{search_query}"

                    Datasets:
                    {json.dumps(json_data_for_ai, indent=2, default=str)}

                    """
            }
                
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            max_tokens=8192
        )


        raw_ai_output = chat_completion.choices[0].message.content
        try:
            ai_socres = json.loads(raw_ai_output)

        except json.JSONDecodeError:
            ai_socres = []

        score_downloads = lambda d: 10 if d >= 100000 else 8 if d >= 10000 else 6 if d >= 1000 else 4 if d >= 100 else 2 if d >= 10 else 1

        score_likes = lambda l: 10 if l >= 1000 else 8 if l >= 100 else 6 if l >= 50 else 4 if l >= 10 else 2 if l >= 1 else 1

        score_recency = lambda d: 10 if d <= 30 else 8 if d <= 90 else 6 if d <= 180 else 4 if d <= 365 else 2 if d <= 730 else 1

        size_map_hf = {"n<1K": 1, "1K<n<10K": 3, "10K<n<100K": 5, "100K<n<1M": 7, "1M<n<10M": 9, "10M<n<100M": 10, "100M<n<1B": 10}
        score_size_hf = lambda s: size_map_hf.get(s, 1)

        score_size_kaggle = lambda b: 10 if b >= 1_000_000_000 else 8 if b >= 100_000_000 else 6 if b >= 10_000_000 else 4 if b >= 1_000_000 else 2 if b >= 100_000 else 1


        final_score_calc = lambda downloads, likes, recency, size, ai: (downloads * 0.3 + size * 0.3 + recency * 0.25 + likes * 0.15 if ai == 0 else downloads * 0.25 + ai * 0.3 + size * 0.25 + recency * 0.1 + likes * 0.1)

        for hugs in hugging_data:
            score_all.append(
                {   
                    "from": "Hugging Face",
                    "name": hugs.id,
                    "ai score": next((float(score["score"]) for score in ai_socres if score["name"] == hugs.id), 0),
                    "downloads_score": score_downloads(hugs.downloads),
                    "likes_score": score_likes(hugs.likes),
                    "recent_score": score_recency((datetime.now(timezone.utc) - hugs.last_modified).days),
                    "size_socre": next((score_size_hf(t) for t in hugs.tags if t.startswith("size_categories:")), 1)

                }
            )

        for kag in kaggle_data:
            score_all.append(
                {
                    "from": "Kaggle",
                    "name": kag.ref,
                    "ai score": next((float(score["score"]) for score in ai_socres if score["name"] == kag.ref), 0),
                    "downloads_score": score_downloads(kag.download_count),
                    "likes_score": score_likes(kag.vote_count),
                    "recent_score": score_recency((datetime.now(timezone.utc) - kag.last_updated.replace(tzinfo=timezone.utc)).days),
                    "size_socre": score_size_kaggle(kag.total_bytes)
                }
            )

        for score in score_all:
            final_score.append(
                {
                    "name": score["name"],
                    "score": final_score_calc(score["downloads_score"], score["likes_score"], score["recent_score"], score["size_socre"], score["ai score"]),
                    "from": score["from"]
                }
                )
            
        
        score_result = sorted(final_score, key=lambda x: x["score"], reverse=True)

    return score_result, search_query
