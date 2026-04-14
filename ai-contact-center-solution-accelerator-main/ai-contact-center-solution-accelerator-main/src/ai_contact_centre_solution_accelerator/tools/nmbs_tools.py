"""
NMBS real-time train data plugin using the iRail open API (https://api.irail.be).

No API key required. The iRail API provides:
 - Live departure boards per station
 - Journey planner (connections between two stations)
 - Active disruptions and planned works across the network

Three plugin classes are defined here:
  NMBSTimetablePlugin  — departures & connections (receptionist, ticketing)
  NMBSDisruptionsPlugin — disruptions & planned works (disruptions agent)
"""

import datetime
import json
import logging
import urllib.parse
import urllib.request

from semantic_kernel.functions.kernel_function_decorator import kernel_function

logger = logging.getLogger(__name__)

_IRAIL_BASE = "https://api.irail.be"
_USER_AGENT = "NMBS-ContactCenter/1.0"
_TIMEOUT = 10

# Canonical iRail station names for common spoken variants.
# The iRail API resolves ambiguous short names to wrong stations:
#   "Antwerp" -> Antwerp-Haven (port, no passenger trains)
#   "Brussels" -> Brussels-West (few trains)
#   "Ghent"   -> Ghent-Dampoort (not the main intercity hub)
#   "London"  -> London St Pancras (Thalys/Eurostar station — not Belgium)
_STATION_ALIASES: dict[str, str] = {
    # Antwerp
    "antwerp": "Antwerpen-Centraal",
    "antwerpen": "Antwerpen-Centraal",
    "anvers": "Antwerpen-Centraal",
    # Brussels
    "brussels": "Brussel-Centraal",
    "brussels central": "Brussel-Centraal",
    "bruxelles": "Brussel-Centraal",
    "brussel": "Brussel-Centraal",
    "bruxelles-central": "Brussel-Centraal",
    "brussel centraal": "Brussel-Centraal",
    # Ghent
    "ghent": "Gent-Sint-Pieters",
    "gent": "Gent-Sint-Pieters",
    "gand": "Gent-Sint-Pieters",
    # Liege
    "liege": "Liège-Guillemins",
    "liège": "Liège-Guillemins",
    "luik": "Liège-Guillemins",
    "liege guillemins": "Liège-Guillemins",
    # Bruges
    "bruges": "Brugge",
    # Leuven / protect against London mishear
    "london": "Leuven",
    "londen": "Leuven",
}


def _normalize_station(name: str) -> str:
    """Map common spoken station variants to canonical iRail-accepted names."""
    return _STATION_ALIASES.get(name.strip().lower(), name.strip())

# Brussels timezone: UTC+2 in summer (CEST, ~Mar–Oct), UTC+1 in winter (CET).
# We prefer ZoneInfo but fall back gracefully when tzdata is absent (Docker slim images).
try:
    from zoneinfo import ZoneInfo as _ZoneInfo
    _TZ: datetime.tzinfo = _ZoneInfo("Europe/Brussels")
except Exception:
    _month = datetime.datetime.now(datetime.timezone.utc).month
    _TZ = datetime.timezone(datetime.timedelta(hours=2 if 4 <= _month <= 10 else 1))


def _irail_get(path: str, params: dict) -> dict:
    """Make a GET request to the iRail API and return parsed JSON."""
    url = f"{_IRAIL_BASE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # nosec - fixed trusted URL
        return json.loads(resp.read().decode())


def _fmt_time(ts: int) -> str:
    """Format a Unix timestamp as HH:MM in Brussels local time."""
    return datetime.datetime.fromtimestamp(int(ts), tz=_TZ).strftime("%H:%M")


def _fmt_delay(delay_seconds) -> str:
    """Return a human-readable delay string for voice output."""
    secs = int(delay_seconds) if delay_seconds else 0
    if secs == 0:
        return "on time"
    minutes = secs // 60
    return f"{minutes} minute{'s' if minutes != 1 else ''} late"


