from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path
import re

from engine.charset import CharsetError

DATA = Path(__file__).resolve().parent.parent / "data" / "persona"
FIELD_KEYS = ("name", "dob", "gender", "street", "location", "phone", "username")
TOLL_FREE = {"800", "822", "833", "844", "855", "866", "877", "888"}
NON_GEO = {"500", "521", "522", "533", "544", "555", "566", "577", "588", "600", "700", "710", "900"}
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO",
    "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA",
    "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
}

_LINES = {}
_AREA = None
_PLACES = None


def _raw_lines(filename, minimum=None):
    key = (filename, minimum)
    if key in _LINES:
        return _LINES[key]
    path = DATA / filename
    rows = []
    seen = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line in seen:
            raise RuntimeError("%s contains duplicate entry %r" % (filename, line))
        seen.add(line)
        rows.append(line)
    if minimum is not None and len(rows) < minimum:
        raise RuntimeError(
            "%s must contain at least %d unique entries, found %d"
            % (filename, minimum, len(rows))
        )
    _LINES[key] = rows
    return rows


def first_male():
    return _raw_lines("first_male.txt", 512)


def first_female():
    return _raw_lines("first_female.txt", 512)


def last_names():
    return _raw_lines("last.txt", 2048)


def streets():
    return _raw_lines("streets.txt")


def area_codes():
    global _AREA
    if _AREA is not None:
        return _AREA
    rows = []
    seen = set()
    for line in _raw_lines("area_codes.txt"):
        parts = line.split("|")
        if len(parts) != 3:
            raise RuntimeError("area_codes.txt row must be NPA|ST|city: %s" % line)
        npa, st, city = (p.strip() for p in parts)
        if not re.fullmatch(r"[2-9]\d{2}", npa):
            raise RuntimeError("invalid NPA in area_codes.txt: %s" % npa)
        if st not in US_STATES:
            raise RuntimeError("invalid ST in area_codes.txt: %s" % st)
        if not city:
            raise RuntimeError("missing city for NPA %s" % npa)
        if npa in TOLL_FREE or npa in NON_GEO:
            raise RuntimeError("non-geographic NPA in area_codes.txt: %s" % npa)
        if npa in seen:
            raise RuntimeError("duplicate NPA in area_codes.txt: %s" % npa)
        seen.add(npa)
        rows.append((npa, st, city))
    if len(rows) < 300:
        raise RuntimeError("area_codes.txt must list at least 300 NPAs, found %d" % len(rows))
    _AREA = rows
    return _AREA


def places():
    global _PLACES
    if _PLACES is not None:
        return _PLACES
    allowed = {(npa, st) for npa, st, _city in area_codes()}
    rows = []
    found = set()
    for line in _raw_lines("places.txt"):
        parts = line.split("|")
        if len(parts) != 4:
            raise RuntimeError("places.txt row must be City|ST|ZIP|NPA: %s" % line)
        city, st, zip_code, npa = (p.strip() for p in parts)
        if not city:
            raise RuntimeError("missing city in places.txt: %s" % line)
        if st not in US_STATES:
            raise RuntimeError("invalid ST in places.txt: %s" % st)
        if not re.fullmatch(r"\d{5}", zip_code):
            raise RuntimeError("invalid ZIP in places.txt: %s" % zip_code)
        if (npa, st) not in allowed:
            raise RuntimeError("places.txt NPA %s does not match area_codes.txt for %s" % (npa, st))
        rows.append((city, st, zip_code, npa))
        found.add(st)
    if found != US_STATES:
        missing = ", ".join(sorted(US_STATES - found))
        raise RuntimeError("places.txt must cover every state and DC; missing %s" % missing)
    _PLACES = rows
    return _PLACES


def _enabled_fields(fields):
    enabled = {key: bool((fields or {}).get(key)) for key in FIELD_KEYS}
    if not any(enabled.values()):
        raise CharsetError("select at least one persona field")
    return enabled


def _age_range(mode, age):
    if mode == "full" or age in (None, "", "any"):
        return 18, 75
    try:
        target = int(age)
    except (TypeError, ValueError):
        raise CharsetError("age must be any or an integer")
    if target < 18 or target > 90:
        raise CharsetError("age target must be 18-90")
    return max(18, target - 2), target + 2


def _add_years(day, years):
    year = day.year + years
    try:
        return day.replace(year=year)
    except ValueError:
        last = monthrange(year, day.month)[1]
        return day.replace(year=year, day=min(day.day, last))


def _random_dob(source, min_age, max_age, today):
    oldest = _add_years(today, -(max_age + 1)) + timedelta(days=1)
    youngest = _add_years(today, -min_age)
    span = (youngest - oldest).days
    if span < 0:
        raise CharsetError("invalid age range")
    return oldest + timedelta(days=source.randbelow(span + 1))


def _completed_age(dob, today):
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return years


def _slug(text):
    text = text.lower().replace("'", "")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def generate_persona(source, spec):
    spec = spec or {}
    mode = spec.get("mode") or "full"
    if mode not in ("full", "partial"):
        raise CharsetError("persona mode must be full or partial")
    enabled = _enabled_fields(spec.get("fields"))
    today = date.today()

    gender = spec.get("gender") or "any"
    if mode == "partial" and gender in ("female", "male"):
        picked_gender = gender
    else:
        picked_gender = source.choice(("female", "male"))

    first = source.choice(first_female() if picked_gender == "female" else first_male())
    last = source.choice(last_names())
    min_age, max_age = _age_range(mode, spec.get("age"))
    dob = _random_dob(source, min_age, max_age, today)
    age = _completed_age(dob, today)
    street = "%d %s" % (100 + source.randbelow(9900), source.choice(streets()))
    place = source.choice(places())
    area = source.choice(area_codes())
    if enabled["location"]:
        npa = place[3]
    else:
        npa = area[0]
    last4 = source.randbelow(10000)
    username = "%s_%s_%04d" % (_slug(first), _slug(last), source.randbelow(10000))

    lines = []
    if enabled["name"]:
        lines.append("Full name: %s %s" % (first, last))
    if enabled["dob"]:
        lines.append("Date of birth: %s (%d years old)" % (dob.isoformat(), age))
    if enabled["gender"]:
        lines.append("Gender: %s" % picked_gender)
    if enabled["street"]:
        lines.append("Street: %s" % street)
    if enabled["location"]:
        lines.append("City: %s" % place[0])
        lines.append("State: %s" % place[1])
        lines.append("ZIP: %s" % place[2])
    if enabled["phone"]:
        lines.append("Phone: (%s) 555-%04d" % (npa, last4))
    if enabled["username"]:
        lines.append("Username: %s" % username)
    return "\n".join(lines)
