import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
from matplotlib.patches import Circle
from math import pi
from IPython.display import HTML

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =====================================================================
# SYSTEM GENOME WITH SACRED COUPLING AND MULTI-OBJECTIVE TRACKING
# =====================================================================
class ConnectionGene:
    def __init__(self, in_node, out_node, weight, enabled=True, innovation_num=0):
        self.in_node = in_node
        self.out_node = out_node
        self.weight = weight
        self.enabled = enabled
        self.innovation_num = innovation_num

class OracleTopologyGenome:
    def __init__(self, stack_id=0):
        self.stack_id = stack_id
        self.num_core_nodes = 9  # Core 3-6-9 Geometry
        self.connections = []
        self.aux_nodes = []     # Sprouted auxiliary resonators
        self.innovation_counter = 0
        self.objectives = [0.0, 0.0, 0.0]  # [Polarization, Anchor Drift, Complexity]
        self.rank = 0
        self.crowding_distance = 0.0
        
        self._initialize_sacred_topology()

    def _initialize_sacred_topology(self):
        idx3, idx6, idx9 = 2, 5, 8
        # Invariant 3-6 balance coupling locks
        self.add_connection_gene(idx3, idx6, 1.35)
        self.add_connection_gene(idx6, idx3, -1.35)
        
        # Perimeter ring layout sequence (Nodes 1-8)
        for i in range(8):
            self.add_connection_gene(i, (i + 1) % 8, 0.50)
            
        # Absolute decoupling of Stator Node 9
        for i in range(8):
            self.add_connection_gene(i, idx9, 0.0)

    def add_connection_gene(self, in_n, out_n, weight):
        self.innovation_counter += 1
        gene = ConnectionGene(in_n, out_n, weight, enabled=True, innovation_num=self.innovation_counter)
        self.connections.append(gene)

    def mutate_topology(self):
        r = np.random.rand()
        total_nodes = self.num_core_nodes + len(self.aux_nodes)
        
        if r < 0.45:  # Sprout connection bridge
            in_n = np.random.randint(0, total_nodes)
            out_n = np.random.randint(0, total_nodes)
            if out_n != 8:  # Enforce Node 9 isolation
                self.add_connection_gene(in_n, out_n, float(np.random.randn() * 0.40))
                
        elif r < 0.70 and len(self.connections) > 0:  # Sprout auxiliary resonator node
            valid_genes = [g for g in self.connections if g.enabled and g.out_node != 8]
            if valid_genes:
                target_gene = np.random.choice(valid_genes)
                target_gene.enabled = False
                
                new_node_id = total_nodes
                self.aux_nodes.append(new_node_id)
                
                self.add_connection_gene(target_gene.in_node, new_node_id, 1.0)
                self.add_connection_gene(new_node_id, target_gene.out_node, target_gene.weight)

# =====================================================================
# INTEGRATED NSGA-II SORTING ENGINE
# =====================================================================
class NSGA2Engine:
    @staticmethod
    def evaluate_lineage(output_tensor, genome):
        # Objective 1: Minimize Binary Polarization (Drive states to fluid ternary bounds)
        pol_loss = torch.mean(torch.abs(torch.abs(output_tensor) - 1.85)).item()
        
        # Objective 2: Minimize Anchor Drift (Enforce Node 9 Absolute Zero rule)
        drift_loss = torch.abs(output_tensor[:, 8]).mean().item()
        
        # Objective 3: Minimize Complexity Bloat (Penalize structural density)
        complexity = len(genome.connections) + (len(genome.aux_nodes) * 2)
        complexity_loss = float(complexity) / 120.0
        
        genome.objectives = [pol_loss, drift_loss, complexity_loss]

    @staticmethod
    def non_dominated_sort(genomes):
        num_ind = len(genomes)
        dom_counts = [0] * num_ind
        dom_sets = [[] for _ in range(num_ind)]
        fronts = [[]]
        
        for p in range(num_ind):
            for q in range(num_ind):
                p_dom_q = all(genomes[p].objectives[i] <= genomes[q].objectives[i] for i in range(3)) and \
                          any(genomes[p].objectives[i] < genomes[q].objectives[i] for i in range(3))
                q_dom_p = all(genomes[q].objectives[i] <= genomes[p].objectives[i] for i in range(3)) and \
                          any(genomes[q].objectives[i] < genomes[p].objectives[i] for i in range(3))
                if p_dom_q:
                    dom_sets[p].append(q)
                elif q_dom_p:
                    dom_counts[p] += 1
            if dom_counts[p] == 0:
                genomes[p].rank = 1
                fronts[0].append(p)
                
        i = 0
        while len(fronts[i]) > 0:
            next_front = []
            for p in fronts[i]:
                for q in dom_sets[p]:
                    dom_counts[q] -= 1
                    if dom_counts[q] == 0:
                        genomes[q].rank = i + 2
                        next_front.append(q)
            i += 1
            fronts.append(next_front)
        return fronts[:-1]

    @staticmethod
    def calculate_crowding(front, genomes):
        num_f = len(front)
        if num_f == 0: return
        for idx in front: genomes[idx].crowding_distance = 0.0
        
        for m in range(3):
            front_sorted = sorted(front, key=lambda idx: genomes[idx].objectives[m])
            genomes[front_sorted[0]].crowding_distance = float('inf')
            if num_f > 1:
                genomes[front_sorted[-1]].crowding_distance = float('inf')
            
            o_min = genomes[front_sorted[0]].objectives[m]
            o_max = genomes[front_sorted[-1]].objectives[m]
            norm = (o_max - o_min) if (o_max - o_min) != 0 else 1.0
            
            for k in range(1, num_f - 1):
                genomes[front_sorted[k]].crowding_distance += (genomes[front_sorted[k+1]].objectives[m] - genomes[front_sorted[k-1]].objectives[m]) / norm

