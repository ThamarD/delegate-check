#!/usr/bin/env python3

# Imports
from config import *
import asyncio
import aiohttp
import aioboto3
from datetime import datetime
from datetime import timedelta
from shutil import copy2

# Functions
async def notifications(msg):
    async with aioboto3.client("sns",
        aws_access_key_id=aws_key_id,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region) as client:
        await client.publish(
            PhoneNumber=phone,
            Message=msg)

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

async def v2(network,delegate):

    del_info = await api_get(nodes[network] + '/delegates/' + delegate)
    if del_info == 'error' or del_info == 'timeout':
        return

    del_blocks = await api_get(nodes[network] + '/delegates/' + delegate + '/blocks')
    if del_blocks == 'error' or del_blocks == 'timeout':
        return

    net_height = await api_get(nodes[network] + '/node/status')
    if net_height == 'error' or net_height == 'timeout':
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
    elif net_round <= cur_round + 1:
        state = 'healthy'
    else:
        state = 'missing'
        if sns_enabled == 'yes' and net_round == cur_round + 2:
            await notifications(network + ' delegate ' + delegate + '  missed a block!')

    missed = 0
    forged = del_blocks['meta']['count']

    if net_round > cur_round + 1:
        missed += net_round - cur_round - 1

    for i in range(0,forged - 2):
        cur_round = get_round(del_blocks['data'][i]['height'],network)
        prev_round = get_round(del_blocks['data'][i + 1]['height'],network)
        if prev_round < cur_round - 1:
            missed += cur_round - prev_round - 1

    prod = str(round(forged*100/(forged + missed)))

    print('Network: ' + network + ' | Delegate: ' + delegate + ' | Rank: ' + rank + ' | Forging: ' + forging + ' | Last Block: ' + delta + ' min ago | State: ' + state + ' | Yield: ' + prod + '%')
    csv.write(network + ',' + delegate + ',' + rank + ',' + forging + ',' + delta + ' min ago,' + state + '\n')

async def v1(network,delegate):
    result = await api_get(nodes[network] + '/delegates/get?username=' + delegate)
    if result == 'error' or result == 'timeout':
        return
    rank = str(result['delegate']['rate'])
    if result['delegate']['rate'] <= db[network][0]:
        forging = 'yes'
    else:
        forging = 'no'
    pubkey = str(result['delegate']['publicKey'])
    result = await api_get(nodes[network] + '/blocks?generatorPublicKey=' + pubkey + '&limit=1')
    timestamp = result['blocks'][0]['timestamp']
    utc_remote = datetime(epoch[network][0], epoch[network][1], epoch[network][2], epoch[network][3], epoch[network][4], epoch[network][5]) + timedelta(seconds=timestamp)
    utc_local = datetime.utcnow().replace(microsecond=0)
    delta = int((utc_local - utc_remote).total_seconds())
    lb_delta = str(int(round(delta/60)))
    tworounds = 2 * db[network][0] * db[network][1]
    if forging == 'no':
        state = 'out'
    elif delta > tworounds:
        state = 'missing'
        if sns_enabled == 'yes' and delta < 90 + tworounds:
            await notifications(network + ' delegate ' + delegate + ' missed a block!')
            print('Sent SMS!')
    else:
        state = 'healthy'
    print('Network: ' + network + ' | Delegate: ' + delegate + ' | Rank: ' + rank + ' | Forging: ' + forging + ' | Last Block: ' + lb_delta + ' min ago | State: ' + state)
    csv.write(network + ',' + delegate + ',' + rank + ',' + forging + ',' + lb_delta + ' min ago,' + state + '\n')

# Build Tasks List
tasks = []
function_map = {
    'v1':v1,
    'v2':v2
}
for network in delegates:
    for delegate in delegates[network]:
        tasks.append(asyncio.ensure_future(function_map[db[network][2]](network,delegate)))

# Initiate CSV
csv = open('state.csv','w+')
csv.write("Network,Delegate,Rank,Forging,Last Block,State\n")

# Async Loop
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(asyncio.wait(tasks))
finally:
    loop.close()

# Close and Copy CSV to web/
csv.close()
copy2('state.csv','web/')
