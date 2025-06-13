import numpy as np

class HMM:
    def __init__(self, n_states, n_emissions):
        self.n_states = n_states
        self.n_emissions = n_emissions
        self.A = np.ones((n_states, n_states)) / n_states
        self.B = np.ones((n_states, n_emissions)) / n_emissions
        self.pi = np.ones(n_states) / n_states
        self.feature_names = None
        self.is_trained = False
    
    def fit(self, X, y, max_iter=10):
        n_samples = X.shape[0]
        
        for i in range(self.n_states):
            self.pi[i] = np.sum(y == i) / n_samples
        
        for i in range(self.n_states):
            X_i = X[y == i]
            if X_i.shape[0] > 0:
                word_counts = np.sum(X_i, axis=0) + 1
                self.B[i] = word_counts / np.sum(word_counts)
        
        for i in range(self.n_states):
            self.A[i] = self.pi
        
        self.is_trained = True
    
    def predict_proba(self, X):
        if not self.is_trained:
            raise ValueError("Model not trained")
            
        n_samples = X.shape[0]
        probs = np.zeros((n_samples, self.n_states))
        
        for i in range(n_samples):
            for j in range(self.n_states):
                state_prob = self.pi[j]
                emission_probs = np.zeros(self.n_emissions)
                
                for k in range(self.n_emissions):
                    if X[i, k] > 0:
                        emission_probs[k] = np.log(self.B[j, k]) * X[i, k]
                
                log_prob = np.sum(emission_probs)
                probs[i, j] = np.exp(log_prob) * state_prob
            
            if np.sum(probs[i]) > 0:
                probs[i] /= np.sum(probs[i])
        
        return probs
    
    def predict(self, X):
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)