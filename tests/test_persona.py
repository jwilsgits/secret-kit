import re
import unittest
from datetime import date

from engine.charset import CharsetError
from engine.entropy import ByteSource
from engine.persona import (
    area_codes,
    first_female,
    first_male,
    generate_persona,
    last_names,
    places,
)


def src():
    return ByteSource(bytes((i * 13 + 7) % 256 for i in range(4096)))


ALL_FIELDS = {
    "name": True,
    "dob": True,
    "gender": True,
    "street": True,
    "location": True,
    "phone": True,
    "username": True,
}

TOLL_FREE = {"800", "822", "833", "844", "855", "866", "877", "888"}
PREMIUM = {"900"}
NON_GEO = {"500", "521", "522", "533", "544", "555", "566", "577", "588", "600", "700", "710"}
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO",
    "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA",
    "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
}


def parse_block(text):
    out = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def completed_age(dob, today=None):
    today = today or date.today()
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return years


class PersonaListTests(unittest.TestCase):
    def test_name_list_floors_and_unique(self):
        male = first_male()
        female = first_female()
        surnames = last_names()
        self.assertGreaterEqual(len(male), 512)
        self.assertGreaterEqual(len(female), 512)
        self.assertGreaterEqual(len(surnames), 2048)
        self.assertEqual(len(male), len(set(male)))
        self.assertEqual(len(female), len(set(female)))
        self.assertEqual(len(surnames), len(set(surnames)))

    def test_area_codes_shape_and_no_non_geo(self):
        rows = area_codes()
        self.assertGreaterEqual(len(rows), 300)
        npas = []
        for npa, st, city in rows:
            self.assertRegex(npa, r"^[2-9]\d{2}$")
            self.assertTrue(st == "DC" or re.fullmatch(r"[A-Z]{2}", st))
            self.assertIn(st, US_STATES)
            self.assertTrue(city)
            self.assertNotIn(npa, TOLL_FREE)
            self.assertNotIn(npa, PREMIUM)
            self.assertNotIn(npa, NON_GEO)
            self.assertRegex(city, r"^[A-Za-z][A-Za-z .'\-]+$")
            self.assertLessEqual(len(city), 40)
            self.assertNotRegex(city.lower(), r"\b(including|except|portions|counties)\b")
            npas.append(npa)
        self.assertEqual(len(npas), len(set(npas)))
        canada = {
            "204", "226", "236", "249", "250", "257", "263", "289", "306", "343",
            "354", "365", "367", "368", "382", "387", "403", "416", "418", "428",
            "431", "437", "438", "450", "468", "474", "506", "514", "519", "548",
            "579", "581", "584", "587", "604", "613", "639", "647", "672", "683",
            "705", "709", "742", "753", "778", "780", "782", "807", "819", "825",
            "873", "879", "902", "905", "942",
        }
        self.assertTrue(canada.isdisjoint(npas))

    def test_places_npa_matches_area_codes_and_covers_states(self):
        npa_st = {(npa, st) for npa, st, _city in area_codes()}
        found = set()
        for city, st, zip_code, npa in places():
            self.assertTrue(city)
            self.assertRegex(zip_code, r"^\d{5}$")
            self.assertIn((npa, st), npa_st)
            found.add(st)
        self.assertEqual(found, US_STATES)


class PersonaGenerateTests(unittest.TestCase):
    def test_full_random_all_fields(self):
        value = generate_persona(
            src(),
            {"mode": "full", "gender": "any", "age": "any", "fields": ALL_FIELDS},
        )
        block = parse_block(value)
        self.assertEqual(
            set(block),
            {"Full name", "Date of birth", "Gender", "Street", "City", "State", "ZIP", "Phone", "Username"},
        )
        self.assertNotRegex(value, r"(?i)^\s*email\s*:", re.M)
        self.assertIn(block["Gender"], ("male", "female"))
        first, last = block["Full name"].split(" ", 1)
        if block["Gender"] == "male":
            self.assertIn(first, first_male())
        else:
            self.assertIn(first, first_female())
        self.assertIn(last, last_names())
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2}) \((\d+) years old\)", block["Date of birth"])
        self.assertIsNotNone(m)
        dob = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        age = int(m.group(4))
        self.assertEqual(age, completed_age(dob))
        self.assertGreaterEqual(age, 18)
        self.assertLessEqual(age, 75)
        phone = re.fullmatch(r"\((\d{3})\) 555-(\d{4})", block["Phone"])
        self.assertIsNotNone(phone)
        npa = phone.group(1)
        matches = [
            row
            for row in places()
            if row[0] == block["City"] and row[1] == block["State"] and row[2] == block["ZIP"]
        ]
        self.assertTrue(matches)
        self.assertIn(npa, {row[3] for row in matches})
        self.assertEqual(block["State"], matches[0][1])

    def test_phone_only_npa_from_area_codes(self):
        fields = dict(ALL_FIELDS)
        for key in fields:
            fields[key] = key == "phone"
        value = generate_persona(src(), {"mode": "full", "fields": fields})
        block = parse_block(value)
        self.assertEqual(set(block), {"Phone"})
        npa = re.fullmatch(r"\((\d{3})\) 555-\d{4}", block["Phone"]).group(1)
        self.assertIn(npa, {row[0] for row in area_codes()})

    def test_subset_name_and_dob_only(self):
        fields = {k: k in ("name", "dob") for k in ALL_FIELDS}
        value = generate_persona(src(), {"mode": "full", "fields": fields})
        self.assertEqual(set(parse_block(value)), {"Full name", "Date of birth"})
        self.assertNotIn("Phone:", value)
        self.assertNotIn("Gender:", value)

    def test_partial_male_first_name(self):
        fields = {k: k == "name" for k in ALL_FIELDS}
        value = generate_persona(
            src(),
            {"mode": "partial", "gender": "male", "age": "any", "fields": fields},
        )
        first = parse_block(value)["Full name"].split(" ", 1)[0]
        self.assertIn(first, first_male())

    def test_partial_age_target_window(self):
        fields = {k: k == "dob" for k in ALL_FIELDS}
        value = generate_persona(
            src(),
            {"mode": "partial", "gender": "any", "age": 43, "fields": fields},
        )
        m = re.fullmatch(
            r"(\d{4})-(\d{2})-(\d{2}) \((\d+) years old\)",
            parse_block(value)["Date of birth"],
        )
        age = int(m.group(4))
        self.assertGreaterEqual(age, 41)
        self.assertLessEqual(age, 45)
        dob = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        self.assertEqual(age, completed_age(dob))

    def test_empty_fields_error(self):
        fields = {k: False for k in ALL_FIELDS}
        with self.assertRaises(CharsetError):
            generate_persona(src(), {"mode": "full", "fields": fields})

    def test_no_email_key(self):
        value = generate_persona(
            src(),
            {"mode": "full", "fields": ALL_FIELDS},
        )
        self.assertNotRegex(value, r"(?i)^\s*email\s*:", re.M)
        self.assertNotIn("@", value)


if __name__ == "__main__":
    unittest.main()
