# PlantGuard Performance Optimization Guide

## Overview

This guide provides comprehensive strategies for optimizing PlantGuard's training and inference performance. It covers hardware optimization, software configuration, data pipeline optimization, and model-specific improvements.

## Performance Benchmarks

### Baseline Performance Metrics

**Training Performance (ResNet50, PlantVillage dataset)**:
- **GPU (RTX 4090)**: ~45 seconds/epoch, 64 batch size
- **GPU (RTX 3080)**: ~75 seconds/epoch, 32 batch size  
- **Apple M2 Max (MPS)**: ~120 seconds/epoch, 32 batch size
- **CPU (16-core)**: ~15 minutes/epoch, 16 batch size

**Inference Performance**:
- **GPU**: ~5ms per image
- **Apple Silicon (MPS)**: ~15ms per image
- **CPU**: ~50ms per image

**Memory Usage**:
- **Training**: 8-12GB GPU memory (batch size 32-64)
- **Inference**: 2-4GB GPU memory
- **Dataset**: 15-20GB disk space (processed)

## Hardware Optimization

### GPU Optimization

#### NVIDIA GPU Configuration

```json
{
  "resources": {
    "device": "cuda",
    "mixed_precision": true,
    "compile_model": true,
    "channels_last": true,
    "cudnn_benchmark": true
  }
}
```

**Optimal Settings by GPU**:

```bash
# RTX 4090 (24GB VRAM)
{
  "training": {
    "batch_size": 128,
    "num_workers": 12,
    "pin_memory": true,
    "persistent_workers": true
  }
}

# RTX 3080 (10GB VRAM)  
{
  "training": {
    "batch_size": 64,
    "gradient_accumulation_steps": 2,
    "num_workers": 8
  }
}

# RTX 3060 (12GB VRAM)
{
  "training": {
    "batch_size": 32,
    "gradient_accumulation_steps": 4,
    "mixed_precision": true
  }
}
```

#### Apple Silicon (MPS) Optimization

```json
{
  "resources": {
    "device": "mps",
    "mixed_precision": false,  // Not supported on MPS
    "num_workers": 4,  // Limited by memory bandwidth
    "pin_memory": false  // Not beneficial on unified memory
  },
  "training": {
    "batch_size": 32,
    "gradient_accumulation_steps": 2
  }
}
```

**MPS-Specific Optimizations**:

```python
# Enable MPS fallback for unsupported operations
import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

# Optimize memory allocation
torch.mps.set_per_process_memory_fraction(0.8)
```

### CPU Optimization

For CPU-only training:

```json
{
  "resources": {
    "device": "cpu",
    "num_workers": 0,  // Avoid multiprocessing overhead
    "pin_memory": false
  },
  "training": {
    "batch_size": 8,
    "gradient_accumulation_steps": 8,
    "mixed_precision": false
  }
}
```

**CPU-Specific Settings**:

```bash
# Enable Intel MKL optimizations
export MKL_NUM_THREADS=8
export OMP_NUM_THREADS=8

# Use Intel Extension for PyTorch (if available)
pip install intel_extension_for_pytorch
```

### Memory Optimization

#### GPU Memory Management

```json
{
  "memory_optimization": {
    "gradient_checkpointing": true,
    "empty_cache_frequency": 10,
    "max_split_size_mb": 512,
    "memory_fraction": 0.9
  }
}
```

**Memory Monitoring**:

```python
# Real-time memory monitoring
def monitor_gpu_memory():
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        cached = torch.cuda.memory_reserved() / 1024**3
        print(f"GPU Memory - Allocated: {allocated:.2f}GB, Cached: {cached:.2f}GB")

# Memory cleanup
def cleanup_memory():
    torch.cuda.empty_cache()
    gc.collect()
```

#### Dynamic Batch Size Adjustment

```python
class AdaptiveBatchSize:
    def __init__(self, initial_batch_size=64, min_batch_size=8):
        self.batch_size = initial_batch_size
        self.min_batch_size = min_batch_size
    
    def adjust_batch_size(self, oom_occurred=False):
        if oom_occurred and self.batch_size > self.min_batch_size:
            self.batch_size = max(self.batch_size // 2, self.min_batch_size)
            return True
        return False
```

## Data Pipeline Optimization

### DataLoader Configuration

#### Optimal DataLoader Settings

