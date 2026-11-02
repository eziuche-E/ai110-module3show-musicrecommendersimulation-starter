"""Run explained recommendations and an optional weight experiment."""
import argparse
from pathlib import Path

if __package__:
    from .recommender import ScoreWeights, load_songs, recommend_songs
else:
    from recommender import ScoreWeights, load_songs, recommend_songs

PROFILES = {
    'High-Energy Pop': {'genre': 'pop', 'mood': 'happy', 'energy': 0.8},
    'Chill Lofi': {'genre': 'lofi', 'mood': 'chill', 'energy': 0.35},
    'Deep Intense Rock': {'genre': 'rock', 'mood': 'intense', 'energy': 0.9},
    'Conflicting Pop': {'genre': 'pop', 'mood': 'sad', 'energy': 0.95},
    'Unknown Genre': {'genre': 'unlisted', 'mood': 'chill', 'energy': 0.2},
}


def main() -> None:
    """Print top-k songs, scores, and reasons for selected user profiles."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['all', *PROFILES], default='all')
    parser.add_argument('--experiment', action='store_true', help='Halve genre and double energy weight')
    parser.add_argument('--k', type=int, default=5)
    args = parser.parse_args()
    if args.k < 0:
        parser.error('--k must be nonnegative')
    songs = load_songs(Path(__file__).resolve().parents[1] / 'data' / 'songs.csv')
    weights = ScoreWeights(genre=1, energy=2) if args.experiment else ScoreWeights()
    print(f'Loaded songs: {len(songs)}')
    print(f'Weights: genre={weights.genre:.1f}, mood={weights.mood:.1f}, energy={weights.energy:.1f}')
    profiles = PROFILES if args.profile == 'all' else {args.profile: PROFILES[args.profile]}
    for name, prefs in profiles.items():
        print(f'\n{name}: genre={prefs["genre"]}, mood={prefs["mood"]}, energy={prefs["energy"]}')
        for index, (song, score, explanation) in enumerate(recommend_songs(prefs, songs, args.k, weights), 1):
            print(f'{index}. {song["title"]} — {score:.2f}')
            print(f'   Because: {explanation}')


if __name__ == '__main__':
    main()
