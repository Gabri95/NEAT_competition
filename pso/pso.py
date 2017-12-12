
import numpy as np
from pso.pso_model import Model


class Trainer():
    
    def __init__(self, N, C1=2, C2=2, I=10, O=2, H=6, init_file=None):
        
        #particles size
        self.N = N
        
        self.I = I
        self.O = O
        self.H = H
        
        self.C1 = C1
        self.C2 = C2
        
        #length of the particles
        self.gen_size = (H + O) * (I + H + O)

        # record of the best solution
        self.best = {'p':None, 'f':None}
        
        #current particles
        self.particles = []
        
        
        if init_file is None:
        
            for i in range(N):
                #append the genotype and its fitness
                self.particles.append(self.particle(randomSparseVector(self.gen_size)))
        else:
            file = open(init_file, 'r')

            # read the first line
            header = file.readline()
    
            # the first line contains the number of input neurons, output neurons and hidden neurons, separated by a comma
            self.I, self.O, self.H = (int(n) for n in header[1:].split(','))
            
            # Matrix containing the connections from each neuron (input, hidden or output) to each hidden or output neuron.
            # As a result, the size has to be (H+O)*(I+H+O).
            # Moreover, the neurons have to be in the following order: input, output, hidden.
            W = np.genfromtxt(init_file, skip_header=1)
    
            assert (self.H + self.O) * (self.I + self.H + self.O) == len(W), "Error! Shape of the parameters not valid!"

            self.particles.append([W, 0.0])
                
            while len(self.particles) < N:
                self.particles.append(self.particle(W + randomSparseVector(self.gen_size, strength=3, sparsity=0.4)))



    def getBestParticle(self):
        return self.best['p']
    
    def getBestModel(self):
        return Model(genome=self.getBestParticle(), I=self.I, O=self.O, H=self.H)
    
    
    
    def particle(self, W):
        return {'p': W, 'fitness': None, 'pbest': W, 'fbest': None, 'v': 4*(-0.5 + np.random.random_sample(W.shape))}
    
    def evaluateparticles(self, evaluation_function):
        
        for i, p in enumerate(self.particles):

            self.particles[i]['f'] = evaluation_function(Model(genome=self.particles[i]['p'], I=self.I, O=self.O, H=self.H))
            
            if self.particles[i]['fbest'] is None or self.particles[i]['f'] > self.particles[i]['fbest']:
                self.particles[i]['pbest'] = np.copy(self.particles[i]['p'])
                self.particles[i]['fbest'] = self.particles[i]['f']
            
            if self.best['f'] is None or self.particles[i]['f'] > self.best['f']:
                self.best['p'] = np.copy(self.particles[i]['p'])
                self.best['f'] = self.particles[i]['f']
                

    
    def epoch(self, evaluation_function):
        
        self.evaluateparticles(evaluation_function)
        
        
        for particle in self.particles:
            particle['v'] += self.C1*np.random.rand()*(particle['pbest']-particle['p'])
            particle['v'] += self.C2*np.random.rand()*(self.best['p']-particle['p'])
            
            particle['p'] += particle['v']
        
                
    def train(self, E, evaluation_function):
        
        for e in range(E):
            print(' - - - - - - - - - - - - - - -  E P O C H  {}  - - - - - - - - - - - - - - -'.format(e))
            
            self.epoch(evaluation_function)
            
            print('\tBest performance so far: {}'.format(self.best['f']))
            
    
def randomSparseVector(n, strength=1, sparsity=0.2):
    v = np.random.normal(0, strength, n)
    
    m = np.random.binomial(1, sparsity, n)
    
    return v*m
    



def sample(P):
    u = sum(P)*np.random.rand()
    p = 0
    for i, p_i in enumerate(P):
        p += p_i
        
        if u <= p:
            return i
    
    return len(P)-1

    