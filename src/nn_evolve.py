
from __future__ import print_function

import os
import pickle
import os.path
import argparse
import sys
import simulation
import math
import datetime
import importlib

FILE_PATH = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(FILE_PATH)


sys.path.insert(0, os.path.join(DIR_PATH, '../'))

from neatsociety import nn, population, statistics, visualize



def eval_fitness(genomes, fitness_function=None, evaluate_function=None, cleaner=None):
    
    print('\nStarting evaluation...\n\n')
    
    tot = len(genomes)
    
    #evaluate the genotypes one by one
    for i, g in enumerate(genomes):
        
        print('evaluating', i+1, '/', tot, '\n')
        net = nn.create_recurrent_phenotype(g)
        
        
        
        #run the simulation to evaluate the model
        results = evaluate_function(net)
        
        # print('\tDistance = ', distance)
        # print('\tDistance from Leader = ', distFromLeader)
        # print('\tAverage Distance from Leader = ', avgDistFromLeader)
        # print('\tRace Position = ', race_position)
        # print('\tLaps = ', laps)
        # print('\tDuration = ', duration)
        # print('\tDamage = ', damage)
        # print('\tPenalty = ', penalty)
        # print('\tDamage/meter = ', damage / math.fabs(distance) if distance != 0.0 else 0.0)
        # print('\tAvgSpeed = ', avg_speed)
            
        
        fitness = fitness_function(results)
        
        print('\tFITNESS =', fitness, '\n')
        
        g.fitness = fitness

    print('\n... finished evaluation\n\n')
    
    if cleaner is not None:
        #at the end of the generation, clean the files we don't need anymore
        cleaner()


def get_best_genome(population):
    best = None
    
    for s in population.species:
        for g in s.members:
            if best is None or best.fitness is None or (g.fitness is not None and g.fitness > best.fitness):
                best = g
    return best


def get_fitness_function(path):
    
    dir, file = os.path.split(os.path.abspath(os.path.splitext(path)[0]))
    
    sys.path.insert(0, dir)
    mod = importlib.import_module(file)
    
    return mod.evaluate
    

