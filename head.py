from cracken.generator      import PreTerminalHeap
from cracken.bullpen        import Bullpen

import datetime
import signal
import sys
import threading

stats = {}

if __name__ == "__main__":
    # Stat collection
    stats["start"] = datetime.datetime.now()
    stats["solution"] = stats["restime"] = stats["start"]
    stats["queued"] = stats["exhausted"] = stats["start"]
    stats["attempts"] = stats["preterms"] = stats["hosts"] = 0
    stats["result"] = "N/A"
    
    def print_stats():
        ended = datetime.datetime.now()
        sys.stdout.write(
            "\nCracken Report:\n" +
            "  Result:          {}\n".format(stats["result"]) +
            "  Runtime:         {}\n".format(ended - stats["start"]) +
            "  Discovery Time:  {}\n".format(stats["restime"] - stats["start"]) +
            "  Time to Queue:   {}\n".format(stats["queued"] - stats["start"]) +
            "  Exhaustion Time: {}\n".format(stats["exhausted"] - stats["start"]) +
            "  Attempts:        {}\n".format(stats["attempts"]) +
            "  Preterminals:    {}\n".format(stats["preterms"]) +
            "  Hosts:           {}\n".format(stats["hosts"])
        )

    # Set up the Bullpen
    hosts = ["tesla{}".format(i) for i in range(1,31)] * 4
    stats["hosts"] = len(hosts)
    bp = Bullpen(hosts, "worker.cracker")
    bp.launch_workers()
    
    # Set up the signal handler to print a report when Ctrl-c is recieved
    def sigint_handler(signum, frame):
        print_stats()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, sigint_handler)

    # Set up the result gathering thread
    def get_result(bullpen):
        while True:
            result = bullpen.get_result()
            if "solution" in result:
                stats["restime"] = datetime.datetime.now()
                stats["result"] = result["solution"]
                sys.stdout.write("MATCH: {}\n".format(result["solution"]))
            if "attempts" in result:
                stats["attempts"] += result["attempts"]
                stats["preterms"] += 1

    t = threading.Thread(target=get_result, args=(bp,))
    t.daemon = True
    t.start()
    
    # Enqueue the preterminals
    preterms_generated = 0
    for preterm in PreTerminalHeap("base_structs.txt", "prob_grammar.txt"):
        preterms_generated += 1
        bp.enqueue(preterm)
        
    bp.kill_workers()
    stats["queued"] = datetime.datetime.now()
    sys.stdout.write("All {} Tasks Queued.\n".format(preterms_generated))
    
    # Wait for all the workers to report termination
    bp.join()
    stats["exhausted"] = datetime.datetime.now()
    print_stats()
