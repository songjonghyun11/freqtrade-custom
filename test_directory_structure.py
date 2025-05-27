import os

dirs = [
    "src/collectors",
    "src/anomaly",
    "src/strategies/entry_signals",
    "src/strategies/short_signals",
    "src/strategies/exit_signals",
    "src/strategies/risk",
    "src/strategies/allocators",
    "src/managers",
    "src/dashboard",
    "src/utils",
]

def test_directory_structure():
    for d in dirs:
        assert os.path.isdir(d), f"{d} 폴더가 없습니다."
