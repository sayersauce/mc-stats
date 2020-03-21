# https://github.com/sayersauce
# A player leave / join statistics recording program.
# Sends graphs and information by discord webhook.

import requests
import json
import os
import time
import csv
import datetime
import matplotlib.pyplot as plt
from mcstatus import MinecraftServer


FILE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/"


def load_config():
    # Loads configuration from mc_stats.json.
    with open(FILE_PATH + "mc_stats.json") as config_file:
        return json.load(config_file)


def query_minecraft_server(host):
    # Queries Minecraft Server for information, requires `enable-query=true` in `server.properties`.
    server = MinecraftServer.lookup(host)
    return server.query()


def send_discord_webhook(url, image, query):
    embed = {
        "title" : "Player Statistics",
        "color" : 15859772,
        "fields" : [
            {
                "name" : "Player Count",
                "value" : query.players.online
            },
            {
                "name" : "Player List",
                "value" : "\n".join(query.players.names)
            }
        ]
    }

    values = {
        "embeds" : [embed]
    }

    requests.post(url, data=json.dumps(values), headers={"Content-Type" : "application/json"})

    if image:
        requests.post(url, files={"upload_file" : open(FILE_PATH + image, "rb")})


def load_csv(csv_file):
    # Load rows from a csv file.
    rows = []

    with open(FILE_PATH + csv_file, "r") as f:
        csv_reader = csv.DictReader(f)
        line_count = 0
        for row in csv_reader:
            rows.append(row)
            line_count += 1
    
    return rows
    

def add_csv_line(csv_file, day, hour, playercount):
    # Appends row to csv file.
    # First checks if csv file has been made.
    if not os.path.exists(FILE_PATH + csv_file):
        with open(FILE_PATH + csv_file, "w+") as f:
            f.write("day,hour,count")
    with open(FILE_PATH + csv_file, "a") as f:
        f.write(f"\n{day},{hour},{playercount}")


def create_graph(rows):
    rows = rows[-24:]
    x = [i["hour"] for i in rows]
    y = [int(i["count"]) for i in rows]
    plt.plot(x, y, "b")
    plt.xlabel("Time")
    plt.ylabel("Players")
    plt.savefig("plot.png")


if __name__ == "__main__":
    config = load_config()

    previous_query = query_minecraft_server(config["host"])
    send_discord_webhook(config["webhook-url"], "", previous_query)

    # Constant loop of gaining statistics. Every 10 minutes.
    while True:

        for i in range(5):
            # Send webhook without graph.
            query = query_minecraft_server(config["host"])
            if query.players.online != previous_query.players.online:
                send_discord_webhook(config["webhook-url"], "", query)
            previous_query = query
            time.sleep(600)

        # Send webhook with playercount graph. Save playercount data.
        query = query_minecraft_server(config["host"])
        date = datetime.datetime.now()
        add_csv_line(config["csv-file"], f"{date.day}/{date.month}/{date.year}", date.hour, query.players.online)
        create_graph(load_csv(config["csv-file"]))
        send_discord_webhook(config["webhook-url"], "plot.png", query)
        time.sleep(600)

