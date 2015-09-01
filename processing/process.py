import os
import sys
import json
from glob import glob

""" WELCOME TO THE LEAGUE OF... PROCESSING. """

untrackedItems = [2003, 2004, 2009, 2010, 2052, 2054, 2047, 		# general consumables
					2137, 2138, 2139, 2140, 						# elixirs
					2043, 2044, 									# consumable wards
					3340, 3341, 3342, 3345, 3361, 3362, 3363, 3364, # trinkets
					3040, 3042, 3930, 3931, 3932, 3933] 			# upgraded items
upgradingItems = {3003: 3040, 3004: 3042, 3710: 3930, 3718: 3931, 3722: 3932, 3726: 3933} # upgradING : upgradED
brawlerItems = [3611, 3612, 3613, 3614, 3615, 3616, 3617, 3621, 3622, 3623, 3624, 3625, 3626] # see lines 185-188

# --------------------------- FIRST PROCESS LOOP --------------------------- #
def process1(matchDumpFile, champsDB, itemsDB):
	""" 
	PROCESS RAW DATA DUMP & POPULATE:
		* champsDB: stores match count on a per champion basis
		* itemsDB: stores item purchases with correlation to champions
		( to be processed for a list of top 10 champs who purchased X item )
	"""
	with open (matchDumpFile, 'r') as m:
		dumpData = m.readlines()

	itemTable = eval(dumpData[0])
	playerTable = eval(dumpData[2])

	# populate champsDB
	for playerId, playerData in playerTable.iteritems():
		if playerData['championId'] not in champsDB:
			champsDB[playerData['championId']] = 1
		else:
			champsDB[playerData['championId']] += 1

	# populate itemsDB
	for player, items in itemTable.iteritems():
		championId = playerTable[player]['championId']

		for item, events in items.iteritems():
			if item not in itemsDB:
				itemsDB[item] = {championId: 1}
			else:
				if championId not in itemsDB[item]:
					itemsDB[item][championId] = 1
				else:
					itemsDB[item][championId] += 1

def narrowTopList(itemsDB, champsDB):
	""" 
	NARROWS DOWN CHAMPION TOPLIST FOR ITEM
		* topList: stores 10 champions sorted by purchase count on a per item basis
		> purchase count is converted to % of games of X champion in which he purchased the item
	"""
	topList = {}
	for item, champs in itemsDB.iteritems():
		tempList = sorted(champs.iteritems(), key=lambda x: x[1], reverse=True)[:10]
		for champ, matchCount in tempList:
			if item not in topList:
				topList[item] = {}
			topList[item][champ] = int(100 * float(matchCount)/float(champsDB[champ]))
	return topList

def createJson(topList, jsonDir):
	if not os.path.exists(jsonDir):
		os.makedirs(jsonDir)

	for item, data in topList.iteritems():
		toPush = {'champs': data}
		if item in upgradingItems: 
			# create JSON for upgradED item, store purchase data from child 
			# (graph data for the upgradED item, on the other hand, is unique)
			with open(os.path.join(jsonDir, str(upgradingItems[item]) + '.json'), 'w') as y:
				json.dump(toPush, y)

		with open(os.path.join(jsonDir, str(item) + '.json'), 'w') as x:
			json.dump(toPush, x)

# --------------------------- SECOND PROCESS LOOP --------------------------- #
def undoFix(undoDict):
	""" 
	FORMATTING FIX FOR UNDO EVENTS IN RAW DATA DUMPS 
		* to save disk space this is done post-api crawling & dumping
		( could potentially be dropped and raw dumps reformatted, not a priority )
	"""
	undoPurchased = []
	undoSold = []
	for event in undoDict:
		if 'undo_purchased' in event:
			undoPurchased.append(event['undo_purchased'])
		elif 'undo_sold' in event:
			undoSold.append(event['undo_sold'])
	return {'undo': {'undo_purchased': undoPurchased, 'undo_sold': undoSold}}

