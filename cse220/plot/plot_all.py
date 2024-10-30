import os
import json
import argparse
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import csv
from matplotlib import cm

matplotlib.rc('font', size=14)

# Read descriptor from JSON
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

def get_IPC(descriptor_data, sim_path, output_dir):
    benchmarks_org = descriptor_data["workloads_list"].copy()
    benchmarks = []
    ipc = {}

    try:
        for config_key in descriptor_data["configurations"].keys():
            ipc_config = []
            avg_IPC_config = 0.0
            for benchmark in benchmarks_org:
                exp_path = sim_path + '/' + benchmark + '/' + descriptor_data["experiment"] + '/'
                IPC = 0
                try:
                    with open(exp_path + config_key + '/memory.stat.0.csv') as f:
                        lines = f.readlines()
                        for line in lines:
                            if 'Periodic IPC' in line:
                                tokens = [x.strip() for x in line.split(',')]
                                IPC = float(tokens[1])
                                break
                except FileNotFoundError:
                    print(f"File not found for {benchmark} in {config_key}, skipping.")
                    continue

                avg_IPC_config += IPC

                if len(benchmarks_org) > len(benchmarks):
                    benchmarks.append(benchmark.split("/"))

                ipc_config.append(IPC)

            num = len(benchmarks_org)  
            if num > 0:
                ipc_config.append(avg_IPC_config / num)  #change to arithmetic mean
            else:
                ipc_config.append(0)

            ipc[config_key] = ipc_config

        benchmarks.append('Avg')
        plot_data(benchmarks, ipc, 'IPC', output_dir + '/Figure_IPC.png')

    except Exception as e:
        print(e)

def get_branch_misprediction(descriptor_data, sim_path, output_dir):
    benchmarks_org = descriptor_data["workloads_list"].copy()
    benchmarks = []
    branch_misprediction = {}

    for config_key in descriptor_data["configurations"].keys():
        misprediction_config = []
        avg_misprediction = 0.0
        for benchmark in benchmarks_org:
            exp_path = sim_path + '/' + benchmark + '/' + descriptor_data["experiment"] + '/'
            branch_mispredict = 0
            branch_correct = 0  # Initialize branch_correct here
            try:
                with open(exp_path + config_key + '/bp.stat.0.csv') as f:  #branch mispredict not in power, in bp
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('BP_ON_PATH_MISPREDICT_count'):
                            tokens = [x.strip() for x in line.split(',')]
                            branch_mispredict = float(tokens[1])
                        if line.startswith('BP_ON_PATH_CORRECT_count'):
                            tokens = [x.strip() for x in line.split(',')]
                            branch_correct = float(tokens[1])

            except FileNotFoundError:
                print(f"File not found for {benchmark} in {config_key}, skipping.")
                continue

            total_branches = branch_mispredict + branch_correct
            if total_branches > 0:
                branch_misprediction_ratio = branch_mispredict / total_branches
                avg_misprediction += branch_misprediction_ratio
                misprediction_config.append(branch_misprediction_ratio)

            if len(benchmarks_org) > len(benchmarks):
                benchmarks.append(benchmark.split("/"))

        num = len(benchmarks_org)
        if num > 0:
            misprediction_config.append(avg_misprediction / num)  #change to arithmetic mean
        else:
            misprediction_config.append(0)

        branch_misprediction[config_key] = misprediction_config

    if 'Avg' not in benchmarks:
        benchmarks.append('Avg')

    plot_data(benchmarks, branch_misprediction, 'Branch Misprediction Ratio', output_dir + '/Figure_Branch_Misprediction.png')


def get_dcache_miss(descriptor_data, sim_path, output_dir):
    benchmarks_org = descriptor_data["workloads_list"].copy()
    benchmarks = []
    dcache_miss_ratio = {}

    for config_key in descriptor_data["configurations"].keys():
        dcache_config = []
        avg_dcache_miss = 0.0
        for benchmark in benchmarks_org:
            exp_path = sim_path + '/' + benchmark + '/' + descriptor_data["experiment"] + '/'
            dcache_miss = None
            dcache_hit = None

            try:
                with open(exp_path + config_key + '/memory.stat.0.csv') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('DCACHE_MISS_count,'):
                            tokens = [x.strip() for x in line.split(',')]
                            dcache_miss = float(tokens[1])
                        if line.startswith('DCACHE_HIT_count,'):
                            tokens = [x.strip() for x in line.split(',')]
                            dcache_hit = float(tokens[1])

            except FileNotFoundError:
                print(f"File not found for {benchmark} in {config_key}, skipping.")
                continue

            total_accesses = dcache_miss + dcache_hit if dcache_miss is not None and dcache_hit is not None else 0
            if total_accesses > 0:
                dcache_miss_ratio_config = dcache_miss / total_accesses
                avg_dcache_miss += dcache_miss_ratio_config
                dcache_config.append(dcache_miss_ratio_config)

            if len(benchmarks_org) > len(benchmarks):
                benchmarks.append(benchmark.split("/"))

        num = len(benchmarks_org)
        if num > 0:
            dcache_config.append(avg_dcache_miss / num)  #change to arithmetic mean
        else:
            dcache_config.append(0)

        dcache_miss_ratio[config_key] = dcache_config

    if 'Avg' not in benchmarks:
        benchmarks.append('Avg')

    plot_data(benchmarks, dcache_miss_ratio, 'Dcache Miss Ratio', output_dir + '/Figure_Dcache_Miss.png')

