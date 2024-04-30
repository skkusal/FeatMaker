import os
import time

configs = {
	'root_dir': os.path.abspath(os.getcwd()),
    'klee_build_dir': os.path.abspath('klee/build/'),
}

search_options = {
    "batching" : "--use-batching-search --batch-instructions=10000",
    "branching" : "--use-branching-search",
}
    
class klee_executor:
    def __init__(self, pconfig, top_dir, options):
        self.pconfig = pconfig
        self.pgm = pconfig["pgm_name"]
        self.top_dir = top_dir
        self.n_scores = options.n_scores
        self.small_time = options.small_time
        self.bin_dir = os.path.abspath('klee/build/bin')
        self.llvm_dir = f"{self.top_dir}/obj-llvm/{self.pconfig['exec_dir']}"
    
    def gen_run_cmd(self, iteration, weight_idx , klee_max_time):
        symbolic_args = self.pconfig["sym_options"]
        
        search_key = "batching"
        if self.pgm in ["find", "sqlite3"]:
            search_key = "branching"

        search_stgy = "nurs:depth"
            
        run_cmd = " ".join([self.bin_dir+"/klee", 
                                    "-only-output-states-covering-new", "--simplify-sym-indices", "--output-module=false",
                                    "--output-source=false", "--output-stats=false", "--disable-inlining", "--write-kqueries", 
                                    "--optimize", "--use-forked-solver", "--use-cex-cache", "--libc=uclibc", "--ignore-solver-failures",
                                    "--posix-runtime", f"-env-file={configs['klee_build_dir']}/../test.env",
                                    "--max-sym-array-size=4096", "--max-memory-inhibit=false",
                                    "--switch-type=internal", search_options[search_key], 
                                    f"--watchdog -max-time={klee_max_time} --search={search_stgy} --output-dir={self.top_dir}/result/iteration-{iteration}/{weight_idx}",
                                    self.pgm+".bc",symbolic_args, "1>/dev/null 2>/dev/null"])
        return run_cmd

    def execute_klee(self, iteration, t):
        print("Execute KLEE in iteration ", iteration)
        remaining_time = t
        os.chdir(self.llvm_dir)
        for weight_idx in range(self.n_scores):
            klee_start_time = time.time()
            run_cmd = self.gen_run_cmd(iteration, weight_idx, min(remaining_time, self.small_time)) 
            os.system(run_cmd)
            remaining_time -= int(time.time()-klee_start_time)
            if remaining_time <= 0:
                break
        os.system(f"ls -l --time-style full-iso {self.top_dir}/result/iteration-{iteration}/*/*.ktest > {self.top_dir}/result/iteration-{iteration}/time_result 2>/dev/null")
        os.chdir(self.top_dir)

