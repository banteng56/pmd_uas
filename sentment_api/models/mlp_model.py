import numpy as np

class MLP:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.01):
        self.W1 = np.random.randn(input_size, hidden_size) * 0.01
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * 0.01
        self.b2 = np.zeros((1, output_size))
        self.lr = learning_rate
        self.is_trained = False
    
    def relu(self, x):
        return np.maximum(0, x)
    
    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    def forward(self, X):
        self.z1 = np.dot(X, self.W1) + self.b1
        self.a1 = self.relu(self.z1)
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        self.a2 = self.softmax(self.z2)
        return self.a2
    
    def backward(self, X, y, output):
        m = X.shape[0]
        
        dz2 = output - y
        dW2 = np.dot(self.a1.T, dz2) / m
        db2 = np.sum(dz2, axis=0, keepdims=True) / m
        
        dz1 = np.dot(dz2, self.W2.T) * (self.a1 > 0)
        dW1 = np.dot(X.T, dz1) / m
        db1 = np.sum(dz1, axis=0, keepdims=True) / m
        
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1
    
    def train(self, X, y, epochs=100, batch_size=32):
        y_onehot = np.zeros((y.shape[0], np.max(y) + 1))
        y_onehot[np.arange(y.shape[0]), y] = 1
        
        for epoch in range(epochs):
            indices = np.random.permutation(X.shape[0])
            for i in range(0, X.shape[0], batch_size):
                batch_indices = indices[i:i+batch_size]
                X_batch = X[batch_indices]
                y_batch = y_onehot[batch_indices]
                
                output = self.forward(X_batch)
                self.backward(X_batch, y_batch, output)
            
            if epoch % 10 == 0:
                output = self.forward(X)
                loss = -np.mean(np.log(output[np.arange(y.shape[0]), y] + 1e-10))
                print(f"MLP Epoch {epoch}, Loss: {loss:.4f}")
        
        self.is_trained = True
    
    def predict(self, X):
        if not self.is_trained:
            raise ValueError("Model not trained")
        output = self.forward(X)
        return np.argmax(output, axis=1)
    
    def predict_proba(self, X):
        if not self.is_trained:
            raise ValueError("Model not trained")
        return self.forward(X)