def pointify(killTable, playerTable, playerId, start, end):
	""" CREATES POINTS OF INTEREST FOR GRAPH """
	points = [0, (start/4), (start/2), start, (start + ( (end-start)/4 )), (start + ( (end-start)/2 )), end]
	returnPoints = {}

	i = 0
	while i < len(points):
		# points[i] = point timestamp
		kills = 0.0
		deaths = 0.0
		assists = 0.0
		for event in killTable:
			if event['timestamp'] < points[i]:
				if playerId in event['killer']: kills += 1.0
				elif playerId in event['victim']:	deaths += 1.0
				elif playerId in event['assistants']:	assists += 1.0
		if deaths == 0: KDA = (kills + assists)/1 # dont divide by 0, silly
		else: KDA = (kills + assists)/deaths

		# GpM and CSpM
		if points[i] < 600000: 
			GpM = playerTable[playerId]['goldPerMinDeltas']['zeroToTen']
			CSpM = playerTable[playerId]['creepsPerMinDeltas']['zeroToTen']

		elif points[i] > 600000 and points[i] < 1200000: 
			if 'tenToTwenty' in playerTable[playerId]['goldPerMinDeltas']:
				GpM = playerTable[playerId]['goldPerMinDeltas']['tenToTwenty']
				CSpM = playerTable[playerId]['creepsPerMinDeltas']['tenToTwenty']
			else: 
				GpM = playerTable[playerId]['goldPerMinDeltas']['zeroToTen']
				CSpM = playerTable[playerId]['creepsPerMinDeltas']['zeroToTen']

		elif points[i] > 1200000 and points[i] < 1800000: 
			if 'twentyToThirty' in playerTable[playerId]['goldPerMinDeltas']:
				GpM = playerTable[playerId]['goldPerMinDeltas']['twentyToThirty']
				CSpM = playerTable[playerId]['creepsPerMinDeltas']['twentyToThirty']
			else:
				GpM = playerTable[playerId]['goldPerMinDeltas']['tenToTwenty']
				CSpM = playerTable[playerId]['creepsPerMinDeltas']['tenToTwenty']
		elif points[i] > 1800000: 
			if 'thirtyToEnd' in playerTable[playerId]['goldPerMinDeltas']:
				GpM = playerTable[playerId]['goldPerMinDeltas']['thirtyToEnd']
				CSpM = playerTable[playerId]['creepsPerMinDeltas']['thirtyToEnd']
			else: 
				GpM = playerTable[playerId]['goldPerMinDeltas']['twentyToThirty']
				CSpM = playerTable[playerId]['creepsPerMinDeltas']['twentyToThirty']

		returnPoints[i] = [round(KDA, 2), round(CSpM, 2), round(GpM, 2), points[i]]
		i += 1

	return returnPoints

def process2(matchDumpFile, targetDB, eventsDB, jsonDir):
	"""
	PROCESS RAW DATA DUMP & POPULATE:
		* targetDB: stores unformated graph data, later formatted via formatForGraph()
	"""

	with open (matchDumpFile, 'r') as m:
		dumpData = m.readlines()

	itemTable = eval(dumpData[0])
	killTable = eval(dumpData[1])
	playerTable = eval(dumpData[2])
	banTable = eval(dumpData[3])
	matchDuration = eval(dumpData[4]) * 1000 # to ms for uniformity with timestamps

	for player, items in itemTable.iteritems():
		championId = playerTable[player]['championId']

		itemLife = {}
		for item, events in items.iteritems():				
			count_Purchased = 0
			count_UndoPurchased = 0
			count_Sold = 0
			count_UndoSold = 0

			undo = undoFix(events['undo'])['undo']
			undoCount_purchased = len(undo['undo_purchased'])
			undoCount_sold = len(undo['undo_sold'])
			destroyed = events['destroyed']
			destroyedCount = len(destroyed)

			""" PURCHASE """
			purchaseNum = 0
			for purchase in events['purchased']:
				if undoCount_purchased > 0 and purchaseNum < undoCount_purchased:
					count_UndoPurchased += 1 # undone purchase
				elif destroyedCount > 0 and purchaseNum < destroyedCount:
					""" BRAWLER ITEMS LOGIC """
					# BRAWLER items get destroyed upon purchase
					if item in brawlerItems:
						if item not in itemLife:
							itemLife[item] = []
						itemLife[item].append([purchase, matchDuration])
						count_Purchased += 1

					""" UPGRADING ITEMS LOGIC """
					if item in upgradingItems:
						upgradeTime = items[item]['destroyed'][purchaseNum]
						# unupgraded item to itemLife array
						if item not in itemLife:
							itemLife[item] = []
						itemLife[item].append([purchase, upgradeTime])
						# upgraded item to itemLife array
						item = upgradingItems[item]
						if item not in itemLife:
							itemLife[item] = []
						itemLife[item].append([upgradeTime, matchDuration])
					else:
						# RAW DATA DUMPS only contain destroy events for upgrading 
						# items, so this pertains only to them and not ALL items
						if item not in untrackedItems:
							destroyTime = items[item]['destroyed'][0]
							# [0] = only first destroy (upgrade) event; REASON: if player sells upgradED item and later
							# buys the same base upgradING item again -> ignore the consecutive destruction (upgrade);
							if item not in itemLife:
								itemLife[item] = []
							itemLife[item].append([purchase, destroyTime])
					""" // UPGRADING ITEMS LOGIC """
				else:
					if item not in itemLife:
						itemLife[item] = []
					itemLife[item].append([purchase, matchDuration])
					count_Purchased += 1

				purchaseNum += 1

			""" SALE """
			saleNum = 0 # only for undo check
			saleIndex = 0 # has to be separate from saleNum
			for sale in events['sold']:
				if undoCount_sold > 0 and saleNum < undoCount_sold:
					count_UndoSold += 1
					saleNum += 1
				else:
					if item not in itemLife:
						itemLife[item] = []
						itemLife[item].append([0,sale])
					else:
						if saleIndex < len(itemLife[item]):
							# stupid case: when item1 is destroyed (i.e. built into item2) and
							# then that is undone the UNDO event doesnt list/bring back item1 (sigh)
							itemLife[item][saleIndex][1] = sale
					count_Sold += 1
					saleIndex += 1

			""" update EVENTS DB """
			if item not in eventsDB:
				eventsDB[item] = [count_Purchased, count_UndoPurchased, count_Sold, count_UndoSold]
			else:
				eventsDB[item][0] += count_Purchased
				eventsDB[item][1] += count_UndoPurchased
				eventsDB[item][2] += count_Sold
				eventsDB[item][3] += count_UndoSold

		""" GRAPH DATA FOR ITEMS PER PLAYER """
		""" ------ NEEDS REFACTORING ------ """
		for item, lifespan in itemLife.iteritems():
			if item not in untrackedItems:
				with open(os.path.join(jsonDir, str(item) + '.json')) as x:
					itemJson = json.load(x) # get item's topList
				if str(championId) not in itemJson['champs']:
					continue # player's champion is not in item's topList; skip ahead

				for instance in lifespan:
					if item not in targetDB:
						targetDB[item] = {'global': [], championId: []}
						targetDB[item]['global'] = [pointify(killTable, playerTable, player, instance[0], instance[1])]
						targetDB[item][championId] = [pointify(killTable, playerTable, player, instance[0], instance[1])]
					else:
						targetDB[item]['global'].append(pointify(killTable, playerTable, player, instance[0], instance[1]))
						if championId not in targetDB[item]:
							targetDB[item][championId] = []
							targetDB[item][championId].append(pointify(killTable, playerTable, player, instance[0], instance[1]))
						else:
							targetDB[item][championId].append(pointify(killTable, playerTable, player, instance[0], instance[1]))

