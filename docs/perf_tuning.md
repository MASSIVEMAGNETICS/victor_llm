# Performance Tuning Guide

This document provides tips and guidance for optimizing Victor's performance on various hardware.

## CPU Optimization

Victor is designed to be efficient on CPU-only systems. The following sections detail CPU-specific optimizations.

### Intel oneAPI Acceleration (Optional)

For users with Intel hardware (CPUs with integrated GPUs), [Intel oneAPI](https://www.intel.com/content/www/us/en/developer/tools/oneapi/overview.html) provides a powerful toolchain for further performance enhancements.

-   **Data Parallel C++ (DPC++)**: DPC++ allows you to write SYCL code that can be compiled to run on Intel CPUs and Intel integrated GPUs. For certain NumPy operations or custom numerical kernels, DPC++ can offer significant acceleration by leveraging the integrated GPU. This can sometimes provide a near drop-in replacement or alternative for NumPy operations, pushing computations to the iGPU where beneficial.
-   **oneAPI Libraries**: Explore libraries like oneMKL (Math Kernel Library) and oneDNN (Deep Neural Network Library) which are optimized for Intel architectures and can speed up relevant computations within Victor if it were to use such operations more directly.

To leverage oneAPI:
1.  Install the relevant oneAPI toolkits from the Intel website.
2.  Follow Intel's documentation for compiling and running SYCL code or integrating oneAPI libraries.
3.  For `OmegaTensor` or other numerical hotspots, you might consider offloading specific computations to DPC++/SYCL if profiling indicates a bottleneck that maps well to GPU execution.

Note: Direct integration of oneAPI into the core Victor framework would require specific code changes to identify and offload compatible operations. This section serves as guidance for advanced users looking to extract maximum performance on Intel hardware.
