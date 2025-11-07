"""
Custom callbacks and utilities for pole tracker training.
"""

import json
import os
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import keras


class MetricsLoggerCallback(keras.callbacks.Callback):
    """
    Custom callback that saves training metrics to JSON and generates plots.
    
    This callback helps preserve training progress in case of disconnection by:
    - Saving all metrics to a JSON file after each epoch
    - Generating and updating a plot of metrics over time
    - Creating a dedicated output directory for all training artifacts
    
    Parameters
    ----------
    output_dir : str or Path
        Directory where metrics and plots will be saved
    metrics_filename : str, optional
        Name of the JSON file to save metrics (default: 'training_metrics.json')
    plot_filename : str, optional
        Name of the plot file (default: 'training_progress.png')
    """
    
    def __init__(self, output_dir, metrics_filename='training_metrics.json', 
                 plot_filename='training_progress.png'):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.metrics_filename = metrics_filename
        self.plot_filename = plot_filename
        self.metrics_path = self.output_dir / self.metrics_filename
        self.plot_path = self.output_dir / self.plot_filename
        self.history = {}
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def on_train_begin(self, logs=None):
        """Initialize or load existing metrics at the start of training."""
        # Try to load existing metrics if resuming training
        if self.metrics_path.exists():
            with open(self.metrics_path, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = {}
    
    def on_epoch_end(self, epoch, logs=None):
        """Save metrics and update plot after each epoch."""
        logs = logs or {}
        
        # Update history with current epoch metrics
        for key, value in logs.items():
            if key not in self.history:
                self.history[key] = []
            # Convert numpy types to Python native types for JSON serialization
            if hasattr(value, 'item'):
                value = value.item()
            self.history[key].append(float(value))
        
        # Save metrics to JSON
        self._save_metrics()
        
        # Update plot
        self._update_plot()
    
    def _save_metrics(self):
        """Save current metrics history to JSON file."""
        with open(self.metrics_path, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def _update_plot(self):
        """Generate and save an updated plot of training metrics."""
        if not self.history:
            return
        
        # Determine number of metrics to plot
        metric_keys = list(self.history.keys())
        n_metrics = len(metric_keys)
        
        if n_metrics == 0:
            return
        
        # Create figure with subplots
        fig, axes = plt.subplots(n_metrics, 1, figsize=(10, 4 * n_metrics))
        
        # Handle single metric case
        if n_metrics == 1:
            axes = [axes]
        
        # Plot each metric
        for idx, key in enumerate(metric_keys):
            ax = axes[idx]
            epochs = range(1, len(self.history[key]) + 1)
            ax.plot(epochs, self.history[key], 'b-', linewidth=2, label=key)
            ax.set_xlabel('Epoch')
            ax.set_ylabel(key.replace('_', ' ').title())
            ax.set_title(f'{key.replace("_", " ").title()} over Epochs')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # Add best value annotation for loss metrics
            if 'loss' in key.lower():
                best_epoch = self.history[key].index(min(self.history[key])) + 1
                best_value = min(self.history[key])
                ax.axvline(x=best_epoch, color='r', linestyle='--', alpha=0.5, 
                          label=f'Best: {best_value:.4f} @ epoch {best_epoch}')
                ax.legend()
        
        plt.tight_layout()
        plt.savefig(self.plot_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
