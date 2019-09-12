#!/usr/bin/env python3

# Imports
from config import *
import os
import json
import asyncio
import aiohttp
import aioboto3
from datetime import datetime
from datetime import timedelta
from shutil import copy2

# Functions
async def notifications(msg):

    async with aioboto3.client('sns',
        aws_access_key_id=aws_key_id,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region) as client:
        await client.publish(PhoneNumber=phone,Message=msg)

async def api_get(url):

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as resp:
                return await resp.json()

    except asyncio.TimeoutError:
        return 'timeout'

    except:
        return 'error'

def get_round(height,network):

    data = divmod(height,db[network][0])

    if data[1] == 0:
        result = data[0]
    else:
        result = data[0] + 1

    return result

async def del_check(network,delegate):

    del_info = await api_get(nodes[network] + '/delegates/' + delegate)
    if del_info == 'error' or del_info == 'timeout':
        return

    del_blocks = await api_get(nodes[network] + '/delegates/' + delegate + '/blocks')
    if del_blocks == 'error' or del_blocks == 'timeout':
        return

    net_height = await api_get(nodes[network] + '/node/status')
    if net_height == 'error' or net_height == 'timeout':
        return

    total_rounds = del_blocks['meta']['count']

    if total_rounds < 2:
        return

    if del_info['data']['rank'] <= db[network][0]:
        forging = 'yes'
    else:
        forging = 'no'

    rank = str(del_info['data']['rank'])
    timestamp = del_info['data']['blocks']['last']['timestamp']['unix']
    utc_remote = datetime.utcfromtimestamp(timestamp)
    utc_local = datetime.utcnow().replace(microsecond=0)
    delta = str(round(int((utc_local - utc_remote).total_seconds())/60))
    net_round = get_round(net_height['data']['now'],network)
    cur_round = get_round(del_blocks['data'][0]['height'],network)

    if forging == 'no':
        state = 'out'
        if sns_enabled == 'yes' and savedState[network][delegate] == 'clean':
            await notifications(network + ' delegate ' + delegate + '  not forging!')
            savedState[network][delegate] = 'dirty'
    elif net_round <= cur_round + 1:
        state = 'healthy'
        savedState[network][delegate] = 'clean'
    else:
        state = 'missing'
        if sns_enabled == 'yes' and savedState[network][delegate] == 'clean':
            await notifications(network + ' delegate ' + delegate + '  missed a block!')
            savedState[network][delegate] = 'dirty'

    if 'statistics' not in del_info['data']:
        return

    prod = str(round(del_info['data']['statistics']['day']['rounds']['productivity'] * 100))

    print('Network: ' + network + ' | Delegate: ' + delegate + ' | Rank: ' + rank + ' | Forging: ' + forging + ' | Last Block: ' + delta + ' min ago | State: ' + state + ' | Yield: ' + prod + '%')
    csv.write(network + ',' + delegate + ',' + rank + ',' + forging + ',' + delta + ' min ago,' + state + ',' + prod + '%\n')

# Initialize Lists
tasks = []
savedState = {}

# Initialize CSV
csv = open('state.csv','w+')
csv.write('Network,Delegate,Rank,Forging,Last Block,State,Yield\n')

# Load JSON state file
if os.path.exists('state.json'):
    with open('state.json', 'r') as file:
      savedState = json.load(file)

# Fill in the Lists
for network in delegates:
    if network not in savedState:
        savedState[network] = {}
    for delegate in delegates[network]:
        if delegate not in savedState[network]:
            savedState[network][delegate] = 'clean'
        tasks.append(asyncio.ensure_future(del_check(network,delegate)))

# Async Loop
loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(asyncio.wait(tasks))

finally:
    loop.close()

# Cleanup
csv.close()
copy2('state.csv','web/')

with open('state.json', 'w+') as file:
  json.dump(savedState, file)
