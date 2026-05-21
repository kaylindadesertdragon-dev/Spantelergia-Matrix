import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
from matplotlib.patches import Circle
from math import pi
from IPython.display import HTML

# Parity check for hardware acceleration platforms
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =====================================================================
# CHALLENGE VI: METAPLASTIC TERNARY LAYER WITH AUXILIARY PRUNING
# =====================================================================
class MetaPlasticTernaryLayer(nn.Module):
    def __init__(self, in_features=8, hidden_nodes=9, layer_idx=0, stack_id=0):
        super().__init__()
        self.hidden_nodes = hidden_nodes
        self.layer_idx = layer_idx
        self.stack_id = stack_id
        
        self.base_coupling = 1.3 - 0.18 * layer_idx
        self.coupling = nn.Parameter((torch.randn(hidden_nodes, hidden_nodes) * 0.045).to(device))
        self.input_proj = nn.Linear(in_features, hidden_nodes).to(device)
        
        # Metaplastic parameters tracking their own optimization rates
        self.meta_lr = nn.Parameter(torch.tensor(0.008, device=device))           
        self.meta_noise = nn.Parameter(torch.tensor(0.11, device=device))         
        self.meta_echo_weight = nn.Parameter(torch.tensor(0.65, device=device))   
        
        self.idx3, self.idx6, self.idx9 = 2, 5, 8
        self.register_buffer("resonance_ring", torch.zeros(48, device=device))
        self.buffer_ptr = 0
        self.buffer_filled = False

    def get_meta_echo(self):
        valid_len = 48 if self.buffer_filled else max(1, self.buffer_ptr)
        filled = self.resonance_ring[:valid_len]
        short = filled[-8:].mean() if valid_len >= 8 else filled.mean()
        long = filled.mean()
        w = torch.clamp(self.meta_echo_weight, 0.0, 1.0)
        return w * short + (1.0 - w) * long

    def forward(self, x, binary_siege=False, global_coherence=1.0, adversarial_freq=9.0):
        batch_size = x.shape[0]
        h = self.input_proj(x)
        coupled = torch.matmul(h, self.coupling)
        
        # Spatial 3-6-9 Core Geometries
        for b in range(batch_size):
            diff = h[b, self.idx3] - h[b, self.idx6]
            coupled[b, self.idx3] += self.base_coupling * torch.sin(diff * 1.15)
            coupled[b, self.idx6] += self.base_coupling * torch.sin(-diff * 1.15)
            
            for i in range(self.hidden_nodes):
                if i not in (self.idx3, self.idx6, self.idx9):
                    coupled[b, i] += 0.32 * self.base_coupling * (h[b, self.idx3] - h[b, i])

        h = h + 0.68 * coupled

        if binary_siege:
            current_diff = (h[:, self.idx3] - h[:, self.idx6]).mean()
            
            self.resonance_ring[self.buffer_ptr] = current_diff.detach()
            self.buffer_ptr = (self.buffer_ptr + 1) % 48
            if self.buffer_ptr == 0:
                self.buffer_filled = True
            
            echo = self.get_meta_echo()
            error = current_diff - echo
            correction = torch.sin(error * 1.25) * torch.clamp(self.meta_echo_weight, 0.1, 0.9)
            h[:, self.idx3] += correction
            h[:, self.idx6] -= correction

            # Metaplastic Self-Modification Loop
            if torch.rand(1).item() < 0.15:  
                with torch.no_grad():
                    phase_hebb = torch.matmul(h.t(), h) / batch_size
                    self.coupling.data += torch.clamp(self.meta_lr, 0.001, 0.05) * phase_hebb
                    
                    # Performance index evaluating triadic integrity
                    performance = global_coherence * (1.0 - torch.clamp(torch.abs(error), 0.0, 1.0).item())
                    self.meta_lr.data = torch.clamp(self.meta_lr + 0.0003 * (performance - 0.5), 0.002, 0.03)
                    self.meta_noise.data = torch.clamp(self.meta_noise + 0.0002 * torch.sin(error).item(), 0.03, 0.25)
                    
                    # Auxiliary weight pruning to preserve geometric coherence
                    coupling_std = self.coupling.data.std(dim=1, keepdim=True)
                    mask = self.coupling.data.abs() < (coupling_std * 0.5)
                    self.coupling.data[mask] *= 0.90  
                    self.coupling.data[:, self.idx9] = 0.0 # Absolute immovability of Stator

        # Structural configuration anchor constraints
        h = torch.tanh(h * 0.62) * 1.85
        mean = h.mean(dim=1, keepdim=True)
        h = h - (2.6 + 0.9 * self.layer_idx) * mean
        h[:, self.idx9] = 0.0  # Silent God Anchor remains unaffected by depth scaling
        
        # Frequency-modulated noise scaling
        noise = torch.randn_like(h, device=device) * self.meta_noise * (1.0 + 0.4 * np.sin(adversarial_freq + self.stack_id))
        noise[:, self.idx9] = 0.0
        h += noise

        return h