```python
def create_optimized_dataloader(dataset, batch_size, num_workers=None):
    if num_workers is None:
        num_workers = min(8, os.cpu_count())
    
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        persistent_workers=True if num_workers > 0 else False,
        prefetch_factor=4 if num_workers > 0 else 2,
        drop_last=True  # For consistent batch sizes
    )
```

#### Data Loading Profiling

```python
def profile_dataloader(dataloader, num_batches=10):
    import time
    
    start_time = time.time()
    for i, (images, labels) in enumerate(dataloader):
        if i >= num_batches:
            break
        # Simulate processing time
        time.sleep(0.01)
    
    total_time = time.time() - start_time
    avg_time_per_batch = total_time / num_batches
    print(f"Average time per batch: {avg_time_per_batch:.3f}s")
```

### Image Preprocessing Optimization

#### Efficient Transforms

```python
# Optimized transform pipeline
def create_optimized_transforms(image_size=224):
    return transforms.Compose([
        transforms.Resize((image_size, image_size), antialias=True),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

# GPU-accelerated transforms (if available)
def create_gpu_transforms(device):
    return torch.nn.Sequential(
        transforms.Resize((224, 224), antialias=True),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ).to(device)
```

#### Data Augmentation Optimization

```python
# Efficient augmentation pipeline
class OptimizedAugmentation:
    def __init__(self, probability=0.5):
        self.augment = transforms.Compose([
            transforms.RandomHorizontalFlip(p=probability),
            transforms.RandomRotation(15),
            transforms.ColorJitter(
                brightness=0.2,
                contrast=0.2,
                saturation=0.2,
                hue=0.1
            ),
            transforms.RandomResizedCrop(224, scale=(0.8, 1.0))
        ])
    
    def __call__(self, image):
        return self.augment(image)
```

### Dataset Caching and Preprocessing

#### Memory-Mapped Datasets

```python
class MemoryMappedDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.samples = self._load_samples()
        
        # Pre-load small images into memory
        self.cache = {}
        self._preload_cache()
    
    def _preload_cache(self):
        # Cache frequently accessed or small images
        for idx, (path, label) in enumerate(self.samples[:1000]):  # Cache first 1000
            if path.stat().st_size < 1024 * 1024:  # < 1MB
                self.cache[idx] = Image.open(path).convert('RGB')
    
    def __getitem__(self, idx):
        if idx in self.cache:
            image = self.cache[idx]
        else:
            path, label = self.samples[idx]
            image = Image.open(path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        
        return image, label
```

## Model Optimization

### Model Architecture Optimization

#### Model Compilation (PyTorch 2.0+)

```python
def create_optimized_model(num_classes=38):
    model = models.resnet50(pretrained=True)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    
    # Compile model for optimization
    if hasattr(torch, 'compile'):
        model = torch.compile(
            model,
            mode='default',  # Options: 'default', 'reduce-overhead', 'max-autotune'
            fullgraph=True
        )
    
    return model
```

#### Channel-Last Memory Format

```python
# Optimize memory layout for better performance
def optimize_model_memory_format(model, device):
    model = model.to(device)
    if device.type == 'cuda':
        model = model.to(memory_format=torch.channels_last)
    return model

# Apply to inputs as well
def optimize_input_format(tensor, device):
    if device.type == 'cuda':
        return tensor.to(device, memory_format=torch.channels_last)
    return tensor.to(device)
```

#### Model Pruning

```python
import torch.nn.utils.prune as prune

def prune_model(model, pruning_ratio=0.2):
    """Apply structured pruning to reduce model size"""
    for name, module in model.named_modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            prune.l1_unstructured(module, name='weight', amount=pruning_ratio)
            prune.remove(module, 'weight')
    
    return model
```

### Training Loop Optimization

#### Optimized Training Loop

```python
class OptimizedTrainer:
    def __init__(self, model, device, use_amp=True):
        self.model = model
        self.device = device
        self.use_amp = use_amp
        self.scaler = torch.cuda.amp.GradScaler() if use_amp else None
    
    def train_epoch(self, dataloader, optimizer, criterion):
        self.model.train()
        total_loss = 0
        
        for batch_idx, (data, target) in enumerate(dataloader):
            data = optimize_input_format(data, self.device)
            target = target.to(self.device, non_blocking=True)
            
            optimizer.zero_grad(set_to_none=True)  # More efficient than zero_grad()
            
            if self.use_amp:
                with torch.cuda.amp.autocast():
                    output = self.model(data)
                    loss = criterion(output, target)
                
                self.scaler.scale(loss).backward()
                self.scaler.step(optimizer)
                self.scaler.update()
            else:
                output = self.model(data)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()
            
            total_loss += loss.item()
            
            # Memory cleanup every N batches
            if batch_idx % 50 == 0:
                torch.cuda.empty_cache()
        
        return total_loss / len(dataloader)
```

