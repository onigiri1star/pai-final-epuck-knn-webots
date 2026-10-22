"""Offline test, balanced by class (no Webots required)."""
import importlib.util
import random
from pathlib import Path
from train_model import random_features, teacher

ROOT = Path(__file__).resolve().parent.parent
MODFILE = ROOT / 'controllers' / 'ai_navigation' / 'learned_policy.py'
spec = importlib.util.spec_from_file_location('learned_policy', MODFILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
model = mod.KNNPolicy.from_json(ROOT / 'controllers' / 'ai_navigation' / 'training_data.json')

rng = random.Random(42)
by_label = [[0, 0] for _ in range(3)]
while min(total for _, total in by_label) < 100:
    x = random_features(rng)
    # Deliberately oversample free-space cases with small heading error.
    if rng.random() < 0.55:
        x = (rng.uniform(0, 0.07), rng.uniform(0, 0.07), rng.uniform(-0.12, 0.12))
    y = teacher(*x)
    if by_label[y][1] >= 100:
        continue
    yp = model.predict(x)
    by_label[y][1] += 1
    by_label[y][0] += yp == y

right = sum(ok for ok, _ in by_label)
n = sum(total for _, total in by_label)
print(f'Balanced synthetic held-out labels: {right}/{n} correct = {right / n:.1%}')
for i, (ok, total) in enumerate(by_label):
    print(f'  {mod.LABELS[i]:>10}: {ok}/{total} correct')
print('NOTE: This is an offline imitation-policy test, NOT a successful Webots route test.')
