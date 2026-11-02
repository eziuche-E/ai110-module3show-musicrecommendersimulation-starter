# Music Recommender Simulation — VibeFinder 1.0

A CLI-first, explainable content-based recommender. It loads 18 fictional tracks,
compares them with explicit taste profiles, and prints the top five with scores
and reasons. It is a classroom simulation, not a trained predictive model.

## Getting Started

Use Python 3.12 (validated). From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.main
python -m pytest -q
```

On Windows PowerShell, activate with `.\.venv\Scripts\Activate.ps1`.
No API keys, external services, or music downloads are needed. Dependencies are
currently unpinned in the starter requirements; installations can vary over time.
The CLI itself uses the Python standard library. Pandas and Streamlit remain
available from the starter requirements; this project does not include a web UI.

```bash
python -m src.main --profile "Chill Lofi" --k 3
python -m src.main --experiment
python src/main.py
```

The module command runs from the repository root. The script also resolves the
catalog correctly when launched from another directory. `--k 0` returns no tracks;
negative counts are rejected.

## How The System Works

Large platforms can combine collaborative filtering (similar listeners' plays,
likes, skips, and playlists) with content-based filtering (properties of items).
Listening duration, repeats, and context can also inform predictions. Behavior is
an imperfect signal: a skip may reflect context rather than dislike. These are
general techniques, not claims about a platform's current proprietary algorithm.
This simulation uses content-based filtering only; it has no listening histories.

`Song` stores id, title, artist, genre, mood, energy, tempo_bpm, valence,
danceability, and acousticness. `UserProfile` stores favorite_genre,
favorite_mood, target_energy, and likes_acoustic. The dictionary API also accepts
genre, mood, and energy; acoustic preference is optional. Labels compare without
case or surrounding-space differences. Energy and the other normalized numeric
features must be finite values from 0 to 1; tempo must be 1–400 BPM.

### Algorithm Recipe

- Genre match: +2 points.
- Mood match: +1 point.
- Energy similarity: `1 - abs(song_energy - target_energy)`, worth up to 1 point.
- When acoustic preference is supplied: add `0.5 * acousticness` for acoustic,
  or `0.5 * (1 - acousticness)` for non-acoustic. Omitted preference adds nothing.

Energy rewards closeness, not simply high energy. The usual score ranges from
0 to 4, or 0 to 4.5 with acoustic preference. Scores are relevance points, not
probabilities. Tempo, valence, and danceability are loaded but not scored; keeping
the recipe small makes its tradeoffs easier to explain.

The scoring rule judges one song and returns a number plus component reasons.
The ranking rule scores every song, uses `sorted()` to create a new ranked list,
and returns the top k. In contrast, `.sort()` mutates a list and returns None.
Ties keep CSV order; no random tie breaking or diversity reranking is used.
Both functional and object-oriented APIs share the same recipe.

```text
CSV → validated song dictionaries ─┐
                                 ├→ score every song → sort descending → top k + reasons
Taste profile + scoring weights ─┘
```

Genre has more influence than mood or energy, so exact genre labels can crowd out
songs that fit a user's mood better. The pop profile's low-energy sad track ranks
above a happy indie pop track under the baseline recipe. This is a design tradeoff
and a potential filter bubble, not evidence that the user will prefer that track.

## Data

The original 10 tracks are retained. Eight AI-generated fictional tracks add
classical, soul, electronic, folk, hip hop, world, and metal examples, plus sad pop.
The resulting 18-track catalog has 14 genre labels. Feature values are illustrative,
not measured audio characteristics or licensed recordings. The broad `world` label
is especially coarse and would need more specific, culturally informed labeling.

## Sample Recommendation Output

Actual output from `python -m src.main` (three core profiles and two edge cases):

```text
Loaded songs: 18
Weights: genre=2.0, mood=1.0, energy=1.0

High-Energy Pop: genre=pop, mood=happy, energy=0.8
1. Sunrise City — 3.98
   Because: genre match (+2.00); mood match (+1.00); energy similarity 0.98 (+0.98)
2. Gym Hero — 2.87
   Because: genre match (+2.00); mood no match (+0.00); energy similarity 0.87 (+0.87)
3. Velvet Goodbye — 2.50
   Because: genre match (+2.00); mood no match (+0.00); energy similarity 0.50 (+0.50)
4. Rooftop Lights — 1.96
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.96 (+0.96)
5. Streetlight Verse — 0.99
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.99 (+0.99)

Chill Lofi: genre=lofi, mood=chill, energy=0.35
1. Library Rain — 4.00
   Because: genre match (+2.00); mood match (+1.00); energy similarity 1.00 (+1.00)
2. Midnight Coding — 3.93
   Because: genre match (+2.00); mood match (+1.00); energy similarity 0.93 (+0.93)
3. Focus Flow — 2.95
   Because: genre match (+2.00); mood no match (+0.00); energy similarity 0.95 (+0.95)
4. Spacewalk Thoughts — 1.93
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.93 (+0.93)
5. Coffee Shop Stories — 0.98
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.98 (+0.98)

Deep Intense Rock: genre=rock, mood=intense, energy=0.9
1. Storm Runner — 3.99
   Because: genre match (+2.00); mood match (+1.00); energy similarity 0.99 (+0.99)
2. Gym Hero — 1.97
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.97 (+0.97)
3. Thunder Awake — 1.92
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.92 (+0.92)
4. Afterglow Steps — 0.98
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.98 (+0.98)
5. Sunrise City — 0.92
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.92 (+0.92)

