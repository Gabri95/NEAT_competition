
import numpy as np


class Model:
    
    def __init__(self, parameters_file=None, genome=None, I=None, H=None, O=None):
        
        if parameters_file is not None:
            print('Build model from file')
            
            file = open(parameters_file, 'r')
            
            #read the first line
            header = file.readline()
            
            # the first line contains the number of input neurons, output neurons and hidden neurons, separated by a comma
            self.I, self.O, self.H = (int(n) for n in header[1:].split(','))
            
            # Matrix containing the connections from each neuron (input, hidden or output) to each hidden or output neuron.
            # As a result, the size has to be (H+O)*(I+H+O).
            # Moreover, the neurons have to be in the following order: input, output, hidden.
            self.W = np.genfromtxt(parameters_file, skip_header=1)

            assert (self.H+self.O)*(self.I+self.H+self.O) == len(self.W), "Error! Shape of the parameters not valid!"
            
            self.W = self.W.reshape((self.H+self.O,self.I+self.H+self.O))

            # array containing the activiation values of each of the neurons
            # N.B. input neurons are excluded
            # N.B the first O neurons are the output ones, while the last H ones are the hidden ones
            self.V = np.zeros(self.O + self.H)

        elif genome is not None and I is not None and H is not None and O is not None:
            
            print('Build model from genome')
            
            # set the shape of the network
            self.I, self.O, self.H = I, O, H
    
            # Matrix containing the connections from each neuron (input, hidden or output) to each hidden or output neuron.
            # As a result, the size has to be (H+O)*(I+H+O).
            # Moreover, the neurons have to be in the following order: input, output, hidden.
            
            assert (H + O)*(I + H + O) == len(genome), 'Error! genome should contains the same number of elements as the expected weights matrix'
            
            # initialize randomly the parameters
            self.W = genome.copy().reshape((H + O, I + H + O))
            
            # array containing the activiation values of each of the neurons
            # N.B. input neurons are excluded
            # N.B the first O neurons are the output ones, while the last H ones are the hidden ones
            self.V = np.zeros(self.O + self.H)
        elif I is not None and H is not None and O is not None:
            
            print('Randomly initialize model')
            
            #set the shape of the network
            self.I, self.O, self.H = I, O, H
        
        
            # Matrix containing the connections from each neuron (input, hidden or output) to each hidden or output neuron.
            # As a result, the size has to be (H+O)*(I+H+O).
            # Moreover, the neurons have to be in the following order: input, output, hidden.
            
            #initialize randomly the parameters
            self.W = np.random.normal(0, 1, (H+O, I+H+O))
    
            
    
            # array containing the activiation values of each of the neurons
            # N.B. input neurons are excluded
            # N.B the first O neurons are the output ones, while the last H ones are the hidden ones
            self.V = np.zeros(self.O + self.H)
            
        else:
            print('Impossible to build model!')
            raise ValueError('Error! No parameter specified!')
    
    #return the genome of this network, i.e. a 1-D array containing all the weights
    def getGenome(self):
        return self.W.copy().reshape(-1)
    
    
    #return the total number of nodes in the network, including also the input layer
    def networkSize(self):
        return self.I + self.O + self.H
    
    #return the number of actual neurons in the network (i.e. hidden + output neurons)
    def numberOfNeurons(self):
        return self.O + self.H
        
    #propagate the input for one step in the network and returns the new values in the output layer
    #N.B.: no activation function is applied to the output layer, i.e. the output layer has a linear (identity) activation function
    def activate(self, input):
        #propagate the value of every neuron to the ones it is connected to
        self.V = self.W.dot(np.concatenate([input, self.V]))
        
        #apply activation function
        # to the hidden neurons
        self.V[self.O:] = np.tanh(self.V[self.O:])

        # to the output neurons
        self.V[:self.O] = sigmoid(self.V[:self.O]) #np.tanh(self.V[:self.O])
        
        #return the output layer
        return self.V[:self.O]
    
    
    #reset the memory of the network
    def reset(self):
        self.V = np.zeros(self.O + self.H)
        
        
        
    #save the parameters of the network to the specified file, in the correct format (the one accepted in the constructor)
    def save_to_file(self, file):
        save_particle(file, self.W, self.I, self.O, self.H)

def save_particle(file, parameters, I, O, H):
    np.savetxt(file, parameters.reshape(-1), header=str(I) + ', ' + str(O) + ', ' + str(H))


#Sigmoid Function
def sigmoid(x):
    return 1.0/(1 + np.exp(-x))