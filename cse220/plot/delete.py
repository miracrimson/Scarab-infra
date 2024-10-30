import os
import json
import argparse
import shutil
#uncomment last line in plot_figures.sh to del all simulations in lab1.json

def read_descriptor_from_json(descriptor_filename):
    try:
        with open(descriptor_filename, 'r') as json_file:
            descriptor_data = json.load(json_file)
        return descriptor_data
    except FileNotFoundError:
        print(f"Error: File '{descriptor_filename}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file '{descriptor_filename}': {e}")
        return None

def delete_config_files(descriptor_data, sim_path):
    workloads_org = descriptor_data["workloads_list"].copy()

    for config_key in descriptor_data["configurations"].keys():
        for workload in workloads_org:
            exp_path = os.path.join(sim_path, workload, descriptor_data["experiment"], config_key)
            
            if os.path.exists(exp_path):
                print(f"Deleting contents in: {exp_path}")
                
                # change to delete
                for file_name in os.listdir(exp_path):
                    file_path = os.path.join(exp_path, file_name)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)  
                            print(f"Deleted file: {file_path}")
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)  
                            print(f"Deleted directory: {file_path}")
                    except Exception as e:
                        print(f"Failed to delete {file_path}. Reason: {e}")

                if not os.listdir(exp_path):
                    try:
                        os.rmdir(exp_path)  # delete empty folders
                        print(f"Deleted empty directory: {exp_path}")
                    except OSError as e:
                        print(f"Failed to delete directory {exp_path}. Reason: {e}")
            else:
                print(f"Path does not exist: {exp_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Read descriptor file name for deletion')
    parser.add_argument('-s', '--simulation_path', required=True, help='Simulation result path. Usage: -s /home/$USER/exp/simulations')
    parser.add_argument('-d', '--descriptor_name', required=True, help='Experiment descriptor name. Usage: -d /home/$USER/lab1.json')

    args = parser.parse_args()
    descriptor_filename = args.descriptor_name

    descriptor_data = read_descriptor_from_json(descriptor_filename)

    if descriptor_data:
        delete_config_files(descriptor_data, args.simulation_path)
