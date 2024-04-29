import numpy as np
import re
from sklearn.cluster import KMeans

lv_hp=8

class random_weight_generator:
    def __init__(self, data, top_dir, n_weights, kvalue=None):
        self.data = data
        self.top_dir = top_dir
        self.n_weights = n_weights
        self.n_features = 26
        self.feature_idx = {}
    
    def random_weight(self):
        tmp_w = np.random.uniform(-10, 10, size=self.n_features)
        return [str(x) for x in tmp_w]
    
    def generate_weight(self, iteration):
        if iteration != 0:
            self.feature_idx = {}
            self.n_features = len(self.data["features"])
            with open(f"{self.top_dir}/features/{iteration}.f", 'w') as f:
                for feat in self.data["features"]:
                    f.write(feat+"\n")
                    self.feature_idx[len(self.feature_idx)] = feat
        for i in range(self.n_weights):
            with open(f"{self.top_dir}/weight/iteration-{iteration}/{i}.w", 'w') as f:
                for w in self.random_weight():
                    f.write(f"{w}\n")

class learning_weight_generator:
    def __init__(self, data, top_dir, n_scores, kvalue=3):
        self.data = data
        self.top_dir = top_dir
        self.n_weights = n_scores
        self.feature_idx = {}
        self.classifier = KMeans(kvalue,n_init='auto')

    def abstract_condition(self,lines):
        result = set()
        largeValRe = re.compile("\\d{"+str(lv_hp)+",}")
        for line in lines:
            result.add(re.sub(largeValRe, "LargeValue", line))        
        return result

    def get_scores(self):
        scores = (self.data["widx_info"])/(self.data["widx_info"].max(axis=0)+ 1)
        scores = scores.sum(axis=1)
        return scores
                    
    def write_feature_file(self, iteration):
        with open(f"{self.top_dir}/features/{iteration}.f", 'w') as f:
            feature_list = sorted(self.feature_idx.keys(), key=lambda x: self.feature_idx[x])
            for feature in feature_list:
                f.write(feature+"\n")

    def write_weight_file(self, iteration):
        for widx in range(self.n_weights):
            with open(f"{self.top_dir}/weight/iteration-{iteration}/{widx}.w", 'w') as f:
                for w in self.weights[:,widx-1]:
                    f.write(f"{w}\n")

    def gather_encountered_features(self, pcidxes):
        tmp_encountered = set()
        for pcidx in pcidxes:
            tmp_encountered |= self.abstract_condition(self.data["unique pc"][pcidx])
        return tmp_encountered
        
    def generate_weight(self, iteration):
        if iteration == 1:
            self.feature_idx = {}
            for feat in self.data["features"]:
                self.feature_idx[feat] = len(self.feature_idx)
            self.weights = np.random.uniform(-10, 10, (len(self.data["features"]), self.n_weights))
        else:
            remaining_features = list(set(self.feature_idx.keys()) & self.data["features"])
            
            if len(remaining_features) != 0:
                feature_encountered_score = np.zeros(self.n_weights)
                encountered_weights = np.zeros((len(remaining_features), self.n_weights))
                for widx in range(self.n_weights):
                    encountered_features = self.gather_encountered_features(self.data["widx_pcidxes"][widx])
                    feature_encountered_score[widx] = len(encountered_features)
                    for i, feat in enumerate(remaining_features):
                        if feat in encountered_features:
                            encountered_weights[i][widx] = 1
                encountered_weights *= self.weights[np.array([self.feature_idx[x] for x in remaining_features])]
                self.feature_idx = {}
                for feat in self.data["features"]:
                    self.feature_idx[feat] = len(self.feature_idx)
                self.weights = np.random.uniform(-10, 10, (len(self.data["features"]), self.n_weights))
                scores = self.get_scores()
                self.classifier.fit(scores.reshape(-1,1))
                labels = self.classifier.labels_
                top_widx = np.zeros_like(scores)
                bot_widx = np.zeros_like(scores)
                top_widx[np.where(labels == labels[scores.argmax()])[0]] = 1
                bot_widx[np.where(labels == labels[scores.argmin()])[0]] = 1
                
                for i, pre_weights in enumerate(encountered_weights):
                    tmp_top = top_widx * pre_weights
                    tmp_bot = bot_widx * pre_weights
                    tmp_top = tmp_top[np.nonzero(tmp_top)[0]]
                    tmp_bot = tmp_bot[np.nonzero(tmp_bot)[0]]
                    
                    tm = np.nan
                    ts = np.nan
                    bm = np.nan
                    bs = np.nan
                    if tmp_top.size:
                        tm = tmp_top.mean()
                        ts = tmp_top.std()
                    if tmp_bot.size:
                        bm = tmp_bot.mean()
                        bs = tmp_bot.std()
                    
                    if np.isnan(tm) and np.isnan(bm):
                        continue
                    elif np.isnan(tm) and not np.isnan(bm):
                        self.weights[self.feature_idx[remaining_features[i]]] = -1 * np.abs(self.weights[self.feature_idx[remaining_features[i]], :self.n_weights])

                    elif not np.isnan(tm) and np.isnan(bm):
                        self.weights[self.feature_idx[remaining_features[i]]] = np.random.normal(tm, ts, self.n_weights)

                    elif np.abs(tm-bm) + np.abs(ts - bs) >= 1:
                        self.weights[self.feature_idx[remaining_features[i]]] = np.random.normal(tm, ts, self.n_weights)

                self.weights[self.weights > 10] = 10
                self.weights[self.weights < -10] = -10

            else:
                self.feature_idx = {}
                for feat in self.data["features"]:
                    self.feature_idx[feat] = len(self.feature_idx)
                self.weights = np.random.uniform(-10, 10, (len(self.data["features"]), self.n_weights))
            
        self.write_feature_file(iteration)
        self.write_weight_file(iteration)