def get_icache_miss(descriptor_data, sim_path, output_dir):
    benchmarks_org = descriptor_data["workloads_list"].copy()
    benchmarks = []
    icache_miss_ratio = {}

    for config_key in descriptor_data["configurations"].keys():
        icache_config = []
        avg_icache_miss = 0.0
        for benchmark in benchmarks_org:
            exp_path = sim_path + '/' + benchmark + '/' + descriptor_data["experiment"] + '/'
            icache_miss = 0
            icache_hit = 0
            try:
                with open(exp_path + config_key + '/memory.stat.0.csv') as f:
                    lines = f.readlines()
                    for line in lines:
                        if 'ICACHE_MISS_count' in line:
                            tokens = [x.strip() for x in line.split(',')]
                            icache_miss = float(tokens[1])
                        if 'ICACHE_HIT_count' in line:
                            tokens = [x.strip() for x in line.split(',')]
                            icache_hit = float(tokens[1])
            except FileNotFoundError:
                print(f"File not found for {benchmark} in {config_key}, skipping.")
                continue

            total_accesses = icache_miss + icache_hit
            if total_accesses > 0:
                icache_miss_ratio_config = icache_miss / total_accesses
                avg_icache_miss += icache_miss_ratio_config
                icache_config.append(icache_miss_ratio_config)

            if len(benchmarks_org) > len(benchmarks):
                benchmarks.append(benchmark.split("/"))

        num = len(benchmarks_org)
        if num > 0:
            icache_config.append(avg_icache_miss / num)  # Arithmetic mean
        else:
            icache_config.append(0)

        icache_miss_ratio[config_key] = icache_config

    if 'Avg' not in benchmarks:
        benchmarks.append('Avg')

    plot_data(benchmarks, icache_miss_ratio, 'Icache Miss Ratio', output_dir + '/Figure_Icache_Miss.png')

# Plot data
def plot_data(benchmarks, data, ylabel_name, fig_name, ylim=None):
    colors = ['#800000', '#911eb4', '#4363d8', '#f58231']
    ind = np.arange(len(benchmarks))
    width = 0.18
    fig, ax = plt.subplots(figsize=(14, 4.4), dpi=80)
    num_keys = len(data.keys())

    idx = 0
    start_id = -int(num_keys/2)
    for key in data.keys():
        hatch = '\\\\' if idx % 2 else '///'
        ax.bar(ind + (start_id+idx)*width, data[key], width=width, fill=False, hatch=hatch, color=colors[idx], edgecolor=colors[idx], label=key)
        idx += 1
    ax.set_xlabel("Benchmarks")
    ax.set_ylabel(ylabel_name)
    ax.set_xticks(ind)
    ax.set_xticklabels(benchmarks, rotation=27, ha='right')
    ax.grid('x')
    if ylim is not None:
        ax.set_ylim(ylim)
    ax.legend(loc="upper left", ncols=2)
    fig.tight_layout()
    plt.savefig(fig_name, format="png", bbox_inches="tight")

# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Read descriptor file name')
    parser.add_argument('-o', '--output_dir', required=True, help='Output path. Usage: -o /home/$USER/plot')
    parser.add_argument('-d', '--descriptor_name', required=True, help='Experiment descriptor name. Usage: -d /home/$USER/lab1.json')
    parser.add_argument('-s', '--simulation_path', required=True, help='Simulation result path. Usage: -s /home/$USER/exp/simulations')

    args = parser.parse_args()
    descriptor_filename = args.descriptor_name

    descriptor_data = read_descriptor_from_json(descriptor_filename)

    get_IPC(descriptor_data, args.simulation_path, args.output_dir)
    get_branch_misprediction(descriptor_data, args.simulation_path, args.output_dir)
    get_dcache_miss(descriptor_data, args.simulation_path, args.output_dir)
    get_icache_miss(descriptor_data, args.simulation_path, args.output_dir)

    plt.grid('x')
    plt.tight_layout()
    plt.show()
