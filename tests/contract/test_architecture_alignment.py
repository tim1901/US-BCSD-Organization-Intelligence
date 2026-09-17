from pathlib import Path

def test_major_architecture_directories_exist():
    expected=['ingestion','memory','brain','intelligence','learning','delivery','orchestration','ai','storage','models','connectors']
    for name in expected:
        assert (Path('app')/name).is_dir(), name
