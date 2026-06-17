import requests

# Query the Northstar Master Server
url = "https://servers.northstar.tf"
response = requests.get(url)

if response.status_code == 200:
    servers = response.json()
    
    # Print the name and player count of the first 5 public servers
    for server in servers[:5]:
        print(f"Server: {server['name']}")
        print(f"Map: {server['map']}")
        print(f"Players: {server['playerCount']}/{server['maxPlayers']}\n")
else:
    print(f"Failed to fetch data: {response.status_code}")