# =====================================================================
# DYNAMIC LIVING ORACLE HARDWARE BLOCK
# =====================================================================
class NSGA2EvolvingOracle(nn.Module):
    def __init__(self, num_stacks=6):
        super().__init__()
        self.num_stacks = num_stacks
        self.genomes = [OracleTopologyGenome(stack_id=i) for i in range(num_stacks)]
        self.optimizer = NSGA2Engine()
        self.time_step = 0
        self.global_coherence = 1.0

    def forward(self, x, binary_siege=False):
        self.time_step += 1
        batch_size = x.shape[0]
        outputs = []
        
        for i, genome in enumerate(self.genomes):
            total_nodes = genome.num_core_nodes + len(genome.aux_nodes)
            h = torch.zeros(batch_size, total_nodes, device=device)
            h[:, :8] = x[:, :8]
            
            for gene in genome.connections:
                if gene.enabled and gene.in_node < total_nodes and gene.out_node < total_nodes:
                    h[:, gene.out_node] += h[:, gene.in_node] * gene.weight
            
            # Enforce unyielding 3-6 kinetic loop anchors
            diff = h[:, 2] - h[:, 5]
            h[:, 2] += 1.25 * torch.sin(diff)
            h[:, 5] += 1.25 * torch.sin(-diff)
            h[:, 8] = 0.0  # Silent God Anchor remains absolute zero
            
            out = torch.tanh(h[:, :9] * 0.70) * 1.85
            outputs.append(out)
            self.optimizer.evaluate_lineage(out, genome)
            
        # Execute NSGA-II Multi-Objective Sorting Optimization Pass
        fronts = self.optimizer.non_dominated_sort(self.genomes)
        for front in fronts:
            self.optimizer.calculate_crowding(front, self.genomes)
            
        # Optimization loop executing structural adaptation
        if binary_siege and self.time_step % 12 == 0:
            # Sort full population indices based on Rank (lower is better) and Crowding Distance (higher is better)
            sorted_indices = sorted(range(self.num_stacks), key=lambda idx: (self.genomes[idx].rank, -self.genomes[idx].crowding_distance))
            
            champion_idx = sorted_indices[0]
            struggling_idx = sorted_indices[-1]
            
            # Elite lineage structures are mapped directly over failing lineages to force synchronization
            if self.genomes[struggling_idx].rank > 1:
                self.genomes[struggling_idx].connections = list(self.genomes[champion_idx].connections)
                self.genomes[struggling_idx].aux_nodes = list(self.genomes[champion_idx].aux_nodes)
                self.genomes[struggling_idx].mutate_topology()

        # Compute systemic optimization health index
        pol_scores = [g.objectives[0] for g in self.genomes]
        self.global_coherence = 1.0 - (sum(pol_scores) / len(pol_scores))
        return outputs

