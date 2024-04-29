import matplotlib.pyplot as plt
import re
import os
import tabulate
from datetime import datetime, timedelta


def branch_handler(ktest_gcov):
    with open(ktest_gcov, 'r', errors='ignore') as f:
        lines = f.read().split('        -:    0:Source')[1:]
    covered_branch = set()
    for s in lines:
        s = s.split('\n')
        src_name = s[0].split('/')[-1]
        line_number = 0
        code_line_start = 1
        while "0:" in s[code_line_start]: code_line_start += 1
       
        for l in s[code_line_start:]:
            if ":" in l:
                line_number += 1
                continue                 
            if 'taken' in l:
                tmp = l.split()
                if tmp[3] != '0%':
                    covered_branch.add(f"{src_name}_{line_number}_{tmp[1]}")
    # os.system(f"rm {ktest_gcov}")
    return covered_branch

def err_file_handler(err_file_name):
    with open(err_file_name, 'r', errors='ignore') as f:
        lines = f.readlines()
    file_name = lines[1].split()[1]
    line_no = lines[2].split()[1]
    return f"{file_name} {line_no}"


markers = ['D','^', 'o','p','v']
colorss = ['r', 'b', 'y', 'c', 'g']
line_style = ['solid', 'dotted', 'dashed', 'dashdot', (0, (3,1,1,1))]


#key : labels of figure, value : output directory to draw 
data_dict = {
    # Example : "featmaker" : "/root/featmaker/featmaker_experiments/test/find"
    "featmaker" : "/root/featmaker/featmaker_experiments/test/find",
    "naive" : "/root/featmaker/naive_experiments/test/find",
    "Original KLEE" : "/root/featmaker/original-klee_experiments/test/find",
}

time_coverage_data = {}
error_case_data = {}

for stgy, output_dir in data_dict.items():
    covered_branches = set()
    time_lst = []
    coverage_lst = []
    iteration=0
    if not os.path.exists(output_dir):
        print(f"{output_dir} not found")
        continue
    while os.path.exists(f"{output_dir}/result/iteration-{iteration}/time_result"):
        with open(f"{output_dir}/result/iteration-{iteration}/time_result", 'r') as f:
            lines = f.readlines()
            for l in lines:
                    filename = l.split()[-1]+"_gcov"
                    covered_branches |= branch_handler(filename)
                    creation_time = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', l).group(0)
                    creation_time = datetime.strptime(creation_time, '%Y-%m-%d %H:%M:%S')
                    coverage_lst.append(len(covered_branches))
                    time_lst.append(creation_time)
        iteration += 1
    time_coverage_data[stgy] = (time_lst,coverage_lst)
    
    with open(f"{output_dir}/error_inputs.txt", 'r') as f:
        error_inputs = f.readlines()
    for ktest in error_inputs:
        err_file_name = os.popen(f"ls {ktest[:-5]}*.err 2>/dev/null").read()
        if err_file_name != '':
            bug_location = err_file_handler(err_file_name.strip('\n'))
            if bug_location not in error_case_data:
                error_case_data[bug_location] = set()
            error_case_data[bug_location].add(stgy)

time_coverage_data = sorted(time_coverage_data.items(), key=lambda x: x[1][1][-1], reverse=True)

plt.figure(figsize=(6,5))
for marker_i, (stgy, (x, y)) in enumerate(time_coverage_data):
    started_time = x[0]
    x = [(t - started_time).total_seconds() for t in x]
    plt.plot(x, y, linestyle=line_style[marker_i],color=colorss[marker_i],marker=markers[marker_i],markersize=9,markeredgecolor="black", markevery=len(y)//10, label=stgy, linewidth = "2.2")
plt.legend()
plt.ylabel('# of covered branches', fontdict={'size': 14})
plt.xlabel('time', fontdict={'size': 14})
plt.grid(visible=True, linestyle="--", linewidth = "1.5")
plt.tight_layout()
plt.savefig(f'coverage_figure.pdf')

bug_table = [["Bug location", "featmaker", "naive", "Original KLEE"]]
for error_location in error_case_data:
    r = [error_location]
    for stgy in ["featmaker", "naive", "Original KLEE"]:
        if stgy in error_case_data[error_location]:
            r.append("O")
        else:
            r.append("X")
    bug_table.append(r)
with open(f'bug_table.md', 'w') as f:
    f.write(tabulate.tabulate(bug_table, headers='firstrow', tablefmt='grid', stralign="center"))
    f.write("\n")