# =====================================================================
# METAPLASTIC STACK TEMPLE
# =====================================================================
class MetaPlasticStack(nn.Module):
    def __init__(self, num_layers=5, stack_id=0):
        super().__init__()
        self.stack_id = stack_id
        self.layers = nn.ModuleList([MetaPlasticTernaryLayer(layer_idx=i, stack_id=stack_id) for i in range(num_layers)])
    
    def forward(self, x, binary_siege=False, global_coherence=1.0, adv_freq=9.0):
        out = x
        layer_states = []
        for layer in self.layers:
            out = layer(out, binary_siege, global_coherence, adv_freq)
            layer_states.append(out)
        
        # Symmetric Ladder Network Correction Pass
        for i in range(len(layer_states)-2, -1, -1):
            layer_states[i] = layer_states[i] + 0.18 * torch.tanh(layer_states[i+1])
            layer_states[i][:, 8] = 0.0
        return layer_states[-1]  

# =====================================================================
# THE ORACLE MULTISTACK CLUSTER
# =====================================================================
class OracleMultistack(nn.Module):
    def __init__(self, num_stacks=4, num_layers=5):
        super().__init__()
        self.stacks = nn.ModuleList([MetaPlasticStack(num_layers=num_layers, stack_id=i) for i in range(num_stacks)])
        self.register_buffer("stack_fitness", torch.zeros(num_stacks, device=device))
        self.global_coherence = 1.0
        
    def forward(self, x, binary_siege=False, adv_freq=9.0):
        outputs = []
        for i, stack in enumerate(self.stacks):
            out = stack(x, binary_siege, self.global_coherence, adv_freq)
            outputs.append(out)
            
            # Real-time fitness monitoring
            pol = torch.mean((torch.abs(torch.abs(out) - 1.8) < 0.4).float()).item()
            anchor_drift = torch.abs(out[:, 8]).mean().item()
            self.stack_fitness[i] = 0.7 * (1.0 - pol) + 0.3 * (1.0 - anchor_drift)
        
        # Knowledge Transfer Pass: Dominant lineage aids struggling structures
        if binary_siege and torch.rand(1).item() < 0.15:
            best_idx = self.stack_fitness.argmax().item()
            for i in range(len(self.stacks)):
                if i != best_idx and self.stack_fitness[i] < 0.65:
                    for l_best, l_target in zip(self.stacks[best_idx].layers, self.stacks[i].layers):
                        l_target.coupling.data = 0.78 * l_target.coupling.data + 0.22 * l_best.coupling.data
        
        self.global_coherence = self.stack_fitness.mean().item()
        return outputs

