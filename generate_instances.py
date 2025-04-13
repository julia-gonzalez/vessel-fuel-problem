from problem_instance import ProblemInstance
import random
import os

def main():
    instances_folder = 'instances'
    os.makedirs(instances_folder, exist_ok=True)  # Ensure the output folder exists
    
    for i in range(1000):
        random.seed(i) 
        problem = ProblemInstance.generate()
        with open("instances/instance_%04d.json" % i, 'w') as file:
            file.write(problem.to_json())

if __name__ == "__main__":
    main()