#### Gradient Accumulation

```python
def train_with_gradient_accumulation(model, dataloader, optimizer, criterion, 
                                   accumulation_steps=4):
    model.train()
    optimizer.zero_grad()
    
    for batch_idx, (data, target) in enumerate(dataloader):
        data, target = data.to(device), target.to(device)
        
        with torch.cuda.amp.autocast():
            output = model(data)
            loss = criterion(output, target) / accumulation_steps
        
        scaler.scale(loss).backward()
        
        if (batch_idx + 1) % accumulation_steps == 0:
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()
```

### Inference Optimization

#### Model Optimization for Inference

```python
def optimize_for_inference(model, example_input):
    """Optimize model for inference"""
    model.eval()
    
    # Convert to TorchScript
    traced_model = torch.jit.trace(model, example_input)
    
    # Optimize for inference
    traced_model = torch.jit.optimize_for_inference(traced_model)
    
    return traced_model

# Usage
example_input = torch.randn(1, 3, 224, 224).to(device)
optimized_model = optimize_for_inference(model, example_input)
```

#### Batch Inference Optimization

```python
class BatchInferenceOptimizer:
    def __init__(self, model, device, max_batch_size=32):
        self.model = model
        self.device = device
        self.max_batch_size = max_batch_size
    
    def predict_batch(self, images):
        """Optimize batch prediction"""
        self.model.eval()
        
        # Process in optimal batch sizes
        results = []
        for i in range(0, len(images), self.max_batch_size):
            batch = images[i:i + self.max_batch_size]
            batch_tensor = torch.stack(batch).to(self.device)
            
            with torch.no_grad(), torch.cuda.amp.autocast():
                outputs = self.model(batch_tensor)
                predictions = torch.softmax(outputs, dim=1)
            
            results.extend(predictions.cpu().numpy())
        
        return results
```

## Training Strategy Optimization

### Learning Rate Optimization

#### Learning Rate Scheduling

```python
def create_optimized_scheduler(optimizer, total_epochs):
    """Create optimized learning rate scheduler"""
    return torch.optim.lr_scheduler.OneCycleLR(
        optimizer,
        max_lr=0.01,
        total_steps=total_epochs,
        pct_start=0.1,  # 10% warmup
        anneal_strategy='cos',
        div_factor=25,
        final_div_factor=10000
    )
```

#### Learning Rate Finding

```python
class LRFinder:
    def __init__(self, model, optimizer, criterion, device):
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device
    
    def find_lr(self, dataloader, start_lr=1e-7, end_lr=10, num_iter=100):
        """Find optimal learning rate"""
        lrs = []
        losses = []
        
        lr_scheduler = torch.optim.lr_scheduler.ExponentialLR(
            self.optimizer, gamma=(end_lr/start_lr)**(1/num_iter)
        )
        
        self.model.train()
        for i, (data, target) in enumerate(dataloader):
            if i >= num_iter:
                break
            
            data, target = data.to(self.device), target.to(self.device)
            
            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.criterion(output, target)
            loss.backward()
            self.optimizer.step()
            lr_scheduler.step()
            
            lrs.append(self.optimizer.param_groups[0]['lr'])
            losses.append(loss.item())
        
        return lrs, losses
```

### Transfer Learning Optimization

#### Progressive Unfreezing

```python
class ProgressiveUnfreezing:
    def __init__(self, model, unfreeze_schedule):
        self.model = model
        self.unfreeze_schedule = unfreeze_schedule  # {epoch: layers_to_unfreeze}
        
    def update_frozen_layers(self, epoch):
        """Progressively unfreeze layers"""
        if epoch in self.unfreeze_schedule:
            layers_to_unfreeze = self.unfreeze_schedule[epoch]
            
            for name, param in self.model.named_parameters():
                if any(layer in name for layer in layers_to_unfreeze):
                    param.requires_grad = True
                    print(f"Unfroze layer: {name}")

# Usage
unfreeze_schedule = {
    0: ['classifier'],  # Unfreeze classifier first
    10: ['layer4'],     # Unfreeze last ResNet block
    20: ['layer3'],     # Unfreeze second-to-last block
    30: []              # Unfreeze all remaining layers
}
```

