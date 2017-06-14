#!/usr/bin/python
#
# Copyright 2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Disable the invalid name warning as we are inheriting from a standard library
# object.
# pylint: disable-msg=C6409,W0212

"""
Stripped down version of `python-datetime-tz` that only contains the "find local
timezone" bits.
"""

import datetime
import os.path
import time
import warnings
import pytz


# Need to patch pytz.utc to have a _utcoffset so you can normalize/localize
# using it.
pytz.utc._utcoffset = datetime.timedelta()


timedelta = datetime.timedelta


def _tzinfome(tzinfo):
  """Gets a tzinfo object from a string.

  Args:
    tzinfo: A string (or string like) object, or a datetime.tzinfo object.

  Returns:
    An datetime.tzinfo object.

  Raises:
    UnknownTimeZoneError: If the timezone given can't be decoded.
  """
  if not isinstance(tzinfo, datetime.tzinfo):
    try:
      tzinfo = pytz.timezone(tzinfo)
    except AttributeError:
      raise pytz.UnknownTimeZoneError("Unknown timezone!")
  return tzinfo


# Our "local" timezone
_localtz = None


def localtz():
  """Get the local timezone.

  Returns:
    The localtime timezone as a tzinfo object.
  """
  # pylint: disable-msg=W0603
  global _localtz
  if _localtz is None:
    _localtz = detect_timezone()
  return _localtz


def detect_timezone():
  """Try and detect the timezone that Python is currently running in.

  We have a bunch of different methods for trying to figure this out (listed in
  order they are attempted).
    * Try and find /etc/timezone file (with timezone name).
    * Try and find /etc/localtime file (with timezone data).
    * Try and match a TZ to the current dst/offset/shortname.

  Returns:
    The detected local timezone as a tzinfo object

  Raises:
    pytz.UnknownTimeZoneError: If it was unable to detect a timezone.
  """

  tz = _detect_timezone_etc_timezone()
  if tz is not None:
    return tz

  tz = _detect_timezone_etc_localtime()
  if tz is not None:
    return tz

  # Next we try and use a similiar method to what PHP does.
  # We first try to search on time.tzname, time.timezone, time.daylight to
  # match a pytz zone.
  warnings.warn("Had to fall back to worst detection method (the 'PHP' "
                "method).")

  tz = _detect_timezone_php()
  if tz is not None:
    return tz

  raise pytz.UnknownTimeZoneError("Unable to detect your timezone!")

def _detect_timezone_etc_timezone():
  if os.path.exists("/etc/timezone"):
    try:
      tz = file("/etc/timezone").read().strip()
      try:
        return pytz.timezone(tz)
      except (IOError, pytz.UnknownTimeZoneError), ei:
        warnings.warn("Your /etc/timezone file references a timezone (%r) that"
                      " is not valid (%r)." % (tz, ei))

    # Problem reading the /etc/timezone file
    except IOError, eo:
      warnings.warn("Could not access your /etc/timezone file: %s" % eo)


def _detect_timezone_etc_localtime():
  matches = []
  if os.path.exists("/etc/localtime"):
    localtime = pytz.tzfile.build_tzinfo("/etc/localtime",
                                         file("/etc/localtime"))

    # See if we can find a "Human Name" for this..
    for tzname in pytz.all_timezones:
      tz = _tzinfome(tzname)

      if dir(tz) != dir(localtime):
        continue

      for attrib in dir(tz):
        # Ignore functions and specials
        if callable(getattr(tz, attrib)) or attrib.startswith("__"):
          continue

        # This will always be different
        if attrib == "zone" or attrib == "_tzinfos":
          continue

        if getattr(tz, attrib) != getattr(localtime, attrib):
          break

      # We get here iff break didn't happen, i.e. no meaningful attributes
      # differ between tz and localtime
      else:
        matches.append(tzname)

    #if len(matches) == 1:
    #  return _tzinfome(matches[0])
    #else:
    #  # Warn the person about this!
    #  warning = "Could not get a human name for your timezone: "
    #  if len(matches) > 1:
    #    warning += ("We detected multiple matches for your /etc/localtime. "
    #                "(Matches where %s)" % matches)
    #  else:
    #    warning += "We detected no matches for your /etc/localtime."
    #  warnings.warn(warning)
    #
    #  return localtime
    if len(matches) > 0:
        return _tzinfome(matches[0])


def _detect_timezone_php():
  tomatch = (time.tzname[0], time.timezone, time.daylight)
  now = datetime.datetime.now()

  matches = []
  for tzname in pytz.all_timezones:
    try:
      tz = pytz.timezone(tzname)
    except IOError:
      continue

    try:
      indst = tz.localize(now).timetuple()[-1]

      if tomatch == (tz._tzname, -tz._utcoffset.seconds, indst):
        matches.append(tzname)

    # pylint: disable-msg=W0704
    except AttributeError:
      pass

  if len(matches) > 1:
    warnings.warn("We detected multiple matches for the timezone, choosing "
                  "the first %s. (Matches where %s)" % (matches[0], matches))
    return pytz.timezone(matches[0])

