

import os
import pickle
import subprocess
import os.path
import sys
import datetime
from shutil import copyfile
import traceback
import time
import signal
import glob

from string import Template


FILE_PATH = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(FILE_PATH)

client_path = os.path.join(DIR_PATH, '../torcs-client/')
client_start = 'start.sh'
shutdown_wait = 10
result_saving_wait = 1
timeout_server = 50


def buildConfigurationFile(phenotype_file, template_file):
    
    filein = open(template_file)
    # read it
    src = Template(filein.read())
    # do the substitution
    content = src.substitute({'phenotype' : os.path.basename(phenotype_file)})
    
    path, _ = os.path.splitext(phenotype_file)
    path = path + '.conf'
    
    with open(path, 'w') as f:
        f.write(content)
    
    return path
        


def simulation(phenotype_file,
               results_file,
               configuration,
               client_stdout_path,
               client_stderr_path,
               server_stdout_path,
               server_stderr_path,
               debug_path,
               port,
               driver_config_template,
               client_path=client_path,
               client_start=client_start,
               shutdown_wait=shutdown_wait,
               result_saving_wait=result_saving_wait,
               timeout_server=timeout_server
               ):
    
    current_time = datetime.datetime.now().isoformat()
    start_time = time.time()

    print('\t\tRun race from', os.path.basename(configuration))
    
    client_stdout = open(client_stdout_path, 'w')
    client_stderr = open(client_stderr_path, 'w')
    server_stdout = open(server_stdout_path, 'w')
    server_stderr = open(server_stderr_path, 'w')
    
    opened_files = [client_stdout, client_stderr, server_stdout, server_stderr]
    
    driver_config = buildConfigurationFile(phenotype_file, driver_config_template)
    
    server = None
    
    print('\t\tStarting Client on port', port)
    client = subprocess.Popen(['./' + client_start, '-p', str(port), '-o', results_file, '-d', driver_config],
                              stdout=client_stdout,
                              stderr=client_stderr,
                              cwd=client_path,
                              preexec_fn=os.setsid
                              )
    
    # wait a second to let client start
    # time.sleep(1)
    
    
    timeout = False
    try:
        
        print('\t\tWaiting for server to stop')
        server = subprocess.Popen(
            ['torcs',
             '-nodamage',
             '-nofuel',
             '-nolaptime',
             '-r',
             configuration],
            stdout=server_stdout,
            stderr=server_stderr,
            preexec_fn=os.setsid
        )
        
        server.wait(timeout=timeout_server)
    
    except subprocess.TimeoutExpired:
        print('\t\tSERVER TIMED-OUT!')
        timeout = True
        
        if server is not None:
            print('Killing server and its children')
            os.killpg(os.getpgid(server.pid), signal.SIGTERM)
    except:
        print('Ops! Something happened"')
        traceback.print_exc()
        
        if server is not None:
            print('Killing server and its children')
            os.killpg(os.getpgid(server.pid), signal.SIGTERM)
        
        client.terminate()
        time.sleep(1)
        if client.poll() is None:
            client.kill()
        
        for file in opened_files:
            file.close()
        
        copyfile(client_stdout_path, os.path.join(debug_path, 'client/ERROR_out_{}.log'.format(current_time)))
        copyfile(client_stderr_path, os.path.join(debug_path, 'client/ERROR_err_{}.log'.format(current_time)))
        copyfile(server_stdout_path, os.path.join(debug_path, 'server/ERROR_out_{}.log'.format(current_time)))
        copyfile(server_stderr_path, os.path.join(debug_path, 'server/ERROR_err_{}.log'.format(current_time)))
        
        raise
    
    print('\t\tGently killing client')

    # Try to be gentle
    os.killpg(os.getpgid(client.pid), signal.SIGTERM)

    # give it some time to stop gracefully
    client.wait(timeout=shutdown_wait)

    # if it is still running, kill it
    if client.poll() is None:
        print('\tCLIENT SURVIVED!!! Trying to KILL client!!')
        os.killpg(os.getpgid(client.pid), signal.SIGKILL)
        time.sleep(shutdown_wait)
    
    for file in opened_files:
        file.close()
    
    print('\t\tSimulation ended')
    
    # wait a second for the results file to be created
    time.sleep(2)

    # if the result file hasn't been created yet, try 10 times waiting 'result_saving_wait' seconds between each attempt
    attempts = 0
    while not os.path.exists(results_file) and attempts < 10:
        attempts += 1
        print('\t\tAttempt', attempts, 'Time =', datetime.datetime.now().isoformat())
        time.sleep(result_saving_wait + attempts - 1)

    # try opening the file
    try:
        results = open(results_file, 'r')
        
        values = []
        
        for line in results.readlines():
            # read the comma-separated values in the first line of the file
            values.append([float(x) for x in line.split(',')])
        
        results.close()
    
    except IOError:
        # if the files doesn't exist print, there might have been some error...
        # print the stacktrace and return None
        
        print("Can't find the result file!")
        traceback.print_exc()
        
        copyfile(client_stdout_path, os.path.join(debug_path, 'client/ERROR_out_{}.log'.format(current_time)))
        copyfile(client_stderr_path, os.path.join(debug_path, 'client/ERROR_err_{}.log'.format(current_time)))
        copyfile(server_stdout_path, os.path.join(debug_path, 'server/ERROR_out_{}.log'.format(current_time)))
        copyfile(server_stderr_path, os.path.join(debug_path, 'server/ERROR_err_{}.log'.format(current_time)))
        
        values = None
    
    end_time = time.time()
    
    print('\t\tSimulation Execution Time =', end_time - start_time, 'seconds')
    
    return values, timeout


