from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.concurrency import run_in_threadpool
from fastapi_utils.tasks import repeat_every
from scout_apm.api import Config
from scout_apm.async_.starlette import ScoutMiddleware
from starlette.responses import FileResponse
import main
import models
import uvicorn
import uvloop
import asyncio
import json
import logging
import aiofiles
  
description = """
The Skyblock Tools api tries to put all information a hypixel dev using the api would need at their fingertips
## Items
Provides an interface to **see all data about all items, data for a specific item or specific data generally.**
Create an issue on github (https://github.com/QuintBrit/Skyblock-Tools/issues) if you need help or run into an error!
"""

tags_metadata = [
  {
    "name": "items",
    "description": "Operations dealing with ✧･ﾟindividual items✧･ﾟ"
  },
  {
    "name": "constants",
    "description": "Constant lists of things, such as what items are auctionable."
  },
  {
    "name": "simplified",
    "description": "Simplifying complex endpoints for dev use"
  },
  {
    "name": "flippers",
    "description": "Provides data for flipping"
  }
]

logging.basicConfig(filename='latest.log', filemode='w+', format='%(asctime)s: [%(levelname)s] %(message)s', datefmt='%d-%b-%y %H:%M:%S')

Config.set(
  name="Skyblock Tools - API"
)

app = FastAPI(
  title="Skyblock Tools",
  description=description,
  version="1.0.1",
  openapi_tags=tags_metadata,
  license_info={
    "name": "GNU General Public License v3.0",
    "url": "https://choosealicense.com/licenses/gpl-3.0/",
  },
)

app.add_middleware(ScoutMiddleware)
favicon_path = 'favicon.ico'
  
@app.get("/", include_in_schema=False)
async def home():
  return RedirectResponse("/docs")


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)

  
@app.get("/items/items/", tags=["items"], response_model=models.Items)
async def items() -> models.Items:
  return db

  
@app.get("/items/item/{item}/", tags=["items"], response_model=models.Item)
async def item(item: str) -> models.Item:
  return db[item]

  
@app.get("/items/item/{item}/name/", tags=["items"], response_model=models.Name)
async def name(item: str) -> models.Name:
  return models.Name(id=item,
                     name=db[item]["name"])

  
@app.get("/items/item/{item}/recipe/", tags=["items"], response_model=models.Recipe)
async def recipe(item: str) -> models.Recipe:
  if db[item]["craftable"] or db[item]["forgable"]:
    return models.Recipe(recipe=db[item]["recipe"],
                         ingredients=db[item]["ingredients"])
  else:
    return {"craftable": False, "forgable": False}

  
@app.get("/items/item/{item}/lowest_bin/", tags=["items"], response_model=models.Bins)
async def lowest_bin(item: str) -> models.Bins:
  if db[item].get("auctionable") == True:
    return models.Bins(lowest=db[item]["lowest_bin"],
                       second_lowest=db[item]["second_lowest_bin"])
  else:
    return {"auctionable": False}

    
@app.get("/items/item/{item}/auctions/", tags=["items"], response_model=models.Auctions)
async def item_auctions(item: str):
  auctions = await main.get_auctions()
  auctions = [d for d in auctions if d["id"] == item]
  return auctions

  
@app.get("/items/item/{item}/bazaar/", tags=["items"], response_model=models.BazaarItem)
async def bazaar(item: str):
  if db[item].get("bazaarable") == True:
    return models.BazaarItem(buy=db[item]["bazaar_buy_price"],
                             sell=db[item]["bazaar_sell_price"],
                             profit=db[item]["bazaar_profit"],
                             percentage_profit=db[item]["bazaar_percentage_profit"])
  else:
    return {"bazaarable": False}

  
