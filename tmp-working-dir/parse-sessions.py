#!/usr/bin/env python3

import csv
import sys

from argparse import ArgumentParser
from datetime import datetime
from inspect import cleandoc
from pathlib import Path

from pydantic import BaseModel

parser = ArgumentParser(prog="csv-to-md",
                        description="Parses a Summit Session Catalog CSV and turns it into a markdown document")
parser.add_argument('source', help='The path to the CSV file', default='session-catalog.csv')
parser.add_argument('--output', '-o', help='The path to a markdown document to write (defaults to stdout)')
args = parser.parse_args()

source = Path(args.source)
if not source.exists():
    raise FileNotFoundError(f"Source needs to be a valid path, got: {source}")

with open(source, newline='') as f:
    reader = csv.DictReader(f)
    data = [row for row in reader]

class Session:
    def __init__(self, s: dict) -> None:
        self.id = s.get("Session ID") or None
        self.type = ', '.join(s.get("Session type").split(',')) or None
        self.title = s.get("Title") or None
        self.industry = s.get("Industry") or "All industries"
        self.audience = s.get("Audience") or None
        self.personas = s.get("Persona", "").split(",")
        self.link = s.get("Catalog link ") or s.get("Catalog link") or None
        self.abstract = s.get("Abstract") or None
        self.track = s.get("Track") or None
        self.proficiency = s.get("Technical proficiency") or None

        self.times = []
        self.add_session(s)
        self.speakers = []
        for speakerno in range(1, 6):
            speakername = s.get(f"Speaker {speakerno}") or None
            if speakername is not None:
                self.speakers.append(speakername.split('-')[0])
        self.products = []
        if s.get("Primary Product"):
            self.products.append(s.get("Primary Product"))
        self.products.extend([p for p in s.get("Additional products").split(",") if p])
        self.topics = []
        if s.get("Primary topic"):
            self.topics.append(s.get("Primary topic"))
        self.topics.extend([t for t in s.get("Additional topics").split(",") if t])

    def add_session(self, s: dict) -> None:
        self.times.append(self._parsetime(s.get("Date") or None, s.get("Time") or None))

    @staticmethod
    def _parsetime(date: str | None, time: str | None) -> datetime | None:
        try:
            if date is None:
                return datetime.strptime(f"{date}", "%m/%d/%Y")
            if time is None:
                return datetime.strptime(f"{time}", "%H:%M %p")
            return datetime.strptime(f"{date} {time}", "%m/%d/%Y %H:%M %p")
        except:
            return None

    @staticmethod
    def _ljoin(l: list) -> str:
        if len(l) > 2:
            return ', '.join(l[:-1]) + ", and " + str(l[-1])
        elif len(l) == 2:
            return ' and '.join(l)
        elif len(l) == 1:
            return l[0] or ''
        else:
            return ''

    def get(self, attr: str) -> str:
        value = getattr(self, attr)
        if isinstance(value, list):
            if len(value) == 0:
                ret = f"<No {attr} provided>"
            elif isinstance(value[0], datetime):
                ret = self._ljoin([dt.strftime('%a %d %b %Y, %I:%M%p') for dt in value if dt is not None])
            else:
                ret = self._ljoin(value)
        elif isinstance(value, str):
            ret = value
        elif isinstance(value, datetime):
            ret = value.strftime()
        else:
            ret = f"<No {attr} provided>"
        return " ".join(ret.split())

    def render(self) -> str:
        return cleandoc(f"""
        {self.get("title")} ({self.get("id")}) - {self.get("type")}
        ===

        Session link: {self.get("link")}

        Speakers
        ---

        {self.get("speakers")}

        Track
        ---

        {self.get("track")}

        Topics
        ---

        {self.get("topics")}

        Session times
        ---

        {self.get("times")}

        Audience
        ---

        Audience: {self.get("audience")}

        Industry: {self.get("industry")}

        Personas: {self.get("personas")}

        Proficiency: {self.get("proficiency")}

        Products
        ---

        {self.get("products")}

        Abstract
        ---

        {self.get("abstract").replace("\n", " ")}
        """)


sessions: dict[Session] = {}

for session in data:
    id = session.get("Session ID")
    if id is not None:
        if sessions.get(id) is None:
            sessions[id] = Session(session)
        else:
            sessions[id].add_session(session)

if args.output is not None:
    output = open(args.output, 'w')
else:
    output = sys.stdout

for session in sessions.values():
    output.write(session.render())
    output.write("\n\n")
    output.flush()
