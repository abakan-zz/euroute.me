from time import time
from collections import defaultdict

import numpy as np
import networkx as nx

from flask import json

from dbhandle import DBHandle

dbh = DBHandle()


# (num of days, max travel hours) -> number of cities
NUMCITIES = {
    (3, 4): 2, (4, 4): 2, (5, 4): 3, (6, 4): 3, (7, 4): 4, (8, 4): 4, (9, 4): 5, (10, 4): 5,
    (3, 7): 2, (4, 7): 2, (5, 7): 3, (6, 7): 3, (7, 7): 3, (8, 7): 4, (9, 7): 4, (10, 7): 4,
    (3, 10): 2, (4, 10): 2, (5, 10): 2, (6, 10): 3, (7, 10): 3, (8, 10): 4, (9, 10): 4, (10, 10): 4,
}

# (travel mode, max hours) -> Graph
GRAPHS = {}
# (travel mode, max hours) -> links in JSON format
LINKS = {}

WEIGHTS = np.array([1., 1., .5, .5, .5])
CATEGORIES = ['Art', 'Historic', 'Technical', 'Amusement', 'Nature']

COUNTS = np.zeros((dbh("SELECT MAX(id) FROM city")[0][0] + 1, 5), int)

# (origin, destin, mode, days, hours) -> routes
ROUTES = {}

for i, category in enumerate(CATEGORIES):
    for cid, pop in dbh("SELECT cityId, SUM(1) FROM place "
                        "WHERE category='{}'"
                        "GROUP BY cityId ".format(category)):
        if cid:
            COUNTS[cid][i] = pop

# (city, category) -> factoids
FACTOIDS = defaultdict(lambda: defaultdict(list))
for cid, cat, fact in dbh("SELECT cityId, category, factoid FROM factoid"):
    FACTOIDS[cid][cat].append(fact)

def get_graph(mode, hours):
    key = mode, hours
    try:
        graph = GRAPHS[key]
    except KeyError:
        pass
    else:
        return graph


    links = dbh("SELECT origin, destin, duration "
                "FROM link WHERE mode='{}' AND duration < {}"
                .format(mode, hours*60))

    data = defaultdict(lambda: defaultdict(dict))
    for origin, destin, duration in links:
        data[origin][destin]['time'] = duration
    LINKS[key] = data

    graph = GRAPHS[key] = nx.Graph()
    graph.add_weighted_edges_from(links)

    return graph


def score_routes(routes, weights, oneway=True):

    start = time()
    scores = np.dot(COUNTS, weights)
    if oneway:
        scores = [scores[route[:-1]].sum() for route in routes]
    else:
        scores = [scores[route].sum() for route in routes]
    print('INFO: Scoring takes {:.3f}'.format(time() - start))

    start = time()
    scored = zip(scores, routes)
    scored.sort(reverse=True)
    print('INFO: Sorting takes {:.3f}'.format(time() - start))
    return scored

def filter_routes(routes):

    rsets = set()
    filtered = []
    for route in routes:
        rset = frozenset(route)
        if rset in rsets:
            continue
        rsets.add(rset)
        filtered.append(route)
    return filtered

def get_scaled_scores(weights=WEIGHTS):
    scores = np.dot(COUNTS, weights)
    scores = scores * 500
    scores[scores==0] = 100
    return list(scores.astype(int))


def get_routes(origin, destin, mode, days, hours, weights=WEIGHTS):

    total = time()
    key = (origin, destin, mode, days, hours)
    if key in ROUTES:
        routes = ROUTES[key]
    else:
        start = time()
        graph = get_graph(mode, hours)
        ncity = NUMCITIES[days, hours]
        print('INFO: Graph was built in {0:.3f}s'
              .format(time() - start))

        start = time()
        routes = list(nx.all_simple_paths(graph, source=origin, target=destin,
                                          cutoff=ncity))
        print('INFO: {} routes were calculated in {:.3f}'
              .format(len(routes), time() - start))

        start = time()
        routes = filter_routes(routes)
        print('INFO: {} routes were selected in {:.3f}'
              .format(len(routes), time() - start))
        ROUTES[key] = routes
    start = time()
    routes = score_routes(routes, weights, origin==destin)
    print('INFO: {} routes were scored in {:.3f}'
          .format(len(routes), time() - start))
    print('INFO: All in all it takes {:.3f}'
          .format(time() - total))


    return [{'score': s, 'route': r} for s, r in routes]

# (city name, country name) -> city id
CITYMAP = {}
# city id -> various city data
CITYDATA = {}
for cid, cnm, co, coco, lat, lng in dbh(
    "SELECT id, city.name, country.name, country.code, latitude, longitude "
    "FROM city JOIN country ON city.countryCode=country.code"):
    CITYMAP[(cnm, co)] = cid
    CITYDATA[cid] = {
        'name': cnm,
        #'co': co,
        'lat': lat,
        'lng': lng,
        'marker': None,
        'id': cid
    }

CITYJSON = json.dumps(CITYDATA)


