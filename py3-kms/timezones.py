#!/usr/bin/env python3

# vim: set ts=2 sw=2 et sts=2 ai:
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

# Disable the invalid name warning as we are inheriting from a standard library
# object.
# pylint: disable=invalid-name,protected-access

"""
Stripped down version of `python-datetime-tz`
( https://github.com/mithro/python-datetime-tz/blob/master/datetime_tz/__init__.py ) 
that only contains the "find local timezone" bits.
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
      assert tzinfo.zone in pytz.all_timezones
    except AttributeError:
      raise pytz.UnknownTimeZoneError("Unknown timezone! %s" % tzinfo)
  return tzinfo


# Our "local" timezone
_localtz = None


def localtz():
  """Get the local timezone.

  Returns:
    The localtime timezone as a tzinfo object.
  """
  # pylint: disable=global-statement
  global _localtz
  if _localtz is None:
    _localtz = detect_timezone()
  return _localtz


def detect_timezone():
  """Try and detect the timezone that Python is currently running in.

  We have a bunch of different methods for trying to figure this out (listed in
  order they are attempted).
    * In windows, use win32timezone.TimeZoneInfo.local()
    * Try TZ environment variable.
    * Try and find /etc/timezone file (with timezone name).
    * Try and find /etc/localtime file (with timezone data).
    * Try and match a TZ to the current dst/offset/shortname.

  Returns:
    The detected local timezone as a tzinfo object

  Raises:
    pytz.UnknownTimeZoneError: If it was unable to detect a timezone.
  """

  # First we try the TZ variable
  tz = _detect_timezone_environ()
  if tz is not None:
    return tz

  # Second we try /etc/timezone and use the value in that
  tz = _detect_timezone_etc_timezone()
  if tz is not None:
    return tz

  # Next we try and see if something matches the tzinfo in /etc/localtime
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


def _detect_timezone_environ():
  if "TZ" in os.environ:
    try:
      return pytz.timezone(os.environ["TZ"])
    except (IOError, pytz.UnknownTimeZoneError):
      warnings.warn("You provided a TZ environment value (%r) we did not "
                    "understand!" % os.environ["TZ"])


def _detect_timezone_etc_timezone():
  if os.path.exists("/etc/timezone"):
    try:
      tz = open("/etc/timezone").read().strip()
      try:
        return pytz.timezone(tz)
      except (IOError, pytz.UnknownTimeZoneError) as ei:
        warnings.warn("Your /etc/timezone file references a timezone (%r) that"
                      " is not valid (%r)." % (tz, ei))

    # Problem reading the /etc/timezone file
    except IOError as eo:
      warnings.warn("Could not access your /etc/timezone file: %s" % eo)


def _load_local_tzinfo():
  """Load zoneinfo from local disk."""
  tzdir = os.environ.get("TZDIR", "/usr/share/zoneinfo/posix")

  localtzdata = {}
  for dirpath, _, filenames in os.walk(tzdir):
    for filename in filenames:
      filepath = os.path.join(dirpath, filename)
      name = os.path.relpath(filepath, tzdir)

      f = open(filepath, "rb")
      tzinfo = pytz.tzfile.build_tzinfo(name, f)
      f.close()
      localtzdata[name] = tzinfo

  return localtzdata


def _detect_timezone_etc_localtime():
  """Detect timezone based on /etc/localtime file."""
  matches = []
  if os.path.exists("/etc/localtime"):
    f = open("/etc/localtime", "rb")
    localtime = pytz.tzfile.build_tzinfo("/etc/localtime", f)
    f.close()

    # We want to match against the local database because /etc/localtime will
    # be copied from that. Once we have found a name for /etc/localtime, we can
    # use the name to get the "same" timezone from the inbuilt pytz database.

    tzdatabase = _load_local_tzinfo()
    if tzdatabase:
      tznames = tzdatabase.keys()
      tzvalues = tzdatabase.__getitem__
    else:
      tznames = pytz.all_timezones
      tzvalues = _tzinfome

    # See if we can find a "Human Name" for this..
    for tzname in tznames:
      tz = tzvalues(tzname)

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
        # Try and get a timezone from pytz which has the same name as the zone
        # which matches in the local database.
        if tzname not in pytz.all_timezones:
          warnings.warn("Skipping %s because not in pytz database." % tzname)
          continue

        matches.append(_tzinfome(tzname))

    matches.sort(key=lambda x: x.zone)

    if len(matches) == 1:
      return matches[0]

    if len(matches) > 1:
      warnings.warn("We detected multiple matches for your /etc/localtime. "
                    "(Matches where %s)" % matches)
      return matches[0]
    else:
      warnings.warn("We detected no matches for your /etc/localtime.")

    # Register /etc/localtime as the timezone loaded.
    pytz._tzinfo_cache["/etc/localtime"] = localtime
    return localtime


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

    # pylint: disable=pointless-except
    except AttributeError:
      pass

  if len(matches) > 1:
    warnings.warn("We detected multiple matches for the timezone, choosing "
                  "the first %s. (Matches where %s)" % (matches[0], matches))
  if matches:
    return pytz.timezone(matches[0])