def evaluate(net,
             configurations,
             debug_path,
             models_path,
             results_path,
             **kwargs):
             # port=3001,
             # driver_config_template = None):

    
    current_time = datetime.datetime.now().isoformat()
    start_time = time.time()
    results = {}

    phenotype_file = os.path.join(models_path, "model_{}.pickle".format(current_time))
    pickle.dump(net, open(phenotype_file, "wb"))

    for conf_file in configurations:
        name = os.path.splitext(os.path.basename(conf_file))[0]
        
        print('\tEVALUATION on: "{}"'.format(name))
        
        results_file = os.path.join(results_path, 'results_{}_{}'.format(current_time, name))
        print('\t\tResults at', os.path.basename(results_file))
        
        client_stdout_path = os.path.join(debug_path, 'client/out.log')
        client_stderr_path = os.path.join(debug_path, 'client/err.log')
        server_stdout_path = os.path.join(debug_path, 'server/out.log')
        server_stderr_path = os.path.join(debug_path, 'server/err.log')
        
        timedout = True
        trials = 3
        while timedout and trials >= 0:
            values, timedout = simulation(phenotype_file,
                                          results_file,
                                          conf_file,
                                          client_stdout_path,
                                          client_stderr_path,
                                          server_stdout_path,
                                          server_stderr_path,
                                          debug_path,
                                          **kwargs
                                          )
                                            # port=port,
                                            # driver_config_template = driver_config_template
                                            # )
            if timedout:
                time.sleep(3)
                print('Timedout:', trials, ' trials left')
                trials -= 1
                
        if timedout:
            print('|--------------------- WARNING!!! Torcs server keeps timing out!! -----------------------|')
            
            copy_path = os.path.join(debug_path, 'model_timedout_{}_{}.pickle'.format(current_time, name))
    
            print('\t\tCopying the model which caused the timeout to:', copy_path)
            copyfile(phenotype_file, copy_path)
            
            print('\t\tCopying the out and err files of the model')
            copyfile(client_stdout_path, os.path.join(debug_path, 'client/timeout_out_{}_{}.log'.format(current_time, name)))
            copyfile(client_stderr_path, os.path.join(debug_path, 'client/timeout_err_{}_{}.log'.format(current_time, name)))
            copyfile(server_stdout_path, os.path.join(debug_path, 'server/timeout_out_{}_{}.log'.format(current_time, name)))
            copyfile(server_stderr_path, os.path.join(debug_path, 'server/timeout_err_{}_{}.log'.format(current_time, name)))
            
        results[name] = values
    
    end_time = time.time()
    print('Total Execution Time =', end_time - start_time, 'seconds')
        
    return results




def clean_temp_files(results_path, models_path):
    print('Cleaning directories')
    for zippath in glob.iglob(os.path.join(DIR_PATH, results_path, 'results_*')):
        os.remove(zippath)
    for zippath in glob.iglob(os.path.join(DIR_PATH, models_path, '*')):
        os.remove(zippath)



def initialize_experiments(
            output_dir,
            configuration=None,
            port=3001,
            driver_config_template=None,
            **kwargs):
    
    print('Using port', port)
    
    results_path = os.path.join(output_dir, 'results')
    models_path = os.path.join(output_dir, 'models')
    debug_path = os.path.join(output_dir, 'debug')
    checkpoints_path = os.path.join(output_dir, 'checkpoints')
    
    directories = [checkpoints_path,
                   os.path.join(debug_path, 'client'),
                   os.path.join(debug_path, 'server'),
                   models_path,
                   results_path]
    
    for d in directories:
        if not os.path.exists(d):
            os.makedirs(d)
    
    if configuration is None:
        configuration = os.path.join(output_dir, 'configuration.xml')
    
        if not os.path.exists(configuration):
            configuration = os.path.join(output_dir, 'configuration/')

    configuration = os.path.realpath(configuration)
    
    if os.path.isdir(configuration):
        configurations = []
        for zippath in glob.iglob(os.path.join(configuration, '*.xml')):
            configurations.append(zippath)
    elif os.path.isfile(configuration):
        configurations = [configuration]
    else:
        print('Error! Configuration file "{}" does not exist'.format(configuration))
        raise FileNotFoundError('Error! Configuration file "{}" does not exist'.format(configuration))
    
    if driver_config_template is None:
        driver_config_template = os.path.join(output_dir, 'subsumption.template')
        
    debug_path = os.path.realpath(debug_path)
    results_path = os.path.realpath(results_path)
    models_path = os.path.realpath(models_path)
    
    
    
    eval = lambda net: evaluate(net,
                                configurations=configurations,
                                debug_path=debug_path,
                                results_path=results_path,
                                models_path=models_path,
                                port=port,
                                driver_config_template=driver_config_template,
                                **kwargs)
        
    return results_path, models_path, debug_path, checkpoints_path, eval