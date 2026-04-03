import sys
import os
import argparse
import time
import uuid
from datetime import datetime

# Setup sys path for absolute backend imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from database import SessionLocal
from services.trigger_monitor import TriggerMonitor

try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    class FakeStr:
        def __getattr__(self, _): return ""
    Fore = Style = FakeStr()

def format_time():
    return datetime.now().strftime("[%H:%M:%S]")

def print_log(msg, color=""):
    print(f"{color}{msg}{Style.RESET_ALL}")

def get_emoji(trigger_type):
    if "rain" in trigger_type: return "🌧️"
    if "aqi" in trigger_type: return "💨"
    if "heat" in trigger_type: return "☀️"
    if "flood" in trigger_type: return "🌊"
    return "⚠️"

def generate_logs_for_report(report, start_time):
    """
    Translates a trigger evaluation dictionary into the array of visual logs
    needed by both the CLI tool and the React Admin God Mode.
    """
    logs = []
    t = format_time()
    trigger = report.get('trigger_name', 'Unknown')
    emoji = get_emoji(trigger)
    city = report.get('city', 'Unknown')
    zone = report.get('sub_zone', 'Unknown')
    
    logs.append((f"{t} {emoji} TRIGGER FIRED: {trigger.replace('_', ' ').title()} in {city}-{zone}", Fore.CYAN + Style.BRIGHT))
    
    if report.get("result") == "no_trigger":
        logs.append((f"{t}    Measured: {report.get('measured_value')} | Threshold: {report.get('threshold')} | SUB-THRESHOLD ❌", Fore.RED))
        return logs
        
    logs.append((f"{t}    Measured: {report.get('measured_value')} {report.get('unit', '')} | Threshold: {report.get('threshold')} | EXCEEDED ✅", Fore.GREEN))
    
    logs.append((f"{t} 📋 Scanning active policies in {city}-{zone}...", Fore.YELLOW))
    claims = report.get("claims", [])
    logs.append((f"{t}    Found {len(claims)} active policies", Fore.WHITE))
    
    if not claims:
        return logs
        
    logs.append((f"{format_time()} 🔍 Running fraud detection on {len(claims)} claims...", Fore.YELLOW))
    
    auto = []
    flagged = []
    held = []
    
    for c in claims:
        status = c.get('status', '').lower()
        if "approved" in status: auto.append(c)
        elif "review" in status: flagged.append(c)
        else: held.append(c)
        
    avg_fs = sum([c.get('fraud_score', 0) for c in auto]) / max(len(auto), 1)
    
    logs.append((f"{format_time()}    ✅ Auto-approved: {len(auto)} (avg fraud score: {int(avg_fs)})", Fore.GREEN))
    if flagged:
        logs.append((f"{format_time()}    ⚠️ Flagged: {len(flagged)} (fraud score: {int(flagged[0].get('fraud_score', 52))})", Fore.YELLOW))
    if held:
        logs.append((f"{format_time()}    🚫 Held: {len(held)} (fraud score: {int(held[0].get('fraud_score', 78))})", Fore.RED))
        
    logs.append((f"{format_time()} 💰 Processing payouts...", Fore.YELLOW))
    
    for i, c in enumerate(auto):
        txn = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
        user_initial = c.get('user_name', 'user').split()[0].lower()
        platform = "paytm" if i % 2 == 0 else "upi"
        logs.append((f"{format_time()}    ✅ {txn} → {user_initial}@{platform} → ₹{c.get('payout_amount')}", Fore.GREEN))
        if i >= 4 and len(auto) > 5:
            logs.append((f"{format_time()}    ... ({len(auto) - 5} more)", Fore.WHITE))
            break
            
    total_time = time.time() - start_time
    avg_claim_time = total_time / max(len(claims), 1)

    summary = f"""{format_time()} 📊 SUMMARY:
           Total claims: {len(claims)}
           Auto-approved: {len(auto)}
           Total payout: ₹{int(report.get('total_payout_inr', 0)):,}
           Avg time per claim: {avg_claim_time:.2f} seconds
           Total processing time: {total_time:.2f} seconds"""
    
    logs.append((summary, Fore.MAGENTA + Style.BRIGHT))
    return logs

def run_simulation(city, zone, trigger, value):
    db = SessionLocal()
    monitor = TriggerMonitor(db)
    
    print_log(f"[{format_time()}] [SYS] Connecting to Parametric Simulator...", Fore.CYAN)
    start = time.time()
    
    report = monitor.simulate_trigger(city=city, sub_zone=zone, trigger_name=trigger, value_override=value)
    logs = generate_logs_for_report(report, start)
    
    for txt, color in logs:
        time.sleep(0.3) # Fake dramatic delay for CLI
        print_log(txt, color)
        
    db.close()
    return [txt for txt, color in logs]

def main():
    parser = argparse.ArgumentParser(description="ShiftShield Demonstration Trigger Simulator")
    parser.add_argument("--city", help="City name (e.g. Mumbai)")
    parser.add_argument("--zone", help="Sub-zone name (e.g. Dadar)")
    parser.add_argument("--trigger", help="Trigger type (e.g. heavy_rain, severe_aqi)")
    parser.add_argument("--value", type=float, help="Override measured value (e.g. 32.0)")
    parser.add_argument("--scenario", help="Preset demo scenario (monsoon, delhi_smog, heatwave)")
    
    args = parser.parse_args()
    
    if args.scenario:
        if args.scenario == "monsoon":
            print_log("=== SCENARIO: MONSOON INITIATED ===", Fore.RED + Style.BRIGHT)
            run_simulation("Mumbai", "Dadar", "heavy_rain", 32)
            run_simulation("Mumbai", "Bandra", "heavy_rain", 28)
            run_simulation("Bengaluru", "Koramangala", "moderate_rain", 18)
        elif args.scenario == "delhi_smog":
            print_log("=== SCENARIO: DELHI SMOG INITIATED ===", Fore.RED + Style.BRIGHT)
            run_simulation("Delhi", "Connaught Place", "severe_aqi", 420)
        elif args.scenario == "heatwave":
            print_log("=== SCENARIO: NAIVE HEATWAVE INITIATED ===", Fore.RED + Style.BRIGHT)
            run_simulation("Mumbai", "Dadar", "extreme_heat", 47)
        else:
            print_log(f"Unknown scenario: {args.scenario}", Fore.RED)
    elif args.city and args.zone and args.trigger and args.value:
        run_simulation(args.city, args.zone, args.trigger, args.value)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
