"""Explainable content-based recommendations shared by two public APIs."""
import csv
import math
from dataclasses import dataclass, asdict, fields
from pathlib import Path


@dataclass(frozen=True)
class Song:
    """A track and its descriptive and numerical audio features."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass(frozen=True)
class UserProfile:
    """Explicit user preferences rather than inferred listening behavior."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


@dataclass(frozen=True)
class ScoreWeights:
    """Configurable nonnegative scoring weights."""
    genre: float = 2.0
    mood: float = 1.0
    energy: float = 1.0
    acoustic: float = 0.5

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f'{field.name} weight must be finite and nonnegative')


def _number(value, name, low=0, high=1):
    """Validate a numerical feature and return it as a float."""
    if isinstance(value, bool):
        raise ValueError(f'{name} must be a number')
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{name} must be a number') from exc
    if not math.isfinite(result) or not low <= result <= high:
        raise ValueError(f'{name} must be between {low} and {high}')
    return result


def _label(value, name):
    """Normalize nonempty labels for comparison."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be a nonempty string')
    return value.strip().casefold()


def load_songs(csv_path: str | Path) -> list[dict]:
    """Read a CSV catalog, validate its schema, and convert numeric features."""
    songs, seen = [], set()
    with open(csv_path, newline='', encoding='utf-8-sig') as source:
        reader = csv.DictReader(source)
        required = {field.name for field in fields(Song)}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'CSV missing required columns: {sorted(missing)}')
        for line, row in enumerate(reader, 2):
            try:
                song = {name: row[name] for name in required}
                song['id'] = int(song['id'])
                if song['id'] <= 0 or song['id'] in seen:
                    raise ValueError('IDs must be positive and unique')
                for name in ('title', 'artist', 'genre', 'mood'):
                    _label(song[name], name)
                    song[name] = song[name].strip()
                for name in ('energy', 'valence', 'danceability', 'acousticness'):
                    song[name] = _number(song[name], name)
                song['tempo_bpm'] = _number(song['tempo_bpm'], 'tempo_bpm', 1, 400)
            except (TypeError, ValueError) as exc:
                raise ValueError(f'Invalid CSV row {line}: {exc}') from exc
            seen.add(song['id'])
            songs.append(song)
    return songs


def score_song(user_prefs: dict, song: dict, weights: ScoreWeights | None = None) -> tuple[float, list[str]]:
    """Return weighted relevance and reasons for each score component."""
    weights = weights or ScoreWeights()
    genre = _label(user_prefs.get('favorite_genre', user_prefs.get('genre')), 'genre preference')
    mood = _label(user_prefs.get('favorite_mood', user_prefs.get('mood')), 'mood preference')
    target = _number(user_prefs.get('target_energy', user_prefs.get('energy')), 'target energy')
    genre_match = genre == _label(song.get('genre'), 'song genre')
    mood_match = mood == _label(song.get('mood'), 'song mood')
    genre_points = weights.genre * genre_match
    mood_points = weights.mood * mood_match
    similarity = 1 - abs(_number(song.get('energy'), 'song energy') - target)
    energy_points = weights.energy * similarity
    reasons = [f"genre {'match' if genre_match else 'no match'} (+{genre_points:.2f})",
               f"mood {'match' if mood_match else 'no match'} (+{mood_points:.2f})",
               f'energy similarity {similarity:.2f} (+{energy_points:.2f})']
    total = genre_points + mood_points + energy_points
    if 'likes_acoustic' in user_prefs:
        likes = user_prefs['likes_acoustic']
        if not isinstance(likes, bool):
            raise ValueError('likes_acoustic must be a boolean')
        acousticness = _number(song.get('acousticness'), 'song acousticness')
        points = weights.acoustic * (acousticness if likes else 1 - acousticness)
        total += points
        reasons.append(f"{'acoustic' if likes else 'non-acoustic'} preference (+{points:.2f})")
    return total, reasons


def recommend_songs(user_prefs: dict, songs: list[dict], k: int = 5,
                    weights: ScoreWeights | None = None) -> list[tuple[dict, float, str]]:
    """Rank every song by descending score, keeping catalog order for ties."""
    if isinstance(k, bool) or not isinstance(k, int) or k < 0:
        raise ValueError('k must be a nonnegative integer')
    ranked = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, weights)
        ranked.append((song, score, '; '.join(reasons)))
    return sorted(ranked, key=lambda item: item[1], reverse=True)[:k]


class Recommender:
    """Object-oriented adapter using the functional API's scoring rules."""
    def __init__(self, songs: list[Song], weights: ScoreWeights | None = None):
        self.songs = list(songs)
        self.weights = weights or ScoreWeights()

    def recommend(self, user: UserProfile, k: int = 5) -> list[Song]:
        """Return the highest-scoring tracks for this user."""
        return [Song(**song) for song, _, _ in recommend_songs(
            asdict(user), [asdict(song) for song in self.songs], k, self.weights)]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Explain the same score components used to rank the song."""
        return '; '.join(score_song(asdict(user), asdict(song), self.weights)[1])
