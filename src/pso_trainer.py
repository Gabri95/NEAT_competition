
import pickle
import os.path
import argparse
import sys

import importlib
import simulation


FILE_PATH = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(FILE_PATH)


sys.path.insert(0, os.path.join(DIR_PATH, '../'))

from pso.pso import Trainer

def get_fitness_function(path):
    dir, file = os.path.split(os.path.abspath(os.path.splitext(path)[0]))
    
    sys.path.insert(0, dir)
    mod = importlib.import_module(file)
    
    return mod.evaluate


def eval_fitness(particle, fitness_function=None, evaluate_function=None, cleaner=None):
    # run the simulation to evaluate the model
    results = evaluate_function(particle)
    
    fitness = fitness_function(results)
    
    print('\tFITNESS =', fitness, '\n')
    
    if cleaner is not None:
        # at the end of the generation, clean the files we don't need anymore
        cleaner()
    
    return fitness


def run(output_dir, generations=20, evaluation=None, init_file=None, **kwargs):
    if output_dir is None:
        print('Error! No output dir has been set')
        return
    
    if evaluation is None:
        fitness_function = get_fitness_function(os.path.join(output_dir, 'fitness.py'))
    else:
        fitness_function = get_fitness_function(evaluation)
    
    trainer = Trainer(30, init_file=init_file)
    
    results_path, models_path, debug_path, checkpoints_path, EVAL_FUNCTION = simulation.initialize_experiments(
        output_dir, **kwargs)
    
    best_model_file = os.path.join(output_dir, 'best.pickle')
    
    trainer.train(generations, lambda particle: eval_fitness(particle=particle,
                                                   fitness_function=fitness_function,
                                                   evaluate_function=lambda g: EVAL_FUNCTION(g),
                                                   cleaner=lambda: simulation.clean_temp_files(results_path,
                                                                                               models_path)
                                                   )
                  )
    
    winner = trainer.getBestModel()
    pickle.dump(winner, open(best_model_file, "wb"))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Trainer for the Particle Swarm Optimization'
    )
    parser.add_argument(
        '-i',
        '--init_file',
        help='Model parameters to use as initializzation.',
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
        required=False
    )
    
    args, _ = parser.parse_known_args()
    
    if args.client_start is None:
        del args.client_start
    
    print(args.__dict__)
    
    run(**args.__dict__)