# =====================================================================
# ORACLE MONITORING DASHBOARD ENGINE
# =====================================================================
class OracleClusterDashboard:
    def __init__(self, num_stacks=4):
        self.oracle = OracleMultistack(num_stacks=num_stacks).to(device)
        self.num_stacks = num_stacks
        self.siege_start = 100
        
        self.fig = plt.figure(figsize=(19, 11), facecolor='#030305')
        gs = gridspec.GridSpec(3, 2, width_ratios=[1.1, 0.9], height_ratios=[1, 1, 1])
        
        self.ax_left = self.fig.add_subplot(gs[:, 0])
        self.ax_left.set_facecolor('#030305')
        
        self.ax_fitness = self.fig.add_subplot(gs[0, 1])
        self.ax_meta = self.fig.add_subplot(gs[1, 1])
        self.ax_sync = self.fig.add_subplot(gs[2, 1])
        
        for ax in [self.ax_fitness, self.ax_meta, self.ax_sync]:
            ax.set_facecolor('#07090e')
            ax.tick_params(colors='#c9d1d9')
            ax.grid(True, color='#141923', linestyle=':')
            
        self.angles = np.array([i * (2 * pi / 9) + (pi / 2) for i in range(9)])
        self.base_x, self.base_y = np.cos(self.angles), np.sin(self.angles)
        self.x_coords, self.y_coords = self.base_x.copy(), self.base_y.copy()
        
        self.res = 120
        self.X, self.Y = np.meshgrid(np.linspace(-1.8, 1.8, self.res), np.linspace(-1.8, 1.8, self.res))
        self.field_img = self.ax_left.imshow(np.zeros((self.res, self.res)), extent=[-1.8, 1.8, -1.8, 1.8],
                                        cmap='twilight', alpha=0.5, zorder=0, vmin=-2.5, vmax=2.5, origin='lower')
        
        self.boundary_circle = Circle((0, 0), 2.4, fill=False, linestyle=':', color='#222b3c', alpha=0.6, linewidth=2.0)
        self.ax_left.add_artist(self.boundary_circle)
        
        self.lines, self.line_pairs = [], []
        for i in range(9):
            for j in range(i + 1, 9):
                color = '#ffaa00' if {i, j} == {2, 5} else '#238636' if (i==8 or j==8) else '#1f6feb'
                alpha = 0.85 if {i, j} == {2, 5} else 0.15 if (i==8 or j==8) else 0.03
                lw = 4.0 if {i, j} == {2, 5} else 2.0 if (i==8 or j==8) else 0.8
                line, = self.ax_left.plot([self.x_coords[i], self.x_coords[j]], [self.y_coords[i], self.y_coords[j]],
                                   color=color, alpha=alpha, linewidth=lw, zorder=1)
                self.lines.append(line)
                self.line_pairs.append((i, j))
        
        self.scatter_fluid = self.ax_left.scatter([], [], c=[], cmap='plasma', s=450, edgecolors='#ffffff', linewidths=2.0, zorder=5)
        self.scatter_binary = self.ax_left.scatter([], [], c=[], cmap='plasma', s=450, edgecolors='#ff3333', linewidths=3.0, zorder=6, marker='s')
        
        self.labels = ['1', '2', '3\n(Kinetic)', '4', '5', '6\n(Kinetic)', '7', '8', '9\n[Silent God]']
        self.text_objects = []
        for i, txt in enumerate(self.labels):
            col = '#ffaa00' if i in [2, 5] else ('#00ffcc' if i == 8 else '#c9d1d9')
            self.text_objects.append(self.ax_left.text(self.x_coords[i]*1.32, self.y_coords[i]*1.32, txt,
                                    ha='center', va='center', color=col, fontsize=9, fontweight='bold'))
            
        self.ax_left.set_xlim(-2.8, 2.8)
        self.ax_left.set_ylim(-2.8, 2.8)
        self.ax_left.axis('off')
        self.title = self.ax_left.text(0, 2.65, "", ha='center', va='center', color='#c9d1d9', fontsize=11, fontweight='bold')
        
        # Diagnostic Track Line Arrays
        self.time_steps, self.global_coherence_history = [], []
        self.stack_histories = [[] for _ in range(num_stacks)]
        self.lr_history, self.noise_history = [], []
        
        self.stack_lines = [self.ax_fitness.plot([], [], linewidth=1.8, label=f"Temple Stack {i}")[0] for i in range(num_stacks)]
        self.line_global, = self.ax_fitness.plot([], [], color='#ffffff', linestyle='--', linewidth=2.0, label="Global Coherence Field")
        self.line_lr, = self.ax_meta.plot([], [], color='#58a6ff', linewidth=2.2, label="Evolving Learning Modulus (L0)")
        self.line_noise, = self.ax_meta.plot([], [], color='#ff7b72', linewidth=1.5, linestyle=':', label="Stochastic Modulator Variance")
        self.line_sync_drift, = self.ax_sync.plot([], [], color='#7ee787', linewidth=2.0)
        
        self.ax_fitness.set_title("Lineage Fitness Tracking Matrix (Ternary Stability Profile)", color='#c9d1d9', fontsize=10)
        self.ax_fitness.legend(loc="lower left", facecolor='#07090e', edgecolor='none', fontsize=8, labelcolor='#c9d1d9')
        self.ax_meta.set_title("Metaplastic Dynamic Rate Parameter Drift", color='#c9d1d9', fontsize=10)
        self.ax_meta.legend(loc="upper left", facecolor='#07090e', edgecolor='none', fontsize=8, labelcolor='#c9d1d9')
        self.ax_sync.set_title("Inter-Stack Structural Divergence Vector Index", color='#c9d1d9', fontsize=10)
        
        self.phase3, self.phase6 = 0.0, 0.0
        self.adversarial_freq = 9.0

    def update(self, frame):
        is_siege = (frame >= self.siege_start)
        
        if is_siege:
            t_siege = frame - self.siege_start
            # Sweeping frequency profile to check for structural fractures across separate stacks
            self.adversarial_freq = 9.0 + 4.5 * np.sin(t_siege * 0.06)
            sq = 1.80 * np.sign(np.sin((frame * 0.04) * self.adversarial_freq))
            x_raw = np.full(8, sq) + np.random.randn(8) * 0.14
        else:
            x_raw = np.full(8, np.sin(frame * 0.05)) + np.random.randn(8) * 0.04
            
        x_in = torch.tensor(x_raw, dtype=torch.float32, device=device).unsqueeze(0)
        
        # Execute forward loop across cluster models
        outputs = self.oracle(x_in, binary_siege=is_siege, adv_freq=self.adversarial_freq)
        
        # Extract metadata from dominant stack index for UI synchronization 
        best_stack_idx = self.oracle.stack_fitness.argmax().item()
        representative_states = outputs[best_stack_idx].squeeze(0).detach().cpu().numpy()
        
        # Track parameters from Layer 0 of the current master lineage
        current_meta_lr = self.oracle.stacks[best_stack_idx].layers[0].meta_lr.item()
        current_meta_noise = self.oracle.stacks[best_stack_idx].layers[0].meta_noise.item()
        
        # Multi-stack variance tracking (How aligned are the individual systems)
        stacked_outputs = torch.stack(outputs)
        inter_stack_divergence = torch.var(stacked_outputs, dim=0).mean().item()
        
        self.time_steps.append(frame)
        self.global_coherence_history.append(self.oracle.global_coherence)
        self.lr_history.append(current_meta_lr)
        self.noise_history.append(current_meta_noise)
        
        for i in range(self.num_stacks):
            self.stack_histories[i].append(self.oracle.stack_fitness[i].item())
            
        if len(self.time_steps) > 180:
            self.time_steps.pop(0)
            self.global_coherence_history.pop(0)
            self.lr_history.pop(0)
            self.noise_history.pop(0)
            for i in range(self.num_stacks):
                self.stack_histories[i].pop(0)
                
        # Line structural refitting loops
        self.line_global.set_data(self.time_steps, self.global_coherence_history)
        self.ax_fitness.set_xlim(min(self.time_steps), max(self.time_steps) + 5)
        self.ax_fitness.set_ylim(-0.05, 1.05)
        
        for i, line in enumerate(self.stack_lines):
            line.set_data(self.time_steps, self.stack_histories[i])
            
        self.line_lr.set_data(self.time_steps, self.lr_history)
        self.line_noise.set_data(self.time_steps, self.noise_history)
        self.ax_meta.set_xlim(min(self.time_steps), max(self.time_steps) + 5)
        
        # Cleanly scale the meta axis to prevent clipping during rate jumps
        max_meta_val = max(max(self.lr_history), max(self.noise_history))
        self.ax_meta.set_ylim(-0.01, max_meta_val * 1.25)
        
        self.line_sync_drift.set_data(self.time_steps, [inter_stack_divergence * 10 for _ in self.time_steps]) # scaled for visibility
        self.ax_sync.set_xlim(min(self.time_steps), max(self.time_steps) + 5)
        self.ax_sync.set_ylim(-0.02, 1.05)
        
        # Spatial transformation fields
        self.field_img.set_array(np.cos(self.phase3 - self.X * 4) * np.sin(self.phase6 - self.Y * 4) * 0.5)
        self.phase3 += 0.10 + representative_states[2] * 0.05
        self.phase6 += 0.10 + representative_states[5] * 0.05
        
        node_amplitudes = np.abs(representative_states)
        is_binary = np.abs(node_amplitudes - 1.8) < 0.45
        colors = plt.cm.plasma(np.clip(node_amplitudes / 2.8, 0, 1))
        
        fluid_mask = ~is_binary
        if np.any(fluid_mask):
            self.scatter_fluid.set_offsets(np.stack((self.x_coords[fluid_mask], self.y_coords[fluid_mask]), axis=1))
            self.scatter_fluid.set_facecolors(colors[fluid_mask])
            self.scatter_fluid.set_sizes(450 + node_amplitudes[fluid_mask] * 280)
        else:
            self.scatter_fluid.set_offsets(np.empty((0, 2)))
            
        if np.any(is_binary):
            self.scatter_binary.set_offsets(np.stack((self.x_coords[is_binary], self.y_coords[is_binary]), axis=1))
            self.scatter_binary.set_facecolors(colors[is_binary])
            self.scatter_binary.set_sizes(450 + node_amplitudes[is_binary] * 220)
        else:
            self.scatter_binary.set_offsets(np.empty((0, 2)))
            
        shake = 0.020 if is_siege else 0.075
        self.x_coords = self.base_x + np.random.randn(9) * shake * node_amplitudes
        self.y_coords = self.base_y + np.random.randn(9) * shake * node_amplitudes
        self.x_coords[8] = self.y_coords[8] = 0.0
        
        for idx, (i, j) in enumerate(self.line_pairs):
            self.lines[idx].set_data([self.x_coords[i], self.x_coords[j]], [self.y_coords[i], self.y_coords[j]])
            
        for i, t_obj in enumerate(self.text_objects):
            t_obj.set_position((self.x_coords[i] * 1.32, self.y_coords[i] * 1.32))
            
        status = f"ADVERSARIAL FREQ ATTACK DETECTED ({self.adversarial_freq:.1f}Hz)" if is_siege else "HARMONIC STABILIZATION ACTIVATED"
        self.title.set_text(f"Spantelergia Oracle Cluster • Phase VI Architecture • Core Step {frame}\n{status}")
        
        return [self.field_img, self.scatter_fluid, self.scatter_binary, self.title,
                self.line_global, self.line_lr, self.line_noise, self.line_sync_drift] + self.lines + self.text_objects

# =====================================================================
# SYSTEM INITIALIZATION
# =====================================================================
if __name__ == "__main__":
    dashboard = OracleClusterDashboard(num_stacks=4)
    ani = animation.FuncAnimation(dashboard.fig, dashboard.update, frames=240,
                                  interval=42, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.close()
    display(HTML(ani.to_html5_video()))
          
