import re
from time import time
from random import choice
from collections import defaultdict

from flask import Flask, redirect, request, render_template
from flask import json

import numpy as np
import networkx as nx

#from dbhandle import DBHandle

app = Flask(__name__)
#dbh = DBHandle()

app.debug = True

execfile('router.py')

# HTML
@app.route("/")
def index():
    return render_template('index.html',
        days=0, origin='', destin='', oneway=-1)


ONEWAY = re.compile(ur"(?P<days>\d+)-days-from-(?P<origin>\w+)-(?P<ocountry>\w+)-to-(?P<destin>\w+)-(?P<dcountry>\w+)-by-(?P<mode>\w+)", re.U)
ROUND = re.compile(ur"(?P<days>\d+)-days-around-(?P<origin>\w+)-(?P<ocountry>\w+)-by-(?P<mode>\w+)", re.U)

# HTML
@app.route("/<trip>", methods=['GET', 'POST'])
def figure(trip):

    args = ROUND.match(trip)
    oneway = False
    if args is None:
        args = ONEWAY.match(trip)
        oneway = True

    if args is None:
        redirect("/")

    args = args.groupdict()


    city = dest = ' '.join(args['origin'].split('_')).strip()
    try:
        if 'ocountry' in args:
            country = ' '.join(args['ocountry'].split('_')).strip()
            origin = destin = CITYMAP[(city, country)]
            ofails = city + ', ' + country
        else:
            ofails = city
            origin = destin = CITYMAP[city]
    except KeyError:
        redirect('/')

    if oneway:
        dest = ' '.join(args['destin'].split('_')).strip()
        try:
            if 'dcountry' in args:
                country = ' '.join(args['dcountry'].split('_')).strip()
                destin = CITYMAP[(dest, country)]
                dfails = dest + ', ' + country
            else:
                destin = CITYMAP[dest]
                dfails = dest
        except KeyError:
            redirect('/')

    days = int(args['days'])
    if not (3 <= days <= 10):
        redirect('/')
    mode = args['mode'][0].upper()
    if mode not in "DT":
        redirect('/')
    routes, hours = get_scored_routes(origin, destin, mode, days, 4)
    if routes:
        return render_template('route.html',
            cities=CITYJSON, routes=json.dumps(routes[:15]),
            links=json.dumps(LINKS[mode, 10]), mode=mode,
            city=city, dest=dest, days=days, hours=hours,
            origin=origin, destin=destin,
            scores=json.dumps(get_scaled_scores()),
            factoids=json.dumps(FACTOIDS),
            around=["false", "true"][origin == destin],
            gmap=bool(int(request.args.get("gmap", 1))))
    else:
        return render_template('index.html', fails=True,
            origin=ofails, destin=dfails, days=days, oneway= origin != destin)


# JSON
def cities():
    """Return list of cities, e.g ["Berlin, Germany", "Bordeaux, France"]."""

    q = request.args.get('q').split(',')[0]
    sql = ("SELECT city.name, country.name "
           "FROM city JOIN country ON city.countryCode=country.code "
           "WHERE city.oglinks > 0 AND city.name LIKE '{0}%' " #OR Country.name LIKE '{0}%'"
           #"LIMIT 10"
           ).format(q)

    return json.dumps([u'{}, {}'.format(city, country)
                       for city, country in dbh(sql)])


def places():

    city = int(request.args.get('city'))

    cats = [(float(request.args.get('arts')), 'art'),
    (float(request.args.get('history')), 'historic'),
    (float(request.args.get('technical')), 'technical'),
    (float(request.args.get('amusement')), 'amusement'),
    (float(request.args.get('nature')), 'nature'),]

    cats.sort(reverse=True)
    places = {}
    for want, cat in cats:
        if not want:
            break
        places[cat] = dbh("SELECT subcategory, name, url FROM place "
                          "WHERE category='{}' AND cityId={}"
                          .format(cat, city))
    return json.dumps(places)


def reroute():

    origin = int(request.args.get('origin'))
    destin = int(request.args.get('destin'))
    days = int(request.args.get('days'))
    mode = request.args.get('mode').upper()[0]
    hours = int(request.args.get('hours'))
    weights = np.array([float(request.args.get('arts')),
                        float(request.args.get('history')),
                        float(request.args.get('technical')),
                        float(request.args.get('amusement')),
                        float(request.args.get('nature'))])
    routes, hours = get_scored_routes(origin, destin, mode, days, hours, weights)[:15]
    return json.dumps({
        'scores': get_scaled_scores(weights),
        'routes': routes,
    })


JSON = {
    'cities': cities,
    'reroute': reroute,
    'places': places
}


@app.route("/json/<what>")
def rjson(what):

    return JSON[what]()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    pass