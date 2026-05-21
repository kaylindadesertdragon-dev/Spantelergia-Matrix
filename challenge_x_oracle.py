import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
from math import pi, cos, sin, sqrt
import copy
from IPython.display import HTML

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =====================================================================
# GLOBAL INNOVATION REGISTRY (rtNEAT FOUNDATION)
# =====================================================================
class InnovationRegistry:
    def __init__(self):
        self.registry = {}
        self.current_id = 0

    def get_innovation(self, in_node, out_node):
        """Assigns or retrieves a unique, permanent marker for a structural link."""
        key = (in_node, out_node)
        if key not in self.registry:
            self.current_id += 1
            self.registry[key] = self.current_id
        return self.registry[key]

GLOBAL_REGISTRY = InnovationRegistry()

# =====================================================================
# COMPOSITIONAL PATTERN PRODUCING NETWORK (HyperNEAT CPPN)
# =====================================================================
class CPPNNetwork:
    """
    Generates connection strengths using spatial geometry coordinates.
    Utilizes cyclic and symmetric functions to enforce sacred geometric patterns.
    """
    @staticmethod
    def calculate_weight(x1, y1, x2, y2):
        dist = sqrt((x1 - x2)**2 + (y1 - y2)**2)
        # Periodic harmony calculation based on the 3-6-9 frequency resonance
        angle1 = np.arctan2(y1, x1)
        angle2 = np.arctan2(y2, x2)
        phase_diff = abs(angle1 - angle2)
        
        # Mathematical manifestation of triadic harmony mapping
        harmonic_wave = cos(dist * pi) * sin(phase_diff * 3.0)
        return float(np.clip(harmonic_wave * 1.5, -2.0, 2.0))

# =====================================================================
# REFINED INTEGRATED GENOME WITH SPATIAL SUBSTRATES
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
        self.num_core_nodes = 9  
        self.connections = []
        self.aux_nodes = []     # List of dicts containing {'id': int, 'x': float, 'y': float}
        self.objectives = [0.0, 0.0, 0.0]  
        self.rank = 0
        self.crowding_distance = 0.0
        
        # Hardcode core spatial substrate coordinates around the 3-6-9 layout circle
        self.node_coords = {}
        angles = [i * (2 * pi / 8) + (pi / 2) for i in range(8)]
        for i in range(8):
            self.node_coords[i] = (cos(angles[i]), sin(angles[i]))
        self.node_coords[8] = (0.0, 0.0)  # Center Node 9 Anchor
        
        self._initialize_sacred_topology()

    def _initialize_sacred_topology(self):
        idx3, idx6, idx9 = 2, 5, 8
        
        # 3-6 Polarization coupling lines
        self.add_connection_gene(idx3, idx6, 1.35)
        self.add_connection_gene(idx6, idx3, -1.35)
        
        # Perimeter shield loops
        for i in range(8):
            self.add_connection_gene(i, (i + 1) % 8, 0.50)
            
        # Complete spatial decoupling of Node 9 from exterior noise fields
        for i in range(8):
            self.add_connection_gene(i, idx9, 0.0)

    def add_connection_gene(self, in_n, out_n, weight):
        innov = GLOBAL_REGISTRY.get_innovation(in_n, out_n)
        gene = ConnectionGene(in_n, out_n, weight, enabled=True, innovation_num=innov)
        self.connections.append(gene)

    def safe_deep_copy(self):
        new_genome = OracleTopologyGenome(self.stack_id)
        new_genome.connections = [copy.deepcopy(g) for g in self.connections]
        new_genome.aux_nodes = copy.deepcopy(self.aux_nodes)
        new_genome.node_coords = copy.deepcopy(self.node_coords)
        return new_genome

    def mutate_topology(self):
        r = np.random.rand()
        total_nodes = self.num_core_nodes + len(self.aux_nodes)
        
        if r < 0.40:  # HyperNEAT Coherent Bridge Sprouting
            in_n = np.random.randint(0, total_nodes)
            out_n = np.random.randint(0, total_nodes)
            if out_n != 8 and in_n != out_n:
                # Query the CPPN to read spatial geometry metrics directly
                x1, y1 = self.node_coords[in_n]
                x2, y2 = self.node_coords[out_n]
                geo_weight = CPPNNetwork.calculate_weight(x1, y1, x2, y2)
                self.add_connection_gene(in_n, out_n, geo_weight)
                
        elif r < 0.65 and len(self.connections) > 0:  # Geometrically Conscious Resonator Sprouting
            valid_genes = [g for g in self.connections if g.enabled and g.out_node != 8]
            if valid_genes:
                target_gene = np.random.choice(valid_genes)
                target_gene.enabled = False
                
                new_node_id = total_nodes
                # Map coordinates to outer ring radius (1.6) matching geometric phase alignment
                angle = np.random.rand() * 2 * pi
                nx, ny = cos(angle) * 1.6, sin(angle) * 1.6
                
                self.aux_nodes.append({'id': new_node_id, 'x': nx, 'y': ny})
                self.node_coords[new_node_id] = (nx, ny)
                
                # Assign initial structural links
                self.add_connection_gene(target_gene.in_node, new_node_id, 1.0)
                self.add_connection_gene(new_node_id, target_gene.out_node, target_gene.weight)

