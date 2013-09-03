#!/usr/bin/python

# calculate sunrise/sunset times for location
# Andrew Elwell <Andrew.Elwell@gmail.com> 2013-09-02

# pyephem http://rhodesmill.org/pyephem/ does all the hard work
import ephem
import ConfigParser

config = "/home/andrew/solarmon.cfg"

settings = ConfigParser.RawConfigParser()
settings.read(config)

home = ephem.Observer()
home.lat = settings.get('general', 'lat')
home.lon = settings.get('general', 'lon')

#print home.lat, home.lon

sunrise = ephem.localtime(home.next_rising(ephem.Sun()))
sunset = ephem.localtime(home.next_setting(ephem.Sun()))

print "sunrise: %s, sunset: %s" % (sunrise, sunset)
