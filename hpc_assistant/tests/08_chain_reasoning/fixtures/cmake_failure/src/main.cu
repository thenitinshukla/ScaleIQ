#include <cuda_runtime.h>
#include <iostream>

__global__ void say_hello() {
    printf("Hello from GPU!\\n");
}

int main() {
    say_hello<<<1, 1>>>();
    cudaDeviceSynchronize();
    std::cout << "Completed GPU kernel" << std::endl;
    return 0;
}
