# Black Market Goods (& Bads)
This is an entry for the [Riot Games API Challenge 2.0](https://developer.riotgames.com/discussion/announcements/show/2lxEyIcE) in the **Black Market Brawlers** category.

**Black Market Goods (& Bads)** processes and presents crunched Black Market Brawlers match data from 10,000 games per region. Notably, individual items' impact on player performance is graphed for a relative understanding of item value.

## Demo
[![demo site](/demo_shot.jpg?raw=true)](http://104.236.45.210/na/)
Before I bore you with my many words, here's a working demo to back them.

## The nitty-gritty
### Processing
A pure Python solution, the match data processing - while arguably not efficiently optimized (yet) - is fairly thoroughly explained in-code.

#### Quick rundown: 
First we scrape the match data off the API with **api_crawl.py**. As simple as:

`api_crawl.py <region>`

Pertinent data is dumped in a temporary directory (`dump/<region>`) in the format:
+ itemTable - item/store events (purchases, sales, undos, upgrades)
+ killTable - killer, assistants and victim & their builds at the event point
+ playerTable & banTable - self explanatory


Onwards to the brains of it all, **process.py**:

`process.py <region> <target dir>`

**NOTE:** This is REALLY detailedly commented at every step of the code so I'd suggest you just look at that, but in short:
+ We start off with the fairly basic right now (see "What's next?"), champion stats processing
+ The first item data processing loop narrows down a list of the 10 champions who bought X item the most so individual graph data for them can be created
+ The second item data processing loop does the big lifting - graph/timeline data population, grouping and averaging based on item events (purchases, sales, etc);
+ All the data for individual items, top item & champ stats (most purchased, most played, etc) is packed and sorted into JSONs pushed to `<target dir>`; note that ordering these top stats I've personally delegated to the server to handle instead (no particular reason, could have easily been stored in ordered JSON arrays here)

From here we go to the...

### Server
**Flask on Nginx (& uWSGI) + PJAX**

While 99.9% of the data is processed before being handed to the server, there are a couple minor tasks it runs apart from presenting our crunched data to the user - sorting champions & items stats for the top lists, and building build paths (*ha!*) for items.

Using a couple libraries on the frontend worth mentioning here - [Chart.js](https://github.com/nnnick/Chart.js/), [Typeahead.js](https://github.com/twitter/typeahead.js/) and [DataTables](https://github.com/DataTables/DataTables).

The [PJAX](https://github.com/defunkt/jquery-pjax) part was a personal itch/experiment as I've wanted to make one of those seemingly seamless websites for a while and never had a project that could benefit from it. 

## What's next?
Basics down just in time for the challenge deadline, the plan is to keep at it and potentially expand past BMB statistics. 

Due to time constraints there is a particular originally planned feature that didn't make the cut (which makes me sad... so very, very sad) - detailed champion statistics (blimey! the whole individual champion page is missing). It's sitting with a priority on the TODO list:

| Champ stats |
--- |
| Overall performance with a timeline representation (similar to the PERFORMANCE IMPACT graphs for items); common and/or best performing item builds and build orders (provide curated item sets for download?) |

 

| Refactoring code |
--- |
| Specifically the graph data processing which is fairly taxing and some other touchups I might notice while at it |

 

| Personal stats |
--- |
| This is the first idea that would mean expanding past BMB. Allow users to analyze their own games and compare with their peers. Provide stats for players on the same level of play - what they build, what of it leads to good performance, what bad and what items and/or tactics counter others. |

etc, etc... don't mean to bore you with just ideas; I'd much rather actually work on executing them than write about them. Have a "*Soon™*".