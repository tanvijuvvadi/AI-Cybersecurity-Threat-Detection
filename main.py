"""One-command runner.   python main.py --step all"""
import argparse
from src import simulate_data, train, evaluate, detect, visualize

STEPS = {"simulate": simulate_data.run, "train": train.run, "evaluate": evaluate.run,
         "detect": detect.run, "visualize": visualize.run}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="AI-Powered Cybersecurity Threat Detection")
    p.add_argument("--step", default="all", choices=["all"] + list(STEPS))
    p.add_argument("--live", type=int, default=0, help="replay N alerts as a live feed (with --step detect)")
    a = p.parse_args()
    if a.step == "all":
        for name, fn in STEPS.items():
            print(f"\n=========== {name.upper()} ===========")
            fn()
    elif a.step == "detect":
        detect.run(live=a.live)
    else:
        STEPS[a.step]()