@app.get("/items/item/{item}/price/", tags=["items"], response_model=models.Price)
async def price(item: str):
  if db[item].get("bazaarable") == True:
    return models.Price(buy=db[item]["bazaar_buy_price"], 
                        sell=db[item]["bazaar_sell_price"], 
                        profit=db[item]["bazaar_profit"], 
                        percentage_profit=db[item]["bazaar_percentage_profit"])
    
  elif db[item].get("auctionable") == True:
    return models.Price(buy=db[item]["lowest_bin"], 
                        sell=db[item]["second_lowest_bin"], 
                        profit=db[item]["bin_flip_profit"], 
                        percentage_profit=db[item]["bin_flip_percentage_profit"])
    
  elif db[item].get("npc_salable") == True:
    return models.Price(sell=db[item]["npc_sell_price"])
    
  else:
    return {"unsellable": True}

    
@app.get("/items/item/{item}/forge/", tags=["items"], response_model=models.ForgeItem)
async def forge(item: str):
  if db[item].get("forgable") == True:
    return models.ForgeItem(cost=db[item]["forge_cost"],
                            profit=db[item]["forge_profit"],
                            duration=db[item]["duration"],
                            pretty_duration=db[item]["pretty_duration"],
                            profit_per_hour=db[item]["forge_profit_per_hour"],
                            percentage_profit=db[item]["forge_percentage_profit"],
                            recipe=db[item]["recipe"],
                            ingredients=db[item]["ingredients"])
  else:
    return {"forgable": False}

    
@app.get("/constants/bazaarables/", tags=["constants"], response_model=list)
async def bazaarables():
  bazaarables = [item for item in db if db[item]["bazaarable"]]
  return bazaarables

  
@app.get("/constants/auctionables/", tags=["constants"], response_model=list)
async def auctionables():
  auctionables = [item for item in db if db[item]["auctionable"]]
  return auctionables

  
@app.get("/constants/craftables/", tags=["constants"], response_model=list)
async def craftables():
  craftables = [item for item in db if db[item]["craftable"]]
  return craftables

  
@app.get("/constants/forgables/", tags=["constants"], response_model=list)
async def forgables():
  forgables = [item for item in db if db[item]["forgable"]]
  return forgables

  
@app.get("/simplified/auctions", tags=["simplified"], response_model=models.Auctions)
async def auctions(page: int = 0):
  auctions = await main.get_auctions()
  auctions = list(main.chunks(auctions, 5000))
  return auctions[page]


@app.get("/flippers/bazaar", tags=["flippers"], response_model=list)
async def bazaar_flipper():
  return  main.bazaar_flipper()


@app.get("/flippers/bazaar/html", tags=["flippers"], response_model=str)
async def bazaar_flipper_html():
  return main.build_table(main.bazaar_flipper()[0], main.bazaar_flipper()[1], "./templates/bazaar_flipper_data.html")


@app.get("/flippers/craft", tags=["flippers"], response_model=list)
async def craft_flipper():
  return main.craft_flipper()


@app.get("/flippers/craft/html", tags=["flippers"], response_model=str)
async def craft_flipper_html():
  return main.build_table(main.craft_flipper()[0], main.craft_flipper()[1], "./templates/craft_flipper_data.html")


@app.get("/flippers/forge", tags=["flippers"], response_model=list)
async def forge_flipper():
  return main.forge_flipper()


@app.get("/flippers/forge/html", tags=["flippers"], response_model=str)
async def forge_flipper_html():
  return main.build_table(main.forge_flipper()[0], main.forge_flipper()[1], "./templates/forge_flipper_data.html")

  
@app.on_event("startup")
async def load_db():
  global db
  async with aiofiles.open("database.json", "r") as database:
    database = await database.read()
    db = json.loads(database)

    
@app.on_event("startup")
@repeat_every(seconds=30, logger=logging.Logger)
async def dynamic_database_updater_task():
  global db
  print("dynamic")
  db = await run_in_threadpool(lambda: main.dynamic_database_updater(db, main.names))

  
@app.on_event("startup")
@repeat_every(seconds=60*10, wait_first=True, logger=logging.Logger)
async def static_database_updater_task():
  global db
  print("static")
  db = await run_in_threadpool(lambda: main.static_database_updater(db, main.names))

uvloop.install()

if __name__ == "__main__":
  uvicorn.run("app:app", host='0.0.0.0', port=8080, workers=4)