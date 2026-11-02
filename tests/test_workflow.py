"""Behavioral tests for catalog loading, ranking, explanations, and the CLI."""
import csv
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from src.main import PROFILES
from src.recommender import (Recommender, ScoreWeights, Song, UserProfile,
                             load_songs, recommend_songs, score_song)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def songs():
    return load_songs(ROOT / 'data/songs.csv')


def test_catalog_types_and_expansion(songs):
    assert len(songs) == 18
    assert len({s['id'] for s in songs}) == 18
    assert all(isinstance(s['id'], int) and isinstance(s['energy'], float) for s in songs)
    assert len({s['genre'] for s in songs}) == 14


@pytest.mark.parametrize('name,title', [
    ('High-Energy Pop', 'Sunrise City'), ('Chill Lofi', 'Library Rain'),
    ('Deep Intense Rock', 'Storm Runner'), ('Conflicting Pop', 'Velvet Goodbye'),
    ('Unknown Genre', 'Spacewalk Thoughts')])
def test_profile_rankings(songs, name, title):
    results = recommend_songs(PROFILES[name], list(reversed(songs)))
    assert results[0][0]['title'] == title
    assert len(results) == 5
    assert [r[1] for r in results] == sorted([r[1] for r in results], reverse=True)


def test_score_math_and_explanations(songs):
    score, reasons = score_song(PROFILES['High-Energy Pop'], songs[0])
    assert score == pytest.approx(3.98)
    assert len(reasons) == 3
    assert 'genre match (+2.00)' in reasons
    assert 'energy similarity 0.98 (+0.98)' in reasons
    assert score_song({'genre': ' POP ', 'mood': 'HAPPY', 'energy': 0.8}, songs[0])[0] == score


def test_energy_rewards_closeness(songs):
    prefs = {'genre': 'absent', 'mood': 'absent', 'energy': 0.5}
    assert score_song(prefs, dict(songs[0], energy=0.5))[0] == 1
    assert score_song(prefs, dict(songs[0], energy=0))[0] == 0.5
    assert score_song(prefs, dict(songs[0], energy=1))[0] == 0.5


def test_shared_apis_and_acoustic_preference(songs):
    user = UserProfile('pop', 'happy', 0.8, True)
    model = Recommender([Song(**s) for s in reversed(songs)])
    expected = recommend_songs(asdict(user), list(reversed(songs)))
    assert [s.id for s in model.recommend(user)] == [r[0]['id'] for r in expected]
    assert model.explain_recommendation(user, model.recommend(user)[0]) == expected[0][2]
    base = dict(songs[0], acousticness=0.8)
    assert score_song(asdict(user), base)[0] == pytest.approx(4.38)
    assert score_song(dict(asdict(user), likes_acoustic=False), base)[0] == pytest.approx(4.08)


def test_stable_ties_and_no_mutation(songs):
    pair = [songs[0], dict(songs[0], id=99)]
    before = [dict(s) for s in pair]
    assert [r[0]['id'] for r in recommend_songs(PROFILES['High-Energy Pop'], pair)] == [1, 99]
    assert pair == before
    assert recommend_songs(PROFILES['Chill Lofi'], songs, 0) == []
    assert recommend_songs(PROFILES['Chill Lofi'], [], 5) == []
    assert len(recommend_songs(PROFILES['Chill Lofi'], songs, 100)) == len(songs)


@pytest.mark.parametrize('k', [-1, 1.5, True])
def test_invalid_k(songs, k):
    with pytest.raises(ValueError, match='k must'):
        recommend_songs(PROFILES['Chill Lofi'], songs, k)


@pytest.mark.parametrize('energy', [-0.1, 1.1, float('nan'), float('inf'), None, True])
def test_invalid_preferences(songs, energy):
    with pytest.raises(ValueError):
        score_song(dict(PROFILES['Chill Lofi'], energy=energy), songs[0])


@pytest.mark.parametrize('value', [-1, float('nan'), float('inf'), True])
def test_invalid_weights(value):
    with pytest.raises(ValueError):
        ScoreWeights(energy=value)


def test_csv_errors(tmp_path, songs):
    path = tmp_path / 'songs.csv'
    path.write_text('title\nExample\n')
    with pytest.raises(ValueError, match='missing required columns'):
        load_songs(path)
    for rows in ([dict(songs[0], energy='bad')], [songs[0], songs[0]]):
        with path.open('w', newline='') as output:
            writer = csv.DictWriter(output, fieldnames=list(songs[0]))
            writer.writeheader()
            writer.writerows(rows)
        with pytest.raises(ValueError, match='Invalid CSV row'):
            load_songs(path)
    with pytest.raises(FileNotFoundError):
        load_songs(tmp_path / 'missing.csv')


def test_experiment_changes_rankings(songs):
    weights = ScoreWeights(genre=1, energy=2)
    assert recommend_songs(PROFILES['Conflicting Pop'], songs, weights=weights)[0][0]['title'] == 'Gym Hero'
    assert recommend_songs(PROFILES['High-Energy Pop'], songs, weights=weights)[1][0]['title'] == 'Rooftop Lights'


def test_cli_from_module_and_other_directory(tmp_path):
    module = subprocess.run([sys.executable, '-m', 'src.main'], cwd=ROOT, capture_output=True, text=True, check=True)
    assert 'Loaded songs: 18' in module.stdout
    assert '1. Sunrise City — 3.98' in module.stdout
    assert '1. Library Rain — 4.00' in module.stdout
    script = subprocess.run([sys.executable, str(ROOT / 'src/main.py'), '--profile', 'Conflicting Pop', '--experiment'],
                            cwd=tmp_path, capture_output=True, text=True, check=True)
    assert '1. Gym Hero — 2.96' in script.stdout
    bad = subprocess.run([sys.executable, '-m', 'src.main', '--k', '-1'], cwd=ROOT, capture_output=True, text=True)
    assert bad.returncode != 0
    assert '--k must be nonnegative' in bad.stderr
