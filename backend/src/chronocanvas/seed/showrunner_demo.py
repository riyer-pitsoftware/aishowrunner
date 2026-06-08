"""Seeded historical-noir demo series (PRD §9.3.7).

Loads a single, canon-rich demo series so the three rooms (Story Room, Writers'
Room, Production Desk) have real data to operate on during UAT/demo without any
hand-authoring. It seeds:

  * one active ``Series`` (title / premise / era / creative_rules),
  * a handful of ``CanonFact``s, a few ``Character``s + ``Relationship``s, and a
    couple of open ``StoryThread``s — enough to populate the Story Room canon
    rail and give the historian / narrative skills material to work with,
  * one ``Episode`` parked in ``story_room`` with a 5-beat ``beat_sheet`` (and
    matching ``Beat`` rows) so the Production Desk shot planner
    (``POST /episodes/{id}/plan-shots``) has something to expand.

Canon is sourced by folding the append-only ``CanonMutation`` log, so the
authoritative writes here are mutations via ``CanonService`` (which the
``/series/{id}/canon`` rail reads). The matching snapshot rows in
``canon_facts`` / ``characters`` / ``relationships`` / ``story_threads`` are
written as plain initial creates for code that queries those tables directly —
never updated, to respect the canon immutability discipline.

The historical-noir content lives in the ``DEMO`` dict below as a single,
clearly-labelled data structure so it is easy to edit. The loader is idempotent:
if a series with the demo title already exists it is left untouched and the
existing ``Series`` is returned.

The setting — Vienna, 1948, in the rubble of the four-power occupation — is a
real historical backdrop (the era of "The Third Man"): black-market penicillin,
zonal checkpoints, and a city carved between the Allied powers. It is canon-rich
and tasteful, and serves as evocative material for the period skills.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.db.models.showrunner_episode import Beat, Episode
from chronocanvas.db.models.showrunner_series import (
    CanonFact,
    Character,
    Relationship,
    Series,
    StoryThread,
)
from chronocanvas.showrunner.canon.state import MutationType
from chronocanvas.showrunner.series.service import CanonService

# ── Historical-noir demo content (edit here) ─────────────────────────────────
#
# A 1948 occupied-Vienna noir. Real backdrop: the four-power (US/UK/French/
# Soviet) occupation, the rotating International Sector, and the black market in
# diverted penicillin that defined the post-war city.

PROVENANCE = {"source": "seed:demo", "gate": "seeded", "skill": "seed"}

DEMO: dict = {
    "series": {
        "title": "Vienna, Four Zones",
        "premise": (
            "1948. Vienna lies in rubble, carved into four occupation zones with a "
            "shared International Sector at its heart. An Austrian ex-police inspector, "
            "now a licensed private investigator, works the seams between the powers — "
            "where diverted penicillin, forged zone passes, and old wartime debts are "
            "the only currency that still spends in every sector."
        ),
        "era": "Occupied Vienna, 1948 (four-power occupation)",
        "creative_rules": {
            "tone": "historical noir",
            "visual_style": (
                "high-contrast black-and-white, canted angles, wet cobblestones, "
                "long shadows under sparse streetlamps"
            ),
            "palette": "monochrome with deep blacks and blown highlights",
            "themes": ["divided loyalties", "scarcity", "moral compromise", "rubble and ruin"],
            "constraints": [
                "period-accurate to 1948 Vienna; no anachronistic technology",
                "violence implied, never gratuitous",
            ],
        },
    },
    # Folded into the canon rail (mutations) AND materialized as snapshot rows.
    "facts": [
        {
            "key": "setting.occupation",
            "category": "setting",
            "text": (
                "Vienna is occupied by four powers — the United States, Britain, France, "
                "and the Soviet Union — each holding a zone, with the central districts "
                "governed jointly as the International Sector."
            ),
        },
        {
            "key": "setting.intl_patrol",
            "category": "setting",
            "text": (
                "The International Sector is patrolled by a jeep carrying one military "
                "policeman from each of the four powers — 'the four men in a jeep' — so no "
                "single power can act alone in the city's heart."
            ),
        },
        {
            "key": "economy.penicillin",
            "category": "economy",
            "text": (
                "Penicillin diverted from Allied military hospitals is the city's most "
                "valuable black-market good; cut and resold, it heals or kills depending on "
                "who handled it."
            ),
        },
        {
            "key": "logistics.zone_passes",
            "category": "logistics",
            "text": (
                "Crossing between zones requires papers stamped by the controlling power; "
                "forged or borrowed zone passes are how anyone with business in more than "
                "one sector actually moves."
            ),
        },
        {
            "key": "place.ferris_wheel",
            "category": "place",
            "text": (
                "The great Ferris wheel at the Prater, the Riesenrad, still turns over the "
                "ruined fairground — a neutral, public place to meet where a private cabin "
                "rises above eavesdroppers."
            ),
        },
    ],
    "characters": [
        {
            "key": "leona_vogt",
            "name": "Leona Vogt",
            "slug": "leona-vogt",
            "role": "protagonist",
            "description": (
                "Former inspector of the Vienna criminal police, struck off in the war "
                "years for the wrong refusals; now a licensed private investigator who can "
                "still read a crime scene and still knows which favours are owed."
            ),
            "attributes": {
                "age": 41,
                "languages": ["German", "Russian", "English"],
                "tell": "keeps her late partner's police whistle on her watch-chain",
            },
        },
        {
            "key": "maj_sokolov",
            "name": "Major Andrei Sokolov",
            "slug": "andrei-sokolov",
            "role": "antagonist",
            "description": (
                "Soviet liaison officer for the International Sector — courteous, exact, "
                "and quietly running half the penicillin that leaves the eastern zone."
            ),
            "attributes": {"power": "Soviet", "office": "zone liaison"},
        },
        {
            "key": "felix_brandt",
            "name": "Felix Brandt",
            "slug": "felix-brandt",
            "role": "broker",
            "description": (
                "A genial fixer who trades zone passes and introductions from a back booth "
                "at a café on the sector line; sells to all four powers and loyal to none."
            ),
            "attributes": {"front": "café proprietor"},
        },
        {
            "key": "sister_clara",
            "name": "Sister Clara",
            "slug": "sister-clara",
            "role": "ally",
            "description": (
                "A nursing sister at a half-ruined children's clinic who first noticed the "
                "diluted penicillin when her patients stopped recovering — and who came to "
                "Leona rather than to any occupying power."
            ),
            "attributes": {"affiliation": "St. Anna children's clinic"},
        },
    ],
    "relationships": [
        {
            "key": "vogt_sokolov",
            "from": "leona_vogt",
            "to": "maj_sokolov",
            "kind": "rival",
            "description": (
                "Wary adversaries who each know the other is competent; they trade "
                "information across the zone line precisely because neither fully trusts it."
            ),
        },
        {
            "key": "vogt_clara",
            "from": "leona_vogt",
            "to": "sister_clara",
            "kind": "client",
            "description": (
                "Sister Clara is Leona's conscience and her client — the reason the "
                "penicillin case is personal rather than merely paid."
            ),
        },
    ],
    "threads": [
        {
            "key": "thread.diluted_penicillin",
            "title": "Who is cutting the clinic's penicillin — and how high does the racket reach?",
        },
        {
            "key": "thread.vogts_war_debt",
            "title": "The wartime favour Leona still owes, and who will call it in.",
        },
    ],
    # Demo episode parked in the Story Room with a beat sheet for the shot planner.
    "episode": {
        "number": 1,
        "title": "The Cabin on the Wheel",
        "status": "story_room",
        "premise": (
            "When Sister Clara's children stop responding to their medicine, Leona traces "
            "the diluted penicillin from a clinic ledger to a meeting she is not meant to "
            "survive — high above the Prater, in a cabin of the great Ferris wheel."
        ),
        "beats": [
            {
                "description": "Cold open: a child's fever breaks the wrong way at the clinic.",
                "visual": (
                    "Night interior of a half-ruined children's clinic, single lamp, "
                    "Sister Clara at a cot, high-contrast black-and-white, long shadows."
                ),
            },
            {
                "description": "Leona reads the clinic ledger and finds the doctored supply line.",
                "visual": (
                    "Close on Leona Vogt's hands over a ledger by lamplight, smoke curling, "
                    "rain on a dark window behind her, monochrome noir."
                ),
            },
            {
                "description": "Felix Brandt sells her the name in exchange for a borrowed zone pass.",
                "visual": (
                    "Back booth of a sector-line café, Felix Brandt across the table from "
                    "Leona, wet street visible through the door, deep blacks."
                ),
            },
            {
                "description": "The Riesenrad meeting: Major Sokolov makes his offer above the ruined fairground.",
                "visual": (
                    "Two figures in a Ferris-wheel cabin rising over a ruined Prater "
                    "fairground at dusk, canted angle, city in rubble below."
                ),
            },
            {
                "description": "Leona walks the four-power line home, the racket named but not yet broken.",
                "visual": (
                    "Leona Vogt walking a wet cobblestone street under a sparse streetlamp, "
                    "a four-power patrol jeep passing, long shadow, monochrome."
                ),
            },
        ],
    },
}


def _mt(value: MutationType) -> str:
    return value.value


async def seed_showrunner_demo(session: AsyncSession) -> Series:
    """Idempotently load the historical-noir demo series and return its ``Series``.

    Re-running is a no-op: if a series with the demo title already exists it is
    returned unchanged (canon rows are append-only and must never be rewritten).
    """
    title = DEMO["series"]["title"]

    existing = (
        await session.execute(select(Series).where(Series.title == title))
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    svc = CanonService(session)
    series = await svc.create_series(
        title=title,
        premise=DEMO["series"]["premise"],
        era=DEMO["series"]["era"],
        creative_rules=DEMO["series"]["creative_rules"],
    )
    series.status = "active"
    await session.flush()

    # ── Canon facts: append to the mutation log AND materialize a snapshot row.
    for fact in DEMO["facts"]:
        await svc.append_mutation(
            series_id=series.id,
            mutation_type=_mt(MutationType.ADD_FACT),
            target_type="fact",
            target_key=fact["key"],
            payload={"category": fact["category"], "text": fact["text"]},
            provenance=PROVENANCE,
            source_skill="seed",
        )
        session.add(
            CanonFact(
                series_id=series.id,
                fact_key=fact["key"],
                category=fact["category"],
                text=fact["text"],
                status="active",
                provenance=PROVENANCE,
            )
        )

    # ── Characters: mutation + snapshot row (keyed by slug for lookups).
    char_ids: dict[str, uuid.UUID] = {}
    for char in DEMO["characters"]:
        await svc.append_mutation(
            series_id=series.id,
            mutation_type=_mt(MutationType.ADD_CHARACTER),
            target_type="character",
            target_key=char["key"],
            payload={
                "name": char["name"],
                "slug": char["slug"],
                "role": char["role"],
                "description": char["description"],
                "attributes": char["attributes"],
            },
            provenance=PROVENANCE,
            source_skill="seed",
        )
        row = Character(
            series_id=series.id,
            name=char["name"],
            slug=char["slug"],
            role=char["role"],
            description=char["description"],
            attributes=char["attributes"],
        )
        session.add(row)
        await session.flush()
        char_ids[char["key"]] = row.id

    # ── Relationships: mutation + snapshot row (resolve character ids by key).
    for rel in DEMO["relationships"]:
        await svc.append_mutation(
            series_id=series.id,
            mutation_type=_mt(MutationType.SET_RELATIONSHIP),
            target_type="relationship",
            target_key=rel["key"],
            payload={
                "from": rel["from"],
                "to": rel["to"],
                "kind": rel["kind"],
                "description": rel["description"],
            },
            provenance=PROVENANCE,
            source_skill="seed",
        )
        session.add(
            Relationship(
                series_id=series.id,
                from_character_id=char_ids[rel["from"]],
                to_character_id=char_ids[rel["to"]],
                kind=rel["kind"],
                description=rel["description"],
                status="active",
            )
        )

    # ── Open story threads: mutation + snapshot row.
    for thread in DEMO["threads"]:
        await svc.append_mutation(
            series_id=series.id,
            mutation_type=_mt(MutationType.OPEN_THREAD),
            target_type="thread",
            target_key=thread["key"],
            payload={"title": thread["title"]},
            provenance=PROVENANCE,
            source_skill="seed",
        )
        session.add(
            StoryThread(
                series_id=series.id,
                thread_key=thread["key"],
                title=thread["title"],
                status="open",
            )
        )

    # ── Demo episode + beat sheet (drives the shot planner).
    ep_data = DEMO["episode"]
    beat_sheet = {
        "beats": [
            {"index": i, "description": b["description"], "visual": b["visual"]}
            for i, b in enumerate(ep_data["beats"])
        ]
    }
    episode = Episode(
        series_id=series.id,
        number=ep_data["number"],
        title=ep_data["title"],
        premise=ep_data["premise"],
        status=ep_data["status"],
        active_room="story_room",
        beat_sheet=beat_sheet,
    )
    session.add(episode)
    await session.flush()

    for i, beat in enumerate(ep_data["beats"]):
        session.add(
            Beat(
                episode_id=episode.id,
                index=i,
                description=beat["description"],
                payload={"visual": beat["visual"]},
            )
        )

    await session.flush()
    return series
