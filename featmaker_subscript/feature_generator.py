import os
import copy
import numpy as np
import pickle
import re

largeValRe = None
lv_hp = 8

def abstract_condition(lines):
    result = set()
    largeValRe = re.compile("\\d{"+str(lv_hp)+",}")
    for line in lines:
        result.add(re.sub(largeValRe, "LargeValue", line))        
    return result

def get_pc_naive(ktest_list):
    local_query_set = set()
    for ktest in ktest_list:
        kquery = ktest.split('.')[0] + '.kquery'
        with open(kquery, 'r', errors='ignore') as f:
            lines = f.read().split('(query [\n') 
        lines = lines[1].split('\n')[:-2]
        local_query_set |= set(lines)
    return local_query_set

def get_pc(ktest):
    kquery = ktest.split('.')[0] + '.kquery'
    if not os.path.exists(kquery):
        return []
    with open(kquery, 'r', errors='ignore') as f:
        lines = f.read().split('(query [\n')
    lines = lines[1].split('\n')[:-2]
    return lines

class feature_generator:
    def __init__(self, data, top_dir, options):
        self.data = data
        self.top_dir = top_dir
        self.n_scores = options.n_scores
        self.main_option = options.main_option

    def collect_naive(self, iteration):
        if iteration <= 1:
            self.data["bsidx_clusters"] = {}
            self.data["unique branchset"] = []
            self.data["branches"] = set()
            self.data["plot data"] = []
        
        self.data["coverage"] = []

        for widx in range(self.n_scores):
            logfile = f"{self.top_dir}/{widx}_result.pkl"
            with open(logfile, 'rb') as f:
                tmp_covered_set = set()
                tmp_ktest_branch_dict = pickle.load(f)
                for ktest, bs in tmp_ktest_branch_dict.items():
                    if bs not in self.data["unique branchset"]:
                        self.data["unique branchset"].append(bs)

                        self.data["bsidx_clusters"][len(self.data["unique branchset"]) - 1] = []
                    bsidx = self.data["unique branchset"].index(bs)
                    self.data["bsidx_clusters"][bsidx].append(ktest)
                    tmp_covered_set |= bs
                self.data["coverage"].append(tmp_covered_set)
                self.data["branches"] |= tmp_covered_set
        self.data["plot data"].append(len(self.data["branches"]))
        with open(f"{self.top_dir}/data/{iteration}.pkl", 'wb') as f:
            pickle.dump(self.data, f)

    def collect_featmaker(self, iteration):
        if iteration <= 1:
            self.data["bsidx_clusters"] = {}
            self.data["unique branchset"] = []
            self.data["unique pc"] = []
            self.data["branches"] = set()
            self.data["plot data"] = []
            self.data["pre_covered"] = set()

        self.data["widx_info"] = np.zeros((self.n_scores,2))
        self.data["widx_pcidxes"] = {}
        tmp_covered_set = set()
        for widx in range(self.n_scores):
            trial_branches = set()
            self.data["widx_pcidxes"][widx] = set()
            logfile = f"{self.top_dir}/{widx}_result.pkl"
            with open(logfile, 'rb') as f:
                tmp_ktest_branch_dict = pickle.load(f)
            for ktest, bs in tmp_ktest_branch_dict.items():
                tmp_pc = get_pc(ktest)

                if len(tmp_pc) == 0:
                    continue
                
                if bs not in self.data["unique branchset"]:
                    self.data["unique branchset"].append(bs)
                    self.data["bsidx_clusters"][len(self.data["unique branchset"]) - 1] = set()
                
                if tmp_pc not in self.data["unique pc"]:
                    self.data["unique pc"].append(tmp_pc)

                bsidx = self.data["unique branchset"].index(bs)
                
                pcidx = self.data["unique pc"].index(tmp_pc)
                self.data["widx_pcidxes"][widx].add(pcidx)

                self.data["bsidx_clusters"][bsidx].add(pcidx)
                trial_branches |= bs

            if iteration != 1:
                self.data["widx_info"][widx] = np.array([len(trial_branches - self.data["pre_covered"]), len(trial_branches)])
            tmp_covered_set |= trial_branches
        
        self.data["branches"] |= tmp_covered_set
        self.data["pre_covered"] = set()
        self.data["pre_covered"] |= tmp_covered_set
        self.data["plot data"].append(len(self.data["branches"]))
        
        with open(f"{self.top_dir}/data/{iteration}.pkl", 'wb') as f:
            pickle.dump(self.data, f)

    def collect(self, iteration):
        if self.main_option == "featmaker":
            self.collect_featmaker(iteration)
        else:
            self.collect_naive(iteration)

        print(f"\tBranch Coverage in iteration-{iteration-1} : {self.data['plot data'][-1]}")

    def cluster_setcover(self):
        bs_br_matrix = np.full((len(self.data["unique branchset"]), len(self.data["branches"])), False)
        coverage_list = np.array([len(x) for x in self.data["unique branchset"]])
        br_dict = {}
        for br in self.data["branches"]:
            br_dict[br] = len(br_dict)
        for bsidx, bs in enumerate(self.data["unique branchset"]):
            for br in bs:
                bs_br_matrix[bsidx, br_dict[br]] = True
        local_bs = np.full(len(self.data["branches"]), False)
        
        tmp_minset = []
        while local_bs.sum() < len(self.data["branches"]):
            tmp_sum = bs_br_matrix.sum(axis=1)
            max_value = tmp_sum.max()
            tmp_bsidxes = np.where(tmp_sum == max_value)[0]
            new_bsidx = tmp_bsidxes[coverage_list[tmp_bsidxes].argmax()]
            tmp_minset.append(new_bsidx)
            local_bs += bs_br_matrix[new_bsidx]
            bs_br_matrix[:, np.where(local_bs)[0]] = False
        return tmp_minset

    def cluster_naive(self):
        return list(self.data["bsidx_clusters"].keys())
    
    def extract_feature(self):
        cluster_set = None
        if self.main_option == "featmaker":
            cluster_set = self.cluster_setcover()
            self.data["features"] = set()
            for bsidx in cluster_set:
                for pcidx in self.data["bsidx_clusters"][bsidx]:
                    self.data["features"] |= set(self.data["unique pc"][pcidx])
            self.data["features"] = abstract_condition(self.data["features"])
        else:
            cluster_set = self.cluster_naive()
            self.data["features"] = set()
            for bsidx in cluster_set:
                 self.data["features"] |= get_pc_naive(self.data["bsidx_clusters"][bsidx])