class NMBSTimetablePlugin:
    """Live departure boards and journey planner for NMBS stations."""

    @kernel_function
    def get_live_departures(self, station: str) -> str:
        """Get the next train departure from a given NMBS/SNCB station.

        Returns ONLY the single next departure. If the caller wants more options,
        call get_more_departures instead.

        Args:
            station: Name of the Belgian railway station (e.g. 'Brussel-Centraal', 'Gent-Sint-Pieters').
        """
        station = _normalize_station(station)
        try:
            data = _irail_get(
                "/liveboard/",
                {"station": station, "format": "json", "lang": "en", "arrdep": "departure"},
            )
        except Exception as exc:
            logger.warning("iRail liveboard request failed: %s", exc)
            return "I'm sorry, I cannot access live departure information right now. Please check the NMBS website or app for the latest times."

        departures = data.get("departures", {}).get("departure", [])
        station_display = data.get("station", station)

        if not departures:
            return f"I don't see any upcoming departures listed for {station_display} at the moment."

        dep = departures[0]
        time_str = _fmt_time(dep["time"])
        dest = dep.get("station", "Unknown")
        platform = dep.get("platform") or "unknown platform"
        if platform == "?":
            platform = "unknown platform"
        train = dep.get("vehicleinfo", {}).get("shortname") or dep.get("vehicle", "")
        delay = _fmt_delay(dep.get("delay", 0))
        total = len(departures)

        # iRail returns "1" (string) for cancelled, "0" for normal
        if str(dep.get("canceled", "0")) == "1":
            result = f"The next train from {station_display} is the {train} to {dest} at {time_str} from platform {platform}, but it is CANCELLED."
        else:
            result = f"The next train from {station_display} is the {train} to {dest} at {time_str} from platform {platform}, {delay}."

        if total > 1:
            result += f" There are {total - 1} more departure{'s' if total - 1 != 1 else ''} available if needed."
        return result

    @kernel_function
    def get_more_departures(self, station: str) -> str:
        """Get the next 4 additional train departures from a station.

        Call this ONLY if the caller explicitly asks for more options after get_live_departures.

        Args:
            station: Name of the Belgian railway station.
        """
        station = _normalize_station(station)
        try:
            data = _irail_get(
                "/liveboard/",
                {"station": station, "format": "json", "lang": "en", "arrdep": "departure"},
            )
        except Exception as exc:
            logger.warning("iRail liveboard request failed: %s", exc)
            return "I'm sorry, I cannot access live departure information right now."

        departures = data.get("departures", {}).get("departure", [])[1:5]
        station_display = data.get("station", station)

        if not departures:
            return f"No further departures found for {station_display}."

        lines = [f"The next departures from {station_display} after that are:"]
        for dep in departures:
            time_str = _fmt_time(dep["time"])
            dest = dep.get("station", "Unknown")
            platform = dep.get("platform") or "unknown platform"
            if platform == "?":
                platform = "unknown platform"
            train = dep.get("vehicleinfo", {}).get("shortname") or dep.get("vehicle", "")
            delay = _fmt_delay(dep.get("delay", 0))
            if str(dep.get("canceled", "0")) == "1":
                lines.append(f"  {time_str} — {train} to {dest}, platform {platform}: CANCELLED")
            else:
                lines.append(f"  {time_str} — {train} to {dest}, platform {platform}, {delay}")
        return "\n".join(lines)

    @kernel_function
    def get_connections(self, origin: str, destination: str) -> str:
        """Find the next train connection between two NMBS/SNCB stations.

        Returns ONLY the single next journey option. If the caller wants more
        alternatives, call get_more_connections instead.

        Args:
            origin: Name of the departure station (e.g. 'Antwerpen-Centraal').
            destination: Name of the arrival station (e.g. 'Luik-Guillemins').
        """
        origin = _normalize_station(origin)
        destination = _normalize_station(destination)
        try:
            data = _irail_get(
                "/connections/",
                {"from": origin, "to": destination, "format": "json", "lang": "en", "results": 4},
            )
        except Exception as exc:
            logger.warning("iRail connections request failed: %s", exc)
            return "I'm sorry, I cannot access journey planning right now. Please check the NMBS website or app."

        connections = data.get("connection", [])
        if not connections:
            return f"I couldn't find any connections from {origin} to {destination} at this time."

        conn = connections[0]
        dep_time = _fmt_time(conn["departure"]["time"])
        arr_time = _fmt_time(conn["arrival"]["time"])
        dep_delay = _fmt_delay(conn["departure"].get("delay", 0))
        duration_min = int(conn.get("duration", 0)) // 60
        vias_block = conn.get("vias") or {}
        changes = int(vias_block.get("number", 0)) if vias_block else 0
        change_str = "direct" if changes == 0 else f"{changes} change{'s' if changes != 1 else ''}"
        total = len(connections)

        result = (
            f"The next train from {origin} to {destination} departs at {dep_time} ({dep_delay}), "
            f"arrives at {arr_time}, taking {duration_min} minutes, {change_str}."
        )
        if total > 1:
            result += f" There are {total - 1} more option{'s' if total - 1 != 1 else ''} if you need alternatives."
        return result

    @kernel_function
    def get_more_connections(self, origin: str, destination: str) -> str:
        """Get up to 3 alternative train connections between two stations.

        Call this ONLY if the caller explicitly asks for more options after get_connections.

        Args:
            origin: Name of the departure station.
            destination: Name of the arrival station.
        """
        origin = _normalize_station(origin)
        destination = _normalize_station(destination)
        try:
            data = _irail_get(
                "/connections/",
                {"from": origin, "to": destination, "format": "json", "lang": "en", "results": 4},
            )
        except Exception as exc:
            logger.warning("iRail connections request failed: %s", exc)
            return "I'm sorry, I cannot access journey planning right now."

        connections = data.get("connection", [])[1:4]
        if not connections:
            return f"No further connections found from {origin} to {destination}."

        lines = ["Here are the next alternatives:"]
        for i, conn in enumerate(connections, 2):
            dep_time = _fmt_time(conn["departure"]["time"])
            arr_time = _fmt_time(conn["arrival"]["time"])
            dep_delay = _fmt_delay(conn["departure"].get("delay", 0))
            duration_min = int(conn.get("duration", 0)) // 60
            vias_block = conn.get("vias") or {}
            changes = int(vias_block.get("number", 0))
            change_str = "direct" if changes == 0 else f"{changes} change{'s' if changes != 1 else ''}"
            lines.append(
                f"  Option {i}: depart {dep_time} ({dep_delay}), arrive {arr_time}, "
                f"{duration_min} minutes, {change_str}"
            )
        return "\n".join(lines)


