# Model Card: VibeFinder 1.0

## 1. Model Name

VibeFinder 1.0: an explainable weighted-score music recommender.

## 2. Intended Use

Classroom exploration of how features become recommendation rankings. A user
provides genre, mood, energy, and optionally an acoustic preference. The system
assumes these labels represent current taste. It is not intended for production
personalization, artist compensation, mental-health inference, or claims about
real listeners. It has no trained parameters or behavioral user tracking.

## 3. How the Model Works

Each exact genre match earns two points and each exact mood match earns one.
Energy earns up to one point: smaller distance from the user's target means more
points. An optional acoustic preference earns up to half a point according to how
acoustic or non-acoustic the track is. Every track is scored, then the highest
scores are returned with component explanations. Ties keep catalog order.
The starter placeholders were replaced with CSV loading, shared scoring and
ranking, validation, and a working CLI. Extra audio features are retained for
future experiments rather than silently included in the score.

## 4. Data

18 fictional tracks: the original ten plus eight AI-generated examples. There are
14 genre labels; pop and lofi each have three tracks, and the other labels have one
each. No original tracks were removed. Fields include labels, energy, tempo,
valence, danceability, and acousticness. Numeric values are illustrative and not
measured from audio. Languages, cultural traditions, artist backgrounds, lyrics,
and real listening contexts are missing. More labels do not prove representative
coverage; the single broad world label is an example of inadequate specificity.

## 5. Strengths

The pop/happy profile selects Sunrise City with 3.98 points; the chill/lofi profile
selects Library Rain with 4.00; intense rock selects Storm Runner with 3.99.
These agree with the explicitly encoded labels and energy targets. Explanations
make the genre, mood, and energy contributions inspectable. Unknown genres still
receive recommendations from mood and energy rather than causing a failure.

## 6. Limitations and Bias

Exact genre matching favors repeated labels: pop and lofi have more matching
candidates than any other genre in this small dataset. A sad, low-energy pop song
outranks happy indie pop for the happy pop profile because the genre bonus is
larger, demonstrating a possible genre filter bubble. Compound or culturally
specific labels are not understood, and catalog-order ties introduce an ordering
bias. Mood and energy tags simplify subjective listening experiences, and no
listener ground truth supports a claim of accurate taste prediction. Expanding
this fictional catalog improves the demonstration's variety but does not resolve
these limitations.

## 7. Evaluation

Executed the CLI for three core profiles and two adversarial profiles; full top-five
outputs, scores, and reasons appear in README.md. Automated checks exercise loading,
score arithmetic, ranking, explanations, validation, both APIs, and CLI behavior.

Pairwise comparisons of the core profiles:

- Pop vs lofi: Sunrise City leads the high-energy happy pop profile; Library Rain
  leads the low-energy chill lofi profile. Both genre and mood bonuses change,
  while the energy target shifts from 0.80 to 0.35.
- Pop vs rock: Sunrise City leads pop and Storm Runner leads rock. Gym Hero appears
  second in both lists: its pop label helps the first and intense mood helps the
  second. Its energy is close to both targets.
- Lofi vs rock: Library Rain leads lofi, while Storm Runner leads rock. Their top
  fives have no shared tracks; genre/mood rewards and opposite energy targets
  favor different catalog regions.

The conflicting profile asks for sad pop at energy 0.95. Velvet Goodbye wins the
baseline despite energy 0.30 because its genre and mood earn three points before
energy is considered. This reveals the recipe's priorities rather than an error
in arithmetic. For an unknown genre with chill mood and energy 0.20, Spacewalk
Thoughts wins because it matches mood and is close in energy; the exact-energy
classical track Quiet Strings ranks fourth because it lacks the mood bonus.

The controlled experiment halves genre weight and doubles energy weight. Rooftop
Lights rises from fourth to second for pop, and Gym Hero replaces Velvet Goodbye
for conflicting pop. Lofi, rock, and unknown-genre top-five orders stay unchanged.
This demonstrates sensitivity, not greater accuracy: no user ratings, held-out
listening histories, or ground-truth preferences are available. Scores are not
probabilities, and no precision or recall claim is made.

## 8. Future Work

1. Collect consented listener feedback and define ground-truth relevance judgments.
2. Add richer genre relationships and optional tempo or danceability targets.
3. Compare diversity-aware reranking with the current exact-match baseline.

## 9. Personal Reflection

Draft for student review and personalization, not a claim about the student's
experience: the main engineering lesson is that a recommendation depends on
explicit choices about features and weights. The sad/high-energy example makes
the tradeoff concrete: a model can follow its formula perfectly while producing
an unexpected suggestion. AI assistance helped connect implementation, tests,
and documentation, but arithmetic and claims needed verification against actual
output. A next experiment would ask listeners which tradeoff they prefer and
compare that feedback with the ranking.