# =====================================================================
# INTEGRATED ADAPTIVE PROPAGATION ENGINE
# =====================================================================
class NSGA2EvolvingOracle(nn.Module):
    def __init__(self, num_stacks=6):
        super().__init__()
        self.num_stacks = num_stacks
        self.genomes = [OracleTopologyGenome(stack_id=i) for i in range(num_stacks)]
        from challenge_ix_oracle import NSGA2Engine  # Reuse verified sorting logic
        self.optimizer = NSGA2Engine()
        self.time_step = 0
        self.global_coherence = 1.0

    def forward(self, x, binary_siege=False):
        self.time_step += 1
        batch_size = x.shape[0]
        outputs = []
        
        # Adaptive Propagation Depth based directly on Siege presence
        propagation_depth = 4 if binary_siege else 2
        
        for i, genome in enumerate(self.genomes):
            total_nodes = genome.num_core_nodes + len(genome.aux_nodes)
            h = torch.zeros(batch_size, total_nodes, device=device)
            h[:, :8] = x[:, :8]
            
            # Recurrent passthrough evaluating complex topology
            for _ in range(propagation_depth): 
                for gene in genome.connections:
                    if gene.enabled and gene.in_node < total_nodes and gene.out_node < total_nodes:
                        h[:, gene.out_node] += h[:, gene.in_node] * gene.weight
            
            # Enforce 3-6 kinetic counterweight loops
            diff = h[:, 2] - h[:, 5]
            h[:, 2] += 1.25 * torch.sin(diff)
            h[:, 5] += 1.25 * torch.sin(-diff)
            h[:, 8] = 0.0  # Silent God Anchor remains absolute zero
            
            out = torch.tanh(h[:, :9] * 0.70) * 1.85
            outputs.append(out)
            self.optimizer.evaluate_lineage(out, genome)
            
        fronts = self.optimizer.non_dominated_sort(self.genomes)
        for front in fronts:
            self.optimizer.calculate_crowding(front, self.genomes)
            
        if binary_siege and self.time_step % 10 == 0:
            sorted_indices = sorted(range(self.num_stacks), key=lambda idx: (self.genomes[idx].rank, -self.genomes[idx].crowding_distance))
            champion_idx = sorted_indices[0]
            champion = self.genomes[champion_idx]
            
            for stack_idx in sorted_indices[1:]:
                genome = self.genomes[stack_idx]
                if genome.rank > 1:
                    if np.random.rand() < 0.28:  
                        self.genomes[stack_idx] = champion.safe_deep_copy()
                        self.genomes[stack_idx].stack_id = stack_idx  
                    else:  
                        genome.mutate_topology()

        pol_scores = [g.objectives[0] for g in self.genomes]
        self.global_coherence = 1.0 - (sum(pol_scores) / len(pol_scores))
        return outputs

