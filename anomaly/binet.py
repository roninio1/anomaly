# AUTOGENERATED! DO NOT EDIT! File to edit: 01_binet.ipynb (unless otherwise specified).

__all__ = ['AnomalyDetection']

# Cell
from fastai.torch_basics import *
from fastai.basics import *


# Cell
class AnomalyDetection():
    def __init__(self, res, y, event_df, t_df, binet=False):
        self.binet = binet
        sm = nn.Softmax(dim=1)
        p = sm(res)
        pred = p.max(1)[0]
        truth = p[list(range(0, len(y))),y]
        a_score = ((pred - truth) / pred).cpu().detach().numpy()
        if self.binet:
            a_score = (pred - truth).cpu().detach().numpy()
        df=pd.DataFrame(columns=['id', 'a_score'])
        df['a_score'] = a_score
        df['trace_id'] = event_df['trace_id'].tolist()
        self.df =  df
        self.t_df = t_df
        self.t = t_df.values.tolist()
    def __call__(self, threshold = 'gmean', s = 20, analyze=False, table=False, t=None):
        self.s = s
        self.threshold = threshold
        if (self.threshold == 'gmean'):
            self.mean = self.df.loc[self.df['a_score']>0]['a_score'].mean()
            self.max_mean = self.mean
        self.alpha = self.heuristic()
        self.anomalies = list(set(self.get_anomalies(self.alpha)))
        self.traces_num = len(self.df['trace_id'].unique())
        f1, precision, recall = self.f1score([item[0] for item in self.t if item[1] !='Attribute'], self.anomalies)
        self.truth = [item[0] for item in self.t if item[1] !='Attribute']
        self.found = len(set(self.truth).intersection(set(self.anomalies)))
        self.results = pd.DataFrame([[self.traces_num, len(self.truth), len(self.anomalies),self.found, f1, self.bestt*self.mean,
                                      self.mean, max(self.fscore)]], columns =['Number of Traces', 'Number of Anomalies', 'Classified as Anomalies',
                                                                               'Correct Classified','F1 Score', 'best Threshold','Mean', 'max Fscore'])
        if (analyze==True):
            self.plot_analyze(self.f, self.best, self.i, self.pre, self.rec,self.fscore)
        if (table==True):
            self.table()

        return self.results

    def get_anomalies(self, a):
        if (self.threshold == 'gmean'):
            return list (self.df.loc[self.df['a_score'] > 0.9]['trace_id'])

    def heuristic(self):
        self.pre = []
        self.rec = []
        self.fscore = []
        if self.binet:
            alpha_low = 0
            alpha_high = 1 / self.max_mean
        else:
            alpha_low = 0.9/self.max_mean
            alpha_high = 1 / self.max_mean
        alpha_dif = alpha_high-alpha_low
        self.alpha_dif = alpha_dif
        self.f =[]
        for i in range (1, self.s):
            alpha = alpha_low+i/self.s*alpha_dif


            r, anomalies = self.r(alpha)
            self.f.append(r)
            f1, precision, recall = self.f1score([item[0] for item in self.t if item[1] !='Attribute'], anomalies)

            self.fscore.append(f1)
            self.pre.append(precision)
            self.rec.append(recall)

        f_2d = self.der(self.f)

        result = 1
        if self.binet:
            result = f_2d.index(max(f_2d)) +2
        else:
            f_2d.reverse()
            spread = max (f_2d) - min (f_2d)
            for i in range(int(len(f_2d)*0.1), len(f_2d)-1):
                if(f_2d[i]> f_2d[i+1] and f_2d[i] - f_2d[i+1] > 0.1 *spread):
                    result = len(f_2d) -i
                    break


        self.i = result
        self.best = self.fscore.index(max(self.fscore))
        self.bestt = (alpha_low+self.best/self.s*alpha_dif)
        return alpha_low+(result+1)/self.s*alpha_dif

    def r(self, a):
        cea = len(self.df)
        anomalies = self.get_anomalies(a)
        p = len(anomalies)
        return p / cea, list(set(anomalies))

    def der (self, f):
        f = np.array(f)
        r_prime_prime = (f[2:] - 2 * f[1:-1] + f[:-2]) / ((1/self.s*self.alpha_dif) * (1/self.s*self.alpha_dif))
        return r_prime_prime.tolist()

    def f1score(self, truth, classified):
        tp = len(set(truth).intersection(set(classified)))
        t = len(truth)
        p = len(classified)

        if (p == 0):
             precision = 1
        else:
            precision = tp/p

        if (t == 0):
            recall = 1
        else:
            recall = tp/t

        if (precision == 0 and recall == 0):
            f1 = 0
        else:
            f1 = 2*precision*recall/(precision+recall)
        return f1, precision, recall

    def plot_analyze (self, f, best, i, pre, rec, fscore):
        fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(18, 4))
        axes[0].plot(f)
        axes[0].set_title('f % classified as Anomaly')
        axes[0].axvline(best, 0, 1, label="Best S", color='g')
        axes[0].axvline(i, 0, 1, label="Chosen S", color='r')
        axes[0].legend()
        axes[1].plot(list(range(2,(self.s-1))), self.der(f))
        axes[1].set_title('f_2der')
        axes[1].axvline(best, 0, 1, label="Best S", color='g')
        axes[1].axvline(i, 0, 1, label="Chosen S", color='r')
        axes[1].legend()
        axes[2].plot(fscore, label="F1 Score")
        axes[2].set_title('F1 Score')
        axes[2].plot(pre, label="Precision")
        axes[2].plot(rec, label="Recall")
        axes[2].axvline(i, 0, 1, label="Chosen S", color='r')
        axes[2].legend()

    def table (self):
        size = list(self.t_df.groupby(by=["1"]).size())
        keys = list(self.t_df.groupby(by=["1"]).groups.keys())
        assigned = []
        for key in keys:
            assigned.append(len(set(list(
                self.t_df.loc[self.t_df['1']== key]['0'])).intersection(set(self.anomalies))))
        display(pd.DataFrame([assigned, size], index =['Found', 'Overall'],columns =keys))


