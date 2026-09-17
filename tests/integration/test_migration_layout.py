from pathlib import Path

def test_migrations_are_ordered():
    names=[p.name for p in sorted(Path('migrations').glob('*.sql'))]
    assert names == sorted(names)
    assert names[0].startswith('001_')
