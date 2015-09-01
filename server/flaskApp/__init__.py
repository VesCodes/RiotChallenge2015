from flask import Flask, render_template, url_for, redirect
from flask_pjax import PJAX
from os import path
import json

application = Flask(__name__)
PJAX(application)
# application.debug = True # TURN OFF WHEN GOING LIVE!!
APP_ROOT = path.dirname(path.abspath(__file__))

with open(path.join(APP_ROOT, 'static/json/item.json')) as x, open(path.join(APP_ROOT, 'static/json/champion.json')) as y:
    itemsJson = json.load(x)['data']
    champsJson = json.load(y)['data']

regions = ['na', 'euw', 'eune', 'br', 'tr', 'ru', 'lan', 'las', 'oce']
untrackedItems = [2003, 2004, 2009, 2010, 2052, 2054, 2047,
2137, 2138, 2139, 2140,
2043, 2044,
3340, 3341, 3342, 3345, 3361, 3362, 3363, 3364,
3040, 3042, 3930, 3931, 3932, 3933]


@application.route('/', defaults={'region': 'teehee'})
@application.route('/<region>/')
def home(region):
    if region not in regions:
        return redirect(url_for('home', region='na'), code=302)
    regions.insert(0, regions.pop(regions.index(region))) # move selected region to first index

    with open(path.join(APP_ROOT, 'static/json/', region, 'events.json')) as x, open(path.join(APP_ROOT, 'static/json/', region, 'champs.json')) as y:
        eventsDB = json.load(x)
        statsDB = json.load(y)

    # STRIP CONSUMABLES & ETC FROM TOP RESULTS
    for item in untrackedItems:
        if str(item) in eventsDB:
            eventsDB.pop(str(item), None)

    # SORT EVENTSDB
    sorted_purchased = sorted(eventsDB.items(), key=lambda (k, v): v[0], reverse=True)
    sorted_sold = sorted(eventsDB.items(), key=lambda (k, v): v[1], reverse=True)
    sorted_undoPurchased = sorted(eventsDB.items(), key=lambda (k, v): v[2], reverse=True)
    sorted_undoSold = sorted(eventsDB.items(), key=lambda (k, v): v[3], reverse=True)

    sorted_eventsDB = [sorted_purchased, sorted_sold, sorted_undoPurchased, sorted_undoSold]
    
    # SORT STATSDB
    sorted_gameCount = sorted(statsDB.items(), key=lambda (k, v): v[0], reverse=True)
    sorted_winCount = sorted(statsDB.items(), key=lambda (k, v): v[1], reverse=True)
    sorted_kda = sorted(statsDB.items(), key=lambda (k, v): v[2], reverse=True)
    sorted_banCount = sorted(statsDB.items(), key=lambda (k, v): v[3], reverse=True)
    sorted_winRate = sorted(statsDB.items(), key=lambda (k, v): 100 * float(v[1])/float(v[0]), reverse=True)

    sorted_statsDB = [sorted_gameCount, sorted_winCount, sorted_kda, sorted_banCount, sorted_winRate]

    return render_template('index.html', region=region, regions=regions, itemsJson=itemsJson, champsJson=champsJson,
        eventsDB=sorted_eventsDB, statsDB=sorted_statsDB)


@application.route('/item/<int:itemId>/', defaults={'region': 'teehee'})
@application.route('/<region>/item/<int:itemId>/')
def itemPage(region, itemId):
    if region not in regions:
        return redirect(url_for('itemPage', region='na', itemId=itemId), code=302)
    regions.insert(0, regions.pop(regions.index(region)))

    if str(itemId) not in itemsJson:
        return 'four-oh-four, dude.'

    current_itemJsonPath = path.join(APP_ROOT, 'static/json/', region, str(itemId) + '.json')
    if not path.isfile(current_itemJsonPath): # no stats for item; load up dummy json
        with open(path.join(APP_ROOT, 'static/json/dummy.json')) as x:
            current_itemJson = json.load(x)
    else:
        with open(current_itemJsonPath) as x:
            current_itemJson = json.load(x)

    # PROCESS BUILD PATH
    buildPathHtml = []
    buildPath(itemsJson[str(itemId)], buildPathHtml, split=1)
    buildPathHtml = ''.join(buildPathHtml)

    sorted_topChamps = sorted(current_itemJson['champs'].items(), key=lambda (k,v): v, reverse=True)

    return render_template('item.html', region=region, regions=regions, itemsJson=itemsJson, champsJson=champsJson, 
        current=str(itemId), buildPath=buildPathHtml, topChamps=sorted_topChamps)