class NMBSDisruptionsPlugin:
    """Live disruptions and planned engineering works on the NMBS network."""

    @kernel_function
    def get_current_disruptions(self) -> str:
        """Get all current disruptions, delays, and planned works on the NMBS rail network.

        Returns a summary of active incidents (unexpected delays/cancellations) and
        scheduled engineering works. Use this when callers ask about delays, service
        alerts, or whether their line is affected by disruptions.
        """
        try:
            data = _irail_get("/disturbances/", {"format": "json", "lang": "en"})
        except Exception as exc:
            logger.warning("iRail disturbances request failed: %s", exc)
            return "I'm sorry, I cannot access disruption information right now. Please check the NMBS website or app."

        disturbances = data.get("disturbance", [])
        if not disturbances:
            return "Good news — there are no disruptions or planned works reported on the NMBS network at the moment. All services are running normally."

        active = [d for d in disturbances if d.get("type") == "disturbance"]
        planned = [d for d in disturbances if d.get("type") == "planned"]

        lines: list[str] = []

        if active:
            count = len(active)
            lines.append(f"There {'is' if count == 1 else 'are'} currently {count} active disruption{'s' if count != 1 else ''} on the network:")
            for d in active[:3]:
                title = d.get('title', 'Unknown disruption')
                lines.append(f"  - {title}")

        if planned:
            count = len(planned)
            lines.append(f"There {'is' if count == 1 else 'are'} also {count} set of planned engineering works.")
            for d in planned[:2]:
                title = d.get("title", "Planned works")
                lines.append(f"  - {title}")

        return "\n".join(lines)