def run(output_dir, neat_config=None, generations=20, frequency=None, evaluation=None, checkpoint=None, **kwargs): #port=3001, configuration=None, driver_config_template=None):

    if output_dir is None:
        print('Error! No output dir has been set')
        return
    
    if neat_config is None:
        neat_config = os.path.join(output_dir, 'nn_config')
    
    if evaluation is None:
        fitness_function = get_fitness_function(os.path.join(output_dir, 'fitness.py'))
    else:
        fitness_function = get_fitness_function(evaluation)
        
    
    results_path, models_path, debug_path, checkpoints_path, EVAL_FUNCTION = simulation.initialize_experiments(output_dir, **kwargs) #configuration=configuration, port=port, driver_config_template=driver_config_template)
    
    best_model_file = os.path.join(output_dir, 'best.pickle')
    
    if frequency is None:
        frequency = generations
    
    pop = population.Population(neat_config)
    
    if checkpoint is not None:
        print('Loading from ', checkpoint)
        pop.load_checkpoint(checkpoint)
    
    for g in range(1, generations+1):
        
        pop.run(lambda individuals: eval_fitness(individuals,
                                                 fitness_function=fitness_function,
                                                 evaluate_function=lambda g: EVAL_FUNCTION(g),
                                                 cleaner=lambda: simulation.clean_temp_files(results_path, models_path)
                                                ),
                1)
        
        if g % frequency == 0:
            print('Saving best net in {}'.format(best_model_file))
            best_genome = get_best_genome(pop)
            
            if best_genome is not None:
                pickle.dump(nn.create_recurrent_phenotype(best_genome), open(best_model_file, "wb"))
                
                new_checkpoint = os.path.join(checkpoints_path, 'neat_gen_{}.checkpoint'.format(pop.generation))
                print('Storing to ', new_checkpoint)
                pop.save_checkpoint(new_checkpoint)
                
                print('Plotting statistics')
                visualize.plot_stats(pop.statistics, filename=os.path.join(output_dir, 'avg_fitness.svg'))
                visualize.plot_species(pop.statistics, filename=os.path.join(output_dir, 'speciation.svg'))
                
                print('Save network view')
                visualize.draw_net(best_genome, view=False,
                                   filename=os.path.join(output_dir, "nn_winner-enabled-pruned.gv"),
                                   show_disabled=False, prune_unused=True)
                visualize.draw_net(best_genome, view=False, filename=os.path.join(output_dir, "nn_winner.gv"))
                visualize.draw_net(best_genome, view=False, filename=os.path.join(output_dir, "nn_winner-enabled.gv"),
                                   show_disabled=False)
                statistics.save_stats(pop.statistics, filename=os.path.join(output_dir, 'fitness_history.csv'))
                statistics.save_species_count(pop.statistics, filename=os.path.join(output_dir, 'speciation.csv'))
                statistics.save_species_fitness(pop.statistics, filename=os.path.join(output_dir, 'species_fitness.csv'))
            else:
                print('No genomes in the population!')
                
                
    print('Number of evaluations: {0}'.format(pop.total_evaluations))

    winner = get_best_genome(pop)
    
    if winner is not None:
        print('Saving best net in {}'.format(best_model_file))
        pickle.dump(nn.create_recurrent_phenotype(winner), open(best_model_file, "wb"))
        
        # Display the most fit genome.
        #print('\nBest genome:')
        #winner = pop.statistics.best_genome()
        #print(winner)
    
        
    
        # Visualize the winner network and plot/log statistics.
        visualize.draw_net(winner, view=True, filename=os.path.join(output_dir, "nn_winner.gv"))
        visualize.draw_net(winner, view=True, filename=os.path.join(output_dir, "nn_winner-enabled.gv"), show_disabled=False)
        visualize.draw_net(winner, view=True, filename=os.path.join(output_dir, "nn_winner-enabled-pruned.gv"), show_disabled=False, prune_unused=True)
        visualize.plot_stats(pop.statistics, filename=os.path.join(output_dir, 'avg_fitness.svg'))
        visualize.plot_species(pop.statistics, filename=os.path.join(output_dir, 'speciation.svg'))
        statistics.save_stats(pop.statistics, filename=os.path.join(output_dir, 'fitness_history.csv'))
        statistics.save_species_count(pop.statistics, filename=os.path.join(output_dir, 'speciation.csv'))
        statistics.save_species_fitness(pop.statistics, filename=os.path.join(output_dir, 'species_fitness.csv'))
    else:
        print('No genomes in the population!')




if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='NEAT algorithm'
    )
    parser.add_argument(
        '-c',
        '--checkpoint',
        help='Checkpoint file',
        type=str
    )
    parser.add_argument(
        '-g',
        '--generations',
        help='Number of generations to train',
        type=int,
        default=10
    )

    parser.add_argument(
        '-f',
        '--frequency',
        help='How often to store checkpoints',
        type=int
    )

    parser.add_argument(
        '-o',
        '--output_dir',
        help='Directory where to store checkpoint.',
        type=str
    )

    parser.add_argument(
        '-p',
        '--port',
        help='Port to use for comunication between server (simulator) and client',
        type=int,
        default=3001
    )

    parser.add_argument(
        '-n',
        '--neat_config',
        help='NEAT configuration file. By default uses the "nn_config" file in "output_dir"',
        type=str,
        default=None,
    )

    parser.add_argument(
        '-x',
        '--configuration',
        help='XML configuration file or directory containing a set of XML configuration files for running the race.'
             'By default, uses the "configuration.xml" file in "output_dir"'
             'or, if not present, the directory "output_dir/configuration"',
        type=str,
        default=None
    )

    parser.add_argument(
        '-e',
        '--evaluation',
        help='Python file containing the function for fitness evaluation.\n'
             'The function implemented must have the following signature "evaluate(values: List[List]) -> float".\n'
             'By default uses the "fitness.py" file in "output_dir"',
        type=str,
        default=None
    )

    parser.add_argument(
        '-d',
        '--driver_config_template',
        help='Configuration file template for the driver (use $phenotype for the path to the model)',
        type=str,
        default=None
    )

    parser.add_argument(
        '-s',
        '--client_start',
        help='Bash file to use to start the client. It has to be inside the torcs-client directory',
        type=str,
        default=None
    )
    
    args, _ = parser.parse_known_args()
    
    run(**args.__dict__)