@application.route('/champions/', defaults={'region': 'teehee'})
@application.route('/<region>/champions/')
def champlistPage(region):
    if region not in regions:
        return redirect(url_for('champlistPage', region='na'), code=302)
    regions.insert(0, regions.pop(regions.index(region)))

    with open(path.join(APP_ROOT, 'static/json/', region, 'champs.json')) as x:
        statsDB = json.load(x)

    # SORT STATSDB
    sorted_gameCount = sorted(statsDB.items(), key=lambda (k, v): v[0], reverse=True)
    sorted_winCount = sorted(statsDB.items(), key=lambda (k, v): v[1], reverse=True)
    sorted_kda = sorted(statsDB.items(), key=lambda (k, v): v[2], reverse=True)
    sorted_banCount = sorted(statsDB.items(), key=lambda (k, v): v[3], reverse=True)
    sorted_winRate = sorted(statsDB.items(), key=lambda (k, v): 100 * float(v[1])/float(v[0]), reverse=True)

    sorted_statsDB = [sorted_gameCount, sorted_winCount, sorted_kda, sorted_banCount, sorted_winRate]

    return render_template('champlist.html', region=region, regions=regions, champsJson=champsJson, statsDB=sorted_statsDB)


@application.route('/items/', defaults={'region': 'teehee'})
@application.route('/<region>/items/')
def itemlistPage(region):
    if region not in regions:
        return redirect(url_for('itemlistPage', region='na'), code=302)
    regions.insert(0, regions.pop(regions.index(region)))

    with open(path.join(APP_ROOT, 'static/json/', region, 'events.json')) as x:
        eventsDB = json.load(x)

    # SORT EVENTSDB
    sorted_purchased = sorted(eventsDB.items(), key=lambda (k, v): v[0], reverse=True)
    sorted_sold = sorted(eventsDB.items(), key=lambda (k, v): v[1], reverse=True)
    sorted_undoPurchased = sorted(eventsDB.items(), key=lambda (k, v): v[2], reverse=True)
    sorted_undoSold = sorted(eventsDB.items(), key=lambda (k, v): v[3], reverse=True)

    sorted_eventsDB = [sorted_purchased, sorted_sold, sorted_undoPurchased, sorted_undoSold]

    return render_template('itemlist.html', region=region, regions=regions, itemsJson=itemsJson, eventsDB=sorted_eventsDB)

def buildPath(item, html, split):
    split = 100/split
    if 'from' in item:
        html.append('<div class="branch" style="width: {}%;">'.format(str(split)))
        html.append('<div class="head" style="width: 100%;">')
        html.append('<a href="{}" title="{}">'.format(url_for('itemPage', itemId=item['id']), item['name']))
        html.append('<img src="' + url_for('static', filename='images/item/' + str(item['id']) + '.png') + '" />')
        html.append('</a></div>')

    else:
        html.append('<div class="head" style="width: {}%;">'.format(str(split)))
        html.append('<a href="{}" title="{}">'.format(url_for('itemPage', itemId=item['id']), item['name']))
        html.append('<img src="' + url_for('static', filename='images/item/' + str(item['id']) + '.png') + '" />')
        html.append('</a></div>')

    if 'from' in item:
        split = 100
        html.append('<div class="branch" style="width: {}%;">'.format(str(split)))
        for child in item['from']:
            buildPath(itemsJson[child], html, split=len(item['from']))
        html.append('</div></div>')

if __name__ == '__main__':
    application.run(host='0.0.0.0')
