"""Reject incomplete or below-target SpaceXAI coverage reports."""

import argparse
import json
from pathlib import Path


def coverage_errors(report: object, integration_dir: Path) -> list[str]:
    """Check every integration module against the unrounded coverage value."""
    expected = {
        f"homeassistant/components/spacexai/{path.relative_to(integration_dir).as_posix()}"
        for path in integration_dir.rglob("*.py")
    }
    if not expected:
        return ["No integration Python modules found"]
    if not isinstance(report, dict) or not isinstance(
        files := report.get("files"), dict
    ):
        return ["Coverage report has no module mapping"]
    if not files:
        return ["Coverage report has no modules"]

    errors = [
        f"Missing coverage for {name}" for name in sorted(expected - files.keys())
    ]
    for name in sorted(expected & files.keys()):
        module = files[name]
        summary = module.get("summary") if isinstance(module, dict) else None
        percentage = (
            summary.get("percent_covered") if isinstance(summary, dict) else None
        )
        if not isinstance(percentage, (int, float)) or not 95 < percentage <= 100:
            errors.append(
                f"{name}: expected coverage above 95%, received {percentage!r}"
            )
    return errors


def main() -> int:
    """Validate a native coverage artifact against its source tree."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument(
        "--integration-dir",
        type=Path,
        default=Path("homeassistant/components/spacexai"),
    )
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        print(f"Cannot read coverage report: {err}")
        return 1
    if errors := coverage_errors(report, args.integration_dir):
        print("\n".join(errors))
        return 1
    print("Every integration Python module is present and has coverage above 95%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
