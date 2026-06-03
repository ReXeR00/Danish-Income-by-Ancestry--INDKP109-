from __future__ import annotations

from . import run_eda, run_hypothesis_tests
from .reporting import write_final_report


def main() -> None:
    run_eda.main()
    run_hypothesis_tests.main()
    write_final_report()
    print("Full project pipeline complete.")


if __name__ == "__main__":
    main()