Conflicting Pop: genre=pop, mood=sad, energy=0.95
1. Velvet Goodbye — 3.35
   Because: genre match (+2.00); mood match (+1.00); energy similarity 0.35 (+0.35)
2. Gym Hero — 2.98
   Because: genre match (+2.00); mood no match (+0.00); energy similarity 0.98 (+0.98)
3. Sunrise City — 2.87
   Because: genre match (+2.00); mood no match (+0.00); energy similarity 0.87 (+0.87)
4. Blue Window — 1.29
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.29 (+0.29)
5. Thunder Awake — 0.97
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.97 (+0.97)

Unknown Genre: genre=unlisted, mood=chill, energy=0.2
1. Spacewalk Thoughts — 1.92
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.92 (+0.92)
2. Library Rain — 1.85
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.85 (+0.85)
3. Midnight Coding — 1.78
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.78 (+0.78)
4. Quiet Strings — 1.00
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 1.00 (+1.00)
5. Blue Window — 0.96
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.96 (+0.96)
```

## Experiments You Tried

`python -m src.main --experiment` changes genre from 2 to 1 and energy from 1 to 2,
leaving mood at 1. This is a runtime option, so the baseline remains reproducible.
Actual experimental output:

```text
Loaded songs: 18
Weights: genre=1.0, mood=1.0, energy=2.0

High-Energy Pop: genre=pop, mood=happy, energy=0.8
1. Sunrise City — 3.96
   Because: genre match (+1.00); mood match (+1.00); energy similarity 0.98 (+1.96)
2. Rooftop Lights — 2.92
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.96 (+1.92)
3. Gym Hero — 2.74
   Because: genre match (+1.00); mood no match (+0.00); energy similarity 0.87 (+1.74)
4. Velvet Goodbye — 2.00
   Because: genre match (+1.00); mood no match (+0.00); energy similarity 0.50 (+1.00)
5. Streetlight Verse — 1.98
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.99 (+1.98)

Chill Lofi: genre=lofi, mood=chill, energy=0.35
1. Library Rain — 4.00
   Because: genre match (+1.00); mood match (+1.00); energy similarity 1.00 (+2.00)
2. Midnight Coding — 3.86
   Because: genre match (+1.00); mood match (+1.00); energy similarity 0.93 (+1.86)
3. Focus Flow — 2.90
   Because: genre match (+1.00); mood no match (+0.00); energy similarity 0.95 (+1.90)
4. Spacewalk Thoughts — 2.86
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.93 (+1.86)
5. Coffee Shop Stories — 1.96
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.98 (+1.96)

Deep Intense Rock: genre=rock, mood=intense, energy=0.9
1. Storm Runner — 3.98
   Because: genre match (+1.00); mood match (+1.00); energy similarity 0.99 (+1.98)
2. Gym Hero — 2.94
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.97 (+1.94)
3. Thunder Awake — 2.84
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.92 (+1.84)
4. Afterglow Steps — 1.96
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.98 (+1.96)
5. Sunrise City — 1.84
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.92 (+1.84)

Conflicting Pop: genre=pop, mood=sad, energy=0.95
1. Gym Hero — 2.96
   Because: genre match (+1.00); mood no match (+0.00); energy similarity 0.98 (+1.96)
2. Sunrise City — 2.74
   Because: genre match (+1.00); mood no match (+0.00); energy similarity 0.87 (+1.74)
3. Velvet Goodbye — 2.70
   Because: genre match (+1.00); mood match (+1.00); energy similarity 0.35 (+0.70)
4. Thunder Awake — 1.94
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.97 (+1.94)
5. Storm Runner — 1.92
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.96 (+1.92)

Unknown Genre: genre=unlisted, mood=chill, energy=0.2
1. Spacewalk Thoughts — 2.84
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.92 (+1.84)
2. Library Rain — 2.70
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.85 (+1.70)
3. Midnight Coding — 2.56
   Because: genre no match (+0.00); mood match (+1.00); energy similarity 0.78 (+1.56)
4. Quiet Strings — 2.00
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 1.00 (+2.00)
5. Blue Window — 1.92
   Because: genre no match (+0.00); mood no match (+0.00); energy similarity 0.96 (+1.92)
```

For High-Energy Pop, Rooftop Lights moves from fourth to second because mood and
energy can compete better with an exact genre match. For Conflicting Pop, Gym Hero
replaces Velvet Goodbye at the top: energy alignment overcomes the sad mood bonus.
The other three profiles keep their top-five order. The experiment changes what
is prioritized; without listener judgments it does not establish better accuracy.

## Evaluation and Limitations

The tests cover exact score arithmetic, energy closeness, ranking from a reversed
catalog, both APIs, acoustic preferences, stable ties, malformed CSV input, invalid
values, empty results, k boundaries, the weight experiment, and CLI execution.
See [model_card.md](model_card.md) for profile comparisons, bias, and intended use.
There are no listener ratings or ground-truth relevance labels, so these are
behavioral checks rather than measured recommendation accuracy.

## Reflection

Engineering reflection draft for the student to adapt: choosing a formula makes
implicit priorities visible. A plausible recommendation is not proof that a model
understands a listener. The conflicting profile shows how weights can select
between equally reasonable interpretations of a user's taste.

AI helped implement and check the pipeline, but its outputs still require review:
feature ranges, ranking arithmetic, generated data, and claims about evaluation
must be checked against actual runs. A useful next step would be collecting user
feedback and comparing baseline relevance with a more diverse recommendation list.

Suggested commit message: `Implement CLI-first music recommender with explained ranking and evaluation`.
