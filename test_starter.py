import subprocess

# divide total time / total requests | avg latency for the game per interaction
# avg those values to get average latency of all clients

# total throughput = total requests / total time, add them all up to get total throughput

import sys
import subprocess

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Please give us a number of cilents")
    
    server_name = sys.argv[1]
    num_clients = int(sys.argv[2])

    with open(f'output.txt', 'a') as output_file:
        output_file.write(f'{num_clients} clients\n')
        output_file.write(f'total_time, total_requests\n')
        output_file.write('--------\n')

    processes = []
    for _ in range(num_clients):
        process = subprocess.Popen(["python3", "test.py", server_name])  # Launch a process
        processes.append(process)
    
    for process in processes:
        process.wait()  # Wait for all processes to complete