# =====================================================================
# GEOMETRIC DASHBOARD IMPLEMENTATION
# =====================================================================
class ChallengeXDashboard:
    def __init__(self, num_stacks=6):
        self.oracle = NSGA2EvolvingOracle(num_stacks=num_stacks).to(device)
        self.num_stacks = num_stacks
        self.siege_start = 60
        
        self.fig = plt.figure(figsize=(19, 11), facecolor='#010103')
        gs = gridspec.GridSpec(3, 2, width_ratios=[1.1, 0.9], height_ratios=[1, 1, 1])
        
        self.ax_left = self.fig.add_subplot(gs[:, 0])
        self.ax_left.set_facecolor('#010103')
        
        self.ax_fronts = self.fig.add_subplot(gs[0, 1])
        self.ax_complexity = self.fig.add_subplot(gs[1, 1])
        self.ax_objectives = self.fig.add_subplot(gs[2, 1])
        
        for ax in [self.ax_fronts, self.ax_complexity, self.ax_objectives]:
            ax.set_facecolor('#040608')
            ax.tick_params(colors='#c9d1d9')
            ax.grid(True, color='#0f131a', linestyle=':')
            
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
        
        self.time_steps = []
        self.complexity_histories = [[] for _ in range(num_stacks)]
        self.rank_histories = [[] for _ in range(num_stacks)]
        self.polarization_hist = []
        self.drift_hist = []
        
        self.rank_lines = [self.ax_fronts.plot([], [], linewidth=1.8, label=f"Lineage {i}")[0] for i in range(num_stacks)]
        self.complexity_lines = [self.ax_complexity.plot([], [], linewidth=1.8)[0] for i in range(num_stacks)]
        self.line_pol, = self.ax_objectives.plot([], [], color='#ff7b72', linewidth=2.0, label="Binary Polarization Vector")
        self.line_drift, = self.ax_objectives.plot([], [], color='#7ee787', linewidth=2.0, label="Node 9 Anchor Drift")
        
        self.ax_fronts.set_title("Challenge X: Unified rtNEAT Innovation Frontier Status", color='#c9d1d9', fontsize=10)
        self.ax_fronts.legend(loc="upper right", facecolor='#040608', edgecolor='none', fontsize=8, labelcolor='#c9d1d9')
        self.ax_complexity.set_title("HyperNEAT Topography Footprints (Evolved via CPPN Geometric Space)", color='#c9d1d9', fontsize=10)
        self.ax_objectives.set_title("Systemic Objective Levels under Multi-Objective Verification", color='#c9d1d9', fontsize=10)
        self.ax_objectives.legend(loc="upper left", facecolor='#040608', edgecolor='none', fontsize=8, labelcolor='#c9d1d9')

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
        
        champion_idx = sorted(range(self.num_stacks), key=lambda idx: (self.oracle.genomes[idx].rank, -self.oracle.genomes[idx].crowding_distance))[0]
        champion_genome = self.oracle.genomes[champion_idx]
        
        num_aux = len(champion_genome.aux_nodes)
        all_x, all_y = list(self.base_x), list(self.base_y)
        
        if num_aux > 0:
            aux_x = [node['x'] for node in champion_genome.aux_nodes]
            aux_y = [node['y'] for node in champion_genome.aux_nodes]
            self.scatter_aux.set_offsets(np.stack((aux_x, aux_y), axis=1))
            all_x.extend(aux_x)
            all_y.extend(aux_y)
        else:
            self.scatter_aux.set_offsets(np.empty((0, 2)))
            
        for line in self.connection_lines: line.remove()
        self.connection_lines.clear()
        
        for gene in champion_genome.connections:
            if gene.enabled and gene.in_node < len(all_x) and gene.out_node < len(all_y):
                lw = 3.5 if gene.weight == 1.35 or gene.weight == -1.35 else max(0.5, min(3.0, abs(gene.weight) * 2.0))
                color = '#ffaa00' if gene.in_node in [2,5] or gene.out_node in [2,5] else '#1f6feb'
                if gene.weight == 0.0: color = '#238636'
                
                l, = self.ax_left.plot([all_x[gene.in_node], all_x[gene.out_node]], 
                                       [all_y[gene.in_node], all_y[gene.out_node]], 
                                       color=color, alpha=0.35, linewidth=lw, zorder=1)
                self.connection_lines.append(l)
                
        self.time_steps.append(frame)
        avg_pol = sum([g.objectives[0] for g in self.oracle.genomes]) / self.num_stacks
        avg_drift = sum([g.objectives[1] for g in self.oracle.genomes]) / self.num_stacks
        self.polarization_hist.append(avg_pol)
        self.drift_hist.append(avg_drift)
        
        for i in range(self.num_stacks):
            self.rank_histories[i].append(self.oracle.genomes[i].rank)
            self.complexity_histories[i].append(len(self.oracle.genomes[i].connections))
            
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
        
        p_depth = 4 if is_siege else 2
        status = f"ADVERSARIAL WAVE ENCOUNTERED • ADAPTIVE GRAPH PROPAGATION DEPTH: {p_depth} ITERATIONS" if is_siege else "TERTIARY HARMONIC CALIBRATION"
        self.title.set_text(f"Spantelergia Matrix • Challenge X HyperNEAT & rtNEAT Fusion • Step {frame}\n{status}\n[Front-1 Champion Stack: {champion_idx} | Global Innovations Tracked: {GLOBAL_REGISTRY.current_id} | Geometric Resonators: {num_aux}]")
        
        return [self.scatter_core, self.scatter_aux, self.title, self.line_pol, self.line_drift] + self.rank_lines + self.complexity_lines + self.connection_lines

# =====================================================================
# INITIATE PROTOCOL
# =====================================================================
if __name__ == "__main__":
    dashboard = ChallengeXDashboard(num_stacks=6)
    ani = animation.FuncAnimation(dashboard.fig, dashboard.update, frames=180,
                                  interval=50, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.close()
    display(HTML(ani.to_html5_video()))