def formatForGraph(targetDB):
	formattedDatabase = {}
	""" GROUP POINTS OF INTEREST """
	groupedPoints = {}
	for item, itemData in targetDB.iteritems():
		for scope, scopeData in itemData.iteritems():
			point0, point1, point2, point3, point4, point5, point6 = [], [], [], [], [], [], []

			for match in scopeData:
				for point, pointValues in match.iteritems():
					if point == 0: point0.append(pointValues)
					elif point == 1: point1.append(pointValues)
					elif point == 2: point2.append(pointValues)
					elif point == 3: point3.append(pointValues)
					elif point == 4: point4.append(pointValues)
					elif point == 5: point5.append(pointValues)
					else: point6.append(pointValues)

			# AVERAGE THE POINTS
			point0 = [sum(x)/len(x) for x in zip(*point0)]
			point1 = [sum(x)/len(x) for x in zip(*point1)]
			point2 = [sum(x)/len(x) for x in zip(*point2)]
			point3 = [sum(x)/len(x) for x in zip(*point3)]
			point4 = [sum(x)/len(x) for x in zip(*point4)]
			point5 = [sum(x)/len(x) for x in zip(*point5)]
			point6 = [sum(x)/len(x) for x in zip(*point6)]
			if item not in groupedPoints:
				groupedPoints[item] = {scope: [point0, point1, point2, point3, point4, point5, point6]}
			else:
				groupedPoints[item][scope] = [point0, point1, point2, point3, point4, point5, point6]

	""" CREATE FINAL ITEM OBJECT FORMAT; JSONIFY """
	for item, scopes in groupedPoints.iteritems():
		itemObj = {}
		for scope, scopeData in scopes.iteritems():
			timestamps, goldData, creepsData, kdaData = [], [], [], []

			for point in scopeData:
				goldData.append( round(point[2]/12, 2) )
				creepsData.append( round(point[1], 2) )
				kdaData.append( round(point[0], 2) )
				# timestamp (ms) -> M:S
				s = int(point[3])/1000
				m, s = divmod(s, 60)
				timestamps.append( str(m).zfill(2) + ':' + str(s).zfill(2) )

			combined = { 'timestamps': timestamps, 'goldData': goldData,
				'creepsData': creepsData,'kdaData': kdaData }

			itemObj[scope] = combined

		formattedDatabase[item] = itemObj
	return formattedDatabase

