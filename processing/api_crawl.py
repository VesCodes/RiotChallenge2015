import os
import sys
import json
import requests
from time import sleep

upgradingItems = {3003: 3040, 3004: 3042, 3710: 3930, 3718: 3931, 3722: 3932, 3726: 3933} # upgradING : upgradED

def getBuild(player, timestamp, itemTable):
	build = []
	if player in itemTable:
		for item, itemData in itemTable[player].iteritems():
			for time in itemData['purchased']:
				if time < timestamp:
					build.append(item)

			for undoEvent in itemData['undo']:
				if 'undo_purchased' in undoEvent:
					if undoEvent['undo_purchased'] < timestamp:
						if item in build:
							build.remove(item)
				elif 'undo_sold' in undoEvent:
					if undoEvent['undo_sold'] < timestamp:
						build.append(item)

			for time in itemData['sold']:
				if time < timestamp:
					if item in build: # if for cases of spawn items
						build.remove(item)

			for time in itemData['destroyed']:
				if time < timestamp:
					if item in build:
						# SPECIAL UPGRADING ITEMS CASE
						if item in upgradingItems:
							build.append(upgradingItems[item])
						# // SPECIAL UPGRADING ITEMS CASES
						build.remove(item)
	return build

if __name__ == '__main__':
	API_KEY = '<snip>'
	region = sys.argv[1].lower()

	with open(os.path.join('match_ids', region.upper() + '.json')) as x:
		matchList = json.load(x)

	if not os.path.exists(os.path.join('dump', region)):
		os.makedirs(os.path.join('dump', region))

	i = 0
	while i < len(matchList):
		matchId = matchList[i]
		apiReq = requests.get('https://{}.api.pvp.net/api/lol/{}/v2.2/match/{}?includeTimeline=true&api_key={}'.format(region, region, matchId, API_KEY))

		if apiReq.status_code == 200:
			print matchId,
			jsonResp = apiReq.json()

			matchDuration = jsonResp['matchDuration']
			itemTable = {}
			killTable = []
			playerTable = {}
			banTable = []

			""" SCRAPE TIMELINE DATA TO POPULATE ITEM & KILL TABLES """
			for frame in jsonResp['timeline']['frames']:
				if 'events' in frame:
					for event in frame['events']:
						if 'ITEM' in event['eventType'] and 'ITEM_UNDO' not in event['eventType']:

							player = event['participantId']
							item = event['itemId']

							if player != 0: # avoid the mysterious 0th player
								if player not in itemTable:
									itemTable[player] = {}
								if event['itemId'] not in itemTable[player]:
									itemTable[player][item] = {'purchased': [], 'sold': [], 'destroyed': [], 'undo': []}

								if 'ITEM_PURCHASED' in event['eventType']:
									itemTable[player][item]['purchased'].append(event['timestamp'])

								elif 'ITEM_SOLD' in event['eventType']:
									itemTable[player][item]['sold'].append(event['timestamp'])

								elif 'ITEM_DESTROYED' in event['eventType']:
									itemTable[player][item]['destroyed'].append(event['timestamp'])
						
						if 'ITEM_UNDO' in event['eventType']:
							player = event['participantId']
							
							# undo purchase:
							if event['itemBefore'] != 0:
								if event['itemBefore'] in upgradingItems:
									itemTable[player][event['itemBefore']] = {'purchased': [], 'sold': [], 'destroyed': [], 'undo': []}
								itemTable[player][event['itemBefore']]['undo'].append({'undo_purchased': event['timestamp']})

							# undo sale:
							else:
								itemTable[player][event['itemAfter']]['undo'].append({'undo_sold': event['timestamp']})

						if 'CHAMPION_KILL' in event['eventType']:
							killEvent = { 'killer': {}, 'victim': {}, 'assistants': {}, 'timestamp': event['timestamp'] }
							
							if event['killerId'] != 0: # avoid the mysterious 0th player
								killEvent['killer'] = {event['killerId']: getBuild(event['killerId'], event['timestamp'], itemTable)}
							killEvent['victim'] = {event['victimId']: getBuild(event['victimId'], event['timestamp'], itemTable)}
							if 'assistingParticipantIds' in event:
								for assistant in event['assistingParticipantIds']:
									killEvent['assistants'][assistant] = getBuild(assistant, event['timestamp'], itemTable)
							
							killTable.append(killEvent)

			""" SCRAPE OTHER DATA TO POPULATE PLAYER & BAN TABLES """
			for player in jsonResp['participants']:
				build = [
					player['stats']['item0'], player['stats']['item1'],
					player['stats']['item2'], player['stats']['item3'],
					player['stats']['item4'], player['stats']['item5'],
					player['stats']['item6']
				]

				playerTable[player['participantId']] = {
					'championId': player['championId'],
					'highestAchievedSeasonTier': player['highestAchievedSeasonTier'],
					'role': player['timeline']['role'], 'lane': player['timeline']['lane'],
					'winner': player['stats']['winner'], 'minionsKilled': player['stats']['minionsKilled'],
					'kills': player['stats']['kills'], 
					'deaths': player['stats']['deaths'], 
					'assists': player['stats']['assists'],
					'build': build,
					'creepsPerMinDeltas': player['timeline']['creepsPerMinDeltas'],
					'goldPerMinDeltas': player['timeline']['goldPerMinDeltas']
				}

			for team in jsonResp['teams']:
				if 'bans' in team:
					for ban in team['bans']:
						banTable.append(ban['championId'])

			with open(os.path.join('dump', region, str(matchId) + '.txt'), 'w') as dump:
				dump.writelines([str(itemTable), '\n', str(killTable), '\n', str(playerTable), '\n', str(banTable), '\n', str(matchDuration)])

			print 'done'
			i += 1


		elif apiReq.status_code == 429:
			if 'Retry-After' in apiReq.headers:
				print 'ERROR: api key limit, retrying after {} seconds'.format(apiReq.headers['Retry-After'])
				sleep(int(apiReq.headers['Retry-After']))
			else:
				print 'ERROR: api overloaded, retrying after 5 seconds'
				sleep(5)

		else:
			print 'ERROR: it all went haywire ({}), retrying after 5 seconds'.format(apiReq.status_code)