#### Discriminative Learning Rates

```python
def create_discriminative_optimizer(model, base_lr=0.001):
    """Create optimizer with different learning rates for different layers"""
    
    # Define layer groups with different learning rates
    layer_groups = [
        {'params': model.conv1.parameters(), 'lr': base_lr * 0.1},
        {'params': model.layer1.parameters(), 'lr': base_lr * 0.2},
        {'params': model.layer2.parameters(), 'lr': base_lr * 0.4},
        {'params': model.layer3.parameters(), 'lr': base_lr * 0.6},
        {'params': model.layer4.parameters(), 'lr': base_lr * 0.8},
        {'params': model.fc.parameters(), 'lr': base_lr}
    ]
    
    return torch.optim.AdamW(layer_groups, weight_decay=0.01)
```

## Monitoring and Profiling

### Performance Profiling

#### Training Profiler

```python
def profile_training(model, dataloader, num_batches=10):
    """Profile training performance"""
    from torch.profiler import profile, record_function, ProfilerActivity
    
    with profile(
        activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
        record_shapes=True,
        profile_memory=True,
        with_stack=True
    ) as prof:
        model.train()
        for batch_idx, (data, target) in enumerate(dataloader):
            if batch_idx >= num_batches:
                break
            
            with record_function("data_loading"):
                data, target = data.to(device), target.to(device)
            
            with record_function("forward_pass"):
                output = model(data)
            
            with record_function("loss_computation"):
                loss = criterion(output, target)
            
            with record_function("backward_pass"):
                loss.backward()
    
    # Print profiling results
    print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))
    
    # Export trace for visualization
    prof.export_chrome_trace("training_trace.json")
```

#### Memory Profiler

```python
def profile_memory_usage(model, input_size=(1, 3, 224, 224)):
    """Profile memory usage"""
    from torch.profiler import profile, ProfilerActivity
    
    dummy_input = torch.randn(input_size).to(device)
    
    with profile(
        activities=[ProfilerActivity.CUDA],
        profile_memory=True,
        record_shapes=True
    ) as prof:
        output = model(dummy_input)
        loss = output.sum()
        loss.backward()
    
    print(prof.key_averages().table(
        sort_by="self_cuda_memory_usage", 
        row_limit=10
    ))
```

### Real-time Monitoring

#### Performance Metrics Dashboard

```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'batch_times': [],
            'gpu_memory': [],
            'cpu_usage': [],
            'throughput': []
        }
    
    def log_batch_metrics(self, batch_time, batch_size):
        """Log metrics for each batch"""
        self.metrics['batch_times'].append(batch_time)
        self.metrics['throughput'].append(batch_size / batch_time)
        
        if torch.cuda.is_available():
            memory_used = torch.cuda.memory_allocated() / 1024**3
            self.metrics['gpu_memory'].append(memory_used)
        
        cpu_percent = psutil.cpu_percent()
        self.metrics['cpu_usage'].append(cpu_percent)
    
    def get_summary(self):
        """Get performance summary"""
        return {
            'avg_batch_time': np.mean(self.metrics['batch_times']),
            'avg_throughput': np.mean(self.metrics['throughput']),
            'max_gpu_memory': max(self.metrics['gpu_memory']) if self.metrics['gpu_memory'] else 0,
            'avg_cpu_usage': np.mean(self.metrics['cpu_usage'])
        }
```

## Configuration Templates

### High-Performance Training Configuration

```json
{
  "experiment": {
    "name": "high_performance_training",
    "description": "Optimized for maximum training speed"
  },
  "model": {
    "architecture": "resnet50",
    "compile": true,
    "channels_last": true
  },
  "training": {
    "epochs": 100,
    "batch_size": 128,
    "learning_rate": 0.01,
    "optimizer": "adamw",
    "scheduler": {
      "type": "onecycle",
      "max_lr": 0.01,
      "pct_start": 0.1
    }
  },
  "resources": {
    "device": "cuda",
    "mixed_precision": true,
    "num_workers": 12,
    "pin_memory": true,
    "persistent_workers": true,
    "prefetch_factor": 4
  },
  "optimization": {
    "gradient_checkpointing": false,
    "compile_model": true,
    "memory_efficient": false
  }
}
```

### Memory-Efficient Training Configuration

```json
{
  "experiment": {
    "name": "memory_efficient_training",
    "description": "Optimized for limited GPU memory"
  },
  "training": {
    "batch_size": 16,
    "gradient_accumulation_steps": 8,
    "learning_rate": 0.001
  },
  "resources": {
    "mixed_precision": true,
    "num_workers": 4,
    "pin_memory": true
  },
  "optimization": {
    "gradient_checkpointing": true,
    "empty_cache_frequency": 5,
    "memory_efficient": true,
    "max_split_size_mb": 256
  }
}
```

### Inference Optimization Configuration

```json
{
  "inference": {
    "batch_size": 32,
    "use_torchscript": true,
    "optimize_for_mobile": false,
    "quantization": {
      "enabled": false,
      "backend": "fbgemm"
    }
  },
  "resources": {
    "device": "cuda",
    "mixed_precision": true,
    "compile_model": true
  }
}
```

## Benchmarking and Testing

### Performance Benchmarking Script

```python
def benchmark_training_performance():
    """Comprehensive training performance benchmark"""
    
    # Test different batch sizes
    batch_sizes = [16, 32, 64, 128]
    results = {}
    
    for batch_size in batch_sizes:
        print(f"Benchmarking batch size: {batch_size}")
        
        # Create dataloader
        dataloader = create_optimized_dataloader(dataset, batch_size)
        
        # Benchmark training
        start_time = time.time()
        total_samples = 0
        
        for batch_idx, (data, target) in enumerate(dataloader):
            if batch_idx >= 50:  # Test 50 batches
                break
            
            data, target = data.to(device), target.to(device)
            
            # Simulate training step
            with torch.cuda.amp.autocast():
                output = model(data)
                loss = criterion(output, target)
            
            total_samples += data.size(0)
        
        elapsed_time = time.time() - start_time
        throughput = total_samples / elapsed_time
        
        results[batch_size] = {
            'throughput': throughput,
            'time_per_batch': elapsed_time / 50,
            'memory_usage': torch.cuda.max_memory_allocated() / 1024**3
        }
        
        torch.cuda.reset_peak_memory_stats()
    
    return results
```

### Automated Performance Testing

```bash
#!/bin/bash
# performance_test.sh

echo "Running PlantGuard Performance Tests..."

# Test different configurations
configs=("high_performance" "memory_efficient" "balanced")

for config in "${configs[@]}"; do
    echo "Testing configuration: $config"
    
    # Run training benchmark
    python -m src.training.benchmark \
        --config="config/${config}_config.json" \
        --duration=300 \
        --output="benchmarks/${config}_results.json"
    
    # Run inference benchmark
    python -m src.core.inference_benchmark \
        --config="config/${config}_config.json" \
        --samples=1000 \
        --output="benchmarks/${config}_inference.json"
done

# Generate performance report
python -m src.utils.performance_report \
    --input="benchmarks/" \
    --output="performance_report.html"
```

## Best Practices Summary

### Training Optimization Checklist

- [ ] **Hardware**: Use GPU with sufficient VRAM, enable mixed precision
- [ ] **Data Loading**: Optimize num_workers, enable pin_memory and persistent_workers
- [ ] **Model**: Enable model compilation (PyTorch 2.0+), use channels_last format
- [ ] **Memory**: Use gradient accumulation for large effective batch sizes
- [ ] **Learning Rate**: Use learning rate scheduling and warmup
- [ ] **Monitoring**: Profile training to identify bottlenecks

### Inference Optimization Checklist

- [ ] **Model Format**: Convert to TorchScript or ONNX for production
- [ ] **Batch Processing**: Process multiple images together when possible
- [ ] **Memory Management**: Use torch.no_grad() and clear cache regularly
- [ ] **Hardware**: Ensure GPU inference is enabled
- [ ] **Preprocessing**: Optimize image preprocessing pipeline

### General Performance Tips

1. **Start with Profiling**: Always profile before optimizing
2. **Optimize Data Loading First**: Often the biggest bottleneck
3. **Use Mixed Precision**: Significant speedup with minimal accuracy loss
4. **Monitor Memory Usage**: Prevent OOM errors and optimize batch sizes
5. **Regular Benchmarking**: Track performance improvements over time
6. **Hardware-Specific Tuning**: Optimize for your specific hardware setup

This performance optimization guide provides comprehensive strategies for maximizing PlantGuard's training and inference performance across different hardware configurations and use cases.