import json
import sys
from spin_core import run_spin_automation

def main():
    try:
        with open("job.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Leeg het logbestand bij start
        with open("run.log", "w", encoding="utf-8") as f:
            f.write("") 

        for msg in run_spin_automation(data["tasks"], data["config"]):
            with open("run.log", "a", encoding="utf-8") as f:
                f.write(msg + "\n")
                
    except Exception as e:
        with open("run.log", "a", encoding="utf-8") as f:
            f.write(f"\nFATAL CRASH IN RUNNER: {e}\n")

if __name__ == "__main__":
    main()