def updateJson(formattedDatabase, jsonDir):
	for item, scopes in formattedDatabase.iteritems():
		with open(os.path.join(jsonDir, str(item) + '.json')) as oldJson:
			mediary = json.load(oldJson)
		mediary.update(scopes)

		with open(os.path.join(jsonDir, str(item) + '.json'), 'w') as newJson:
			json.dump(mediary, newJson)

# ------------------------ CHAMPION DATA PROCESSING ------------------------ #

def champStats(matchDumpFile, statsDB):
	"""
	PROCESS RAW DATA DUMP & POPULATE:
		* statsDB: stores stats on a per champion basis in format: 
		[ gameCount, winCount, kdaList[], banCount ]
		> kdaList[] is later averaged via averageKDA()
	"""
	with open (matchDumpFile, 'r') as m:
		dumpData = m.readlines()

	playerTable = eval(dumpData[2])
	banTable = eval(dumpData[3])

	# db format: [ gameCount, winCount, kdaList[], banCount ]

	for champ in banTable:
		if champ not in statsDB:
			statsDB[champ] = [0, 0, [], 1]
		else:
			statsDB[champ][3] += 1

	for player, data in playerTable.iteritems():
		if data['championId'] not in statsDB:
			statsDB[data['championId']] = [0, 0, [], 0]
		
		statsDB[data['championId']][0] += 1

		if data['winner']: statsDB[data['championId']][1] += 1

		if data['deaths'] == 0: KDA = (data['kills'] + data['assists'])/1
		else: KDA =  (data['kills'] + data['assists'])/data['deaths']
		statsDB[data['championId']][2].append(KDA)

def averageKDA(statsDB):
	for champ, stats in statsDB.iteritems():
		if len(stats[2]) != 0:
			averaged = round(sum(stats[2]) / float(len(stats[2])), 2)
			statsDB[champ][2] = averaged

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
	# ___ POINT TO RAW DUMP DATA & OUTPUT JSON DIRECTORY ___ #
	region = sys.argv[1].lower()
	matchData = glob('dump/' + region + '/*.txt')
	jsonDir = os.path.join(sys.argv[2], region)

	""" PROCESSING CHAMPS """
	# ___ Define DBs for use in processing ___ #
	statsDB = {}

	# ___ Run CHAMPION STATS processing ___ #
	progress = 0
	for match in matchData:
		progress += 1
		if progress <= len(matchData): print '(', str(progress) + ' / ' + str(len(matchData)) + ' )\r',
		champStats(match, statsDB)
	averageKDA(statsDB)

	if not os.path.exists(jsonDir):	os.makedirs(jsonDir) # if ran before item processing; makes sure jsonDir exists
	with open(os.path.join(jsonDir, 'champs.json'), 'w') as x:
		json.dump(statsDB, x)

	""" PROCESSING ITEMS """
	# ___ Define DBs for use in processing ___ #
	champsDB = {}
	itemsDB = {}
	eventsDB = {}

	# ___ Run the FIRST process step ___ #
	progress = 0
	for match in matchData:
		progress += 1
		if progress <= len(matchData): print '(', str(progress) + ' / ' + str(len(matchData)) + ' )\r',
		process1(match, champsDB, itemsDB)
	itemTopLists = narrowTopList(itemsDB, champsDB)
	createJson(itemTopLists, jsonDir)

	# ___ Flush the DBs, reuse in the second process step ___ #
	champsDB.clear()
	itemsDB.clear()

	# ___ Run the SECOND process step ___ #
	progress = 0
	for match in matchData:
		progress += 1
		if progress <= len(matchData): print '(', str(progress) + ' / ' + str(len(matchData)) + ' )\r',
		process2(match, itemsDB, eventsDB, jsonDir)

	# ___ OPTIONAL: Sort eventsDB at this point; I do it on the server ___ #
	# sorted_purchased = sorted(eventsDB.items(), key=lambda (k, v): v[0], reverse=True)
	# sorted_sold = sorted(eventsDB.items(), key=lambda (k, v): v[1], reverse=True)
	# sorted_undoPurchased = sorted(eventsDB.items(), key=lambda (k, v): v[2], reverse=True)
	# sorted_undoSold = sorted(eventsDB.items(), key=lambda (k, v): v[3], reverse=True)
	# with open(os.path.join(jsonDir, 'events.json'), 'w') as x:
	# 	json.dump([sorted_purchased, sorted_undoPurchased, sorted_sold, sorted_undoSold], x)
	with open(os.path.join(jsonDir, 'events.json'), 'w') as x:
		json.dump(eventsDB, x)

	# ___ Format and update JSONs with graph data; ___ #
	itemsDB = formatForGraph(itemsDB)
	updateJson(itemsDB, jsonDir)