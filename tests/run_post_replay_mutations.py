"""Driver-only literal POST-guard mutations; never called by source repair.

Requires a successful frozen baseline in the driver's installed Python venv.
Each selected test runs against baseline, one changed production guard, and
byte-restored source. Collection errors, skips and unexpected test names fail
the run; they never count as a killed guard.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "tests/post_replay_mutations.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run_test(checkout, evidence, selector, label):
    report = evidence / (label + ".xml")
    log = evidence / (label + ".log")
    if report.exists():
        report.unlink()
    with log.open("w") as output:
        process = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", selector, "--junitxml=" + str(report)],
            cwd=str(checkout), stdout=output, stderr=subprocess.STDOUT, timeout=120)
    if not report.is_file():
        raise RuntimeError("No fresh JUnit report: " + label)
    document = ET.parse(report)
    suites = list(document.iter("testsuite"))
    counts = {key: sum(int(suite.get(key, "0")) for suite in suites)
              for key in ("tests", "failures", "errors", "skipped")}
    cases = list(document.iter("testcase"))
    names = sorted((case.get("classname", ""), case.get("name", "")) for case in cases)
    failures = [failure.get("message", "") + "\n" + (failure.text or "")
                for case in cases for failure in case.findall("failure")]
    return {"exit": process.returncode, "counts": counts, "names": names,
            "failure_text": "\n".join(failures)}


def clean(result):
    return (result["exit"] == 0 and result["counts"]["tests"] > 0
            and result["counts"]["failures"] == result["counts"]["errors"]
            == result["counts"]["skipped"] == 0)


def main():
    matrix = json.loads(MATRIX.read_text())
    checkout = Path(matrix["checkout"]).resolve()
    if checkout != ROOT.resolve() or str(checkout) != "/private/tmp/swfte-p5-resume-20261001/python":
        raise SystemExit("Refusing mutation outside the owned isolated Python clone")
    evidence = Path(matrix["evidence"]).resolve()
    expected = Path("/private/tmp/swfte-p5-resume-20261001/.unlazy/p5-code/evidence/sdk-python-post-mutants")
    if evidence != expected:
        raise SystemExit("Refusing an unexpected evidence directory")
    evidence.mkdir(parents=True, exist_ok=True)
    results = []
    for mutant in matrix["mutants"]:
        name = mutant["id"]
        source = (checkout / mutant["path"]).resolve()
        if (checkout / "swfte").resolve() not in source.parents:
            raise SystemExit("Mutation source must belong to production swfte/")
        original = source.read_bytes()
        before, after = mutant["before"].encode(), mutant["after"].encode()
        if before == after or original.count(before) != 1:
            raise SystemExit("Guard must match exactly once: " + name)
        baseline = run_test(checkout, evidence, mutant["selector"], name + ".baseline")
        if not clean(baseline):
            raise SystemExit("Baseline failed: " + name)
        changed = None
        try:
            source.write_bytes(original.replace(before, after, 1))
            changed = run_test(checkout, evidence, mutant["selector"], name + ".mutant")
        finally:
            source.write_bytes(original)
        restored = run_test(checkout, evidence, mutant["selector"], name + ".restored")
        killed = (changed is not None and changed["exit"] != 0
                  and changed["counts"]["failures"] > 0
                  and changed["counts"]["errors"] == changed["counts"]["skipped"] == 0
                  and changed["names"] == restored["names"] == baseline["names"]
                  and mutant["assertion"] in changed["failure_text"]
                  and clean(restored) and source.read_bytes() == original)
        results.append({"id": name, "selector": mutant["selector"], "killed": killed,
                        "source_sha256": digest(original), "baseline": baseline,
                        "mutant": changed, "restored": restored})
        (evidence / "results.json").write_text(json.dumps(results, indent=2) + "\n")
        print(name + ("_KILLED" if killed else "_SURVIVED"), flush=True)
        if not killed:
            raise SystemExit(1)
    print("PYTHON_POST_MUTATIONS_RESTORED_ALL_KILLED", flush=True)


if __name__ == "__main__":
    main()
