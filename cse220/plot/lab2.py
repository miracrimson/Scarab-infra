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

# Function to calculate arithmetic mean for IPC
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

            num = len(benchmarks_org)  # Use the number of original benchmarks
            if num > 0:
                ipc_config.append(avg_IPC_config / num)  # Arithmetic mean
            else:
                ipc_config.append(0)

            ipc[config_key] = ipc_config

        benchmarks.append('Avg')
        plot_data(benchmarks, ipc, 'IPC', output_dir + '/Figure_IPC.png')

    except Exception as e:
        print(e)

# Function to calculate arithmetic mean for dcache miss ratio
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
            dcache_config.append(avg_dcache_miss / num)  # Arithmetic mean
        else:
            dcache_config.append(0)

        dcache_miss_ratio[config_key] = dcache_config

    if 'Avg' not in benchmarks:
        benchmarks.append('Avg')

    plot_data(benchmarks, dcache_miss_ratio, 'Dcache Miss Ratio', output_dir + '/Figure_Dcache_Miss.png')




import matplotlib.patches as mpatches

def plot_data(benchmarks, data, ylabel_name, fig_name, ylim=None):
    colors = ['#800000', '#911eb4', '#4363d8', '#f58231', '#42d4f4', '#fabebe', '#9A6324']
    num_keys = len(data.keys())

    # Split benchmarks into three groups of ~8 each for better visualization
    partitions = [benchmarks[i:i + 8] for i in range(0, len(benchmarks), 8)]

    for i, part_benchmarks in enumerate(partitions):
        fig, ax = plt.subplots(figsize=(14, 4.4), dpi=80)
        ind = np.arange(len(part_benchmarks))  # X locations for the benchmarks

        # Dynamically adjust bar width to fit better in the space
        width = 0.8 / num_keys  # Width of bars, adjusting to fit all bars comfortably

        patches = []  # To store patches for custom legend

        # Plot 7 bars for each benchmark corresponding to each configuration
        for idx, key in enumerate(data.keys()):
            hatch = '\\\\' if idx % 2 else '///'
            ax.bar(ind + idx * width, data[key][i*8:(i+1)*8], width=width, fill=False, hatch=hatch, 
                   color=colors[idx], edgecolor=colors[idx], label=key)
            
            # Create a patch for the legend with the same hatch pattern and color
            patch = mpatches.Patch(facecolor='white', edgecolor=colors[idx], hatch=hatch, label=key)
            patches.append(patch)

        ax.set_xlabel("Benchmarks")
        ax.set_ylabel(ylabel_name)
        ax.set_xticks(ind + width * num_keys / 2)
        ax.set_xticklabels(part_benchmarks, rotation=45, ha="right")
        ax.grid('x')

        if ylim is not None:
            ax.set_ylim(ylim)

        # Custom legend using the patches list
        ax.legend(handles=patches, loc="upper left", ncols=2, framealpha=0.5)

        # Save each plot as a separate file
        part_fig_name = fig_name.replace(".png", f"_part{i + 1}.png")
        plt.tight_layout()
        plt.savefig(part_fig_name, format="png", bbox_inches="tight")
        plt.show()


# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Read descriptor file name')
    parser.add_argument('-o', '--output_dir', required=True, help='Output path. Usage: -o /home/$USER/plot')
    parser.add_argument('-d', '--descriptor_name', required=True, help='Experiment descriptor name. Usage: -d /home/$USER/lab1.json')
    parser.add_argument('-s', '--simulation_path', required=True, help='Simulation result path. Usage: -s /home/$USER/exp/simulations')

    args = parser.parse_args()
    descriptor_filename = args.descriptor_name

    descriptor_data = read_descriptor_from_json(descriptor_filename)
    
    # Generate plots for each metric
    get_IPC(descriptor_data, args.simulation_path, args.output_dir)
    get_dcache_miss(descriptor_data, args.simulation_path, args.output_dir)

    plt.grid('x')
    plt.tight_layout()
    plt.show()