# =====================================================================
# ADVANCED CHALLENGE IX LIVE DASHBOARD
# =====================================================================
class NSGA2Dashboard:
    def __init__(self, num_stacks=6):
        self.oracle = NSGA2EvolvingOracle(num_stacks=num_stacks).to(device)
        self.num_stacks = num_stacks
        self.siege_start = 60
        
        self.fig = plt.figure(figsize=(19, 11), facecolor='#010204')
        gs = gridspec.GridSpec(3, 2, width_ratios=[1.1, 0.9], height_ratios=[1, 1, 1])
        
        self.ax_left = self.fig.add_subplot(gs[:, 0])
        self.ax_left.set_facecolor('#010204')
        
        self.ax_fronts = self.fig.add_subplot(gs[0, 1])
        self.ax_complexity = self.fig.add_subplot(gs[1, 1])
        self.ax_objectives = self.fig.add_subplot(gs[2, 1])
        
        for ax in [self.ax_fronts, self.ax_complexity, self.ax_objectives]:
            ax.set_facecolor('#05070a')
            ax.tick_params(colors='#c9d1d9')
            ax.grid(True, color='#10151d', linestyle=':')
            
        self.angles = np.array([i * (2 * pi / 8) + (pi / 2) for i in range(8)])
        self.base_x = np.append(np.cos(self.angles), 0.0)
        self.base_y = np.append(np.sin(self.angles), 0.0)
        
        self.scatter_core = self.ax_left.scatter(self.base_x, self.base_y, c='#1f6feb', s=600, edgecolors='#ffffff', zorder=5)
        self.scatter_aux = self.ax_left.scatter([], [], c='#00ffcc', s=400, edgecolors='#ffffff', marker='^', zorder=6)
        
        self.connection_lines = []
        self.ax_left.set_xlim(-2.2, 2.2)
        self.ax_left.set_ylim(-2.2, 2.2)
        self.ax_left.axis('off')
        
        self.title = self.ax_left.text(0, 2.0, "", ha='center', va='center', color='#c9d1d9', fontsize=12, fontweight='bold')
        
        self.time_steps, self.global_coherence_hist = [], []
        self.complexity_histories = [[] for _ in range(num_stacks)]
        self.rank_histories = [[] for _ in range(num_stacks)]
        self.polarization_hist = []
        self.drift_hist = []
        
        self.rank_lines = [self.ax_fronts.plot([], [], linewidth=1.8, label=f"Lineage {i} Rank")[0] for i in range(num_stacks)]
        self.complexity_lines = [self.ax_complexity.plot([], [], linewidth=1.8)[0] for i in range(num_stacks)]
        self.line_pol, = self.ax_objectives.plot([], [], color='#ff7b72', linewidth=2.0, label="Binary Polarization Vector")
        self.line_drift, = self.ax_objectives.plot([], [], color='#7ee787', linewidth=2.0, label="Node 9 Anchor Drift")
        
        self.ax_fronts.set_title("NSGA-II Pareto Frontier Rank Sorting Profile (Lower is Better)", color='#c9d1d9', fontsize=10)
        self.ax_fronts.legend(loc="upper right", facecolor='#05070a', edgecolor='none', fontsize=8, labelcolor='#c9d1d9')
        self.ax_complexity.set_title("Topological Metric Footprint Count (Connections + Resonators)", color='#c9d1d9', fontsize=10)
        self.ax_objectives.set_title("Systemic Objective Function Deflection Levels", color='#c9d1d9', fontsize=10)
        self.ax_objectives.legend(loc="upper left", facecolor='#05070a', edgecolor='none', fontsize=8, labelcolor='#c9d1d9')

    def update(self, frame):
        is_siege = (frame >= self.siege_start)
        adv_freq = 9.0 + 4.0 * np.sin(frame * 0.10) if is_siege else 9.0
        
        if is_siege:
            sq = 1.85 * np.sign(np.sin((frame * 0.05) * adv_freq))
            x_raw = np.full(8, sq) + np.random.randn(8) * 0.15
        else:
            x_raw = np.full(8, np.sin(frame * 0.06)) + np.random.randn(8) * 0.02
            
        x_in = torch.tensor(x_raw, dtype=torch.float32, device=device).unsqueeze(0)
        outputs = self.oracle(x_in, binary_siege=is_siege)
        
        # Isolate Pareto Frontier Leader index
        champion_idx = sorted(range(self.num_stacks), key=lambda idx: (self.oracle.genomes[idx].rank, -self.oracle.genomes[idx].crowding_distance))[0]
        champion_genome = self.oracle.genomes[champion_idx]
        
        num_aux = len(champion_genome.aux_nodes)
        if num_aux > 0:
            aux_angles = np.linspace(0, 2 * pi, num_aux, endpoint=False) + (frame * 0.02)
            aux_x, aux_y = np.cos(aux_angles) * 1.6, np.sin(aux_angles) * 1.6
            self.scatter_aux.set_offsets(np.stack((aux_x, aux_y), axis=1))
            all_x, all_y = np.concatenate((self.base_x, aux_x)), np.concatenate((self.base_y, aux_y))
        else:
            self.scatter_aux.set_offsets(np.empty((0, 2)))
            all_x, all_y = self.base_x, self.base_y
            
        for line in self.connection_lines: line.remove()
        self.connection_lines.clear()
        
        for gene in champion_genome.connections:
            if gene.enabled and gene.in_node < len(all_x) and gene.out_node < len(all_y):
                lw = 3.5 if gene.weight == 1.35 else max(0.5, min(3.0, abs(gene.weight) * 2.0))
                color = '#ffaa00' if gene.in_node in [2,5] or gene.out_node in [2,5] else '#1f6feb'
                if gene.weight == 0.0: color = '#238636'
                
                l, = self.ax_left.plot([all_x[gene.in_node], all_x[gene.out_node]], 
                                       [all_y[gene.in_node], all_y[gene.out_node]], 
                                       color=color, alpha=0.35, linewidth=lw, zorder=1)
                self.connection_lines.append(l)
                
        self.time_steps.append(frame)
        self.global_coherence_hist.append(self.oracle.global_coherence)
        
        avg_pol = sum([g.objectives[0] for g in self.oracle.genomes]) / self.num_stacks
        avg_drift = sum([g.objectives[1] for g in self.oracle.genomes]) / self.num_stacks
        self.polarization_hist.append(avg_pol)
        self.drift_hist.append(avg_drift)
        
        for i in range(self.num_stacks):
            self.rank_histories[i].append(self.oracle.genomes[i].rank)
            self.complexity_histories[i].append(len(self.oracle.genomes[i].connections) + len(self.oracle.genomes[i].aux_nodes))
            
        if len(self.time_steps) > 140:
            self.time_steps.pop(0)
            self.polarization_hist.pop(0)
            self.drift_hist.pop(0)
            for i in range(self.num_stacks):
                self.rank_histories[i].pop(0)
                self.complexity_histories[i].pop(0)
                
        self.ax_fronts.set_xlim(min(self.time_steps), max(self.time_steps) + 5)
        self.ax_fronts.set_ylim(0.8, 4.2)
        for i, line in enumerate(self.rank_lines): line.set_data(self.time_steps, self.rank_histories[i])
            
        for i, line in enumerate(self.complexity_lines): line.set_data(self.time_steps, self.complexity_histories[i])
        self.ax_complexity.set_xlim(min(self.time_steps), max(self.time_steps) + 5)
        self.ax_complexity.set_ylim(0, max([max(h) for h in self.complexity_histories]) + 5)
        
        self.line_pol.set_data(self.time_steps, self.polarization_hist)
        self.line_drift.set_data(self.time_steps, self.drift_hist)
        self.ax_objectives.set_xlim(min(self.time_steps), max(self.time_steps) + 5)
        self.ax_objectives.set_ylim(-0.05, max(max(self.polarization_hist), max(self.drift_hist)) * 1.3 + 0.1)
        
        status = f"ADVERSARIAL FREQUENCY SIEGE PROFILE ACTIVE ({adv_freq:.2f}Hz)" if is_siege else "TERTIARY HARMONIC CALIBRATION PROTOCOL"
        self.title.set_text(f"Spantelergia Oracle Matrix • Challenge IX NSGA-II Integration • Step {frame}\n{status}\n[Pareto Front-1 Dominant Lineage: Stack {champion_idx} | Resonators Sprouted: {num_aux}]")
        
        return [self.scatter_core, self.scatter_aux, self.title, self.line_pol, self.line_drift] + self.rank_lines + self.complexity_lines + self.connection_lines

# =====================================================================
# EXECUTION
# =====================================================================
if __name__ == "__main__":
    dashboard = NSGA2Dashboard(num_stacks=6)
    ani = animation.FuncAnimation(dashboard.fig, dashboard.update, frames=180,
                                  interval=50, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.close()
    display(HTML(ani.to_html5_video()))
