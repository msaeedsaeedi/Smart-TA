import os
import shutil
import zipfile
import subprocess
import re
import uuid
import json
import pty
import select
import termios
import tty
import sys
from typing import List, Dict
from datetime import datetime

class AssignmentEvaluator:
    def __init__(self, submissions_path: str, output_log_path: str):
        """
        Initialize the Assignment Evaluator
        
        :param submissions_path: Path to folder containing zipped student submissions
        :param output_log_path: Path to store evaluation logs
        """
        self.submissions_path = submissions_path
        self.output_log_path = output_log_path
        self.student_logs = {}
        
        # Validate and create paths
        os.makedirs(self.output_log_path, exist_ok=True)
        
        # Regex for validating roll number
        self.roll_number_pattern = re.compile(r'^[a-z]\d{6}$')
    
    def validate_roll_number(self, roll_number: str) -> bool:
        """
        Validate student roll number
        
        :param roll_number: Student's roll number
        :return: Boolean indicating validity
        """
        return bool(self.roll_number_pattern.match(roll_number))
    
    def extract_submission(self, zip_file_path: str, extraction_dir: str):
        """
        Safely extract submission zip
        
        :param zip_file_path: Path to zip file
        :param extraction_dir: Directory to extract files
        """
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Prevent zip bomb and path traversal
            for file in zip_ref.namelist():
                if file.startswith('__MACOSX/') or file.endswith('/'):
                    continue
                    
                # Extract files safely
                target_path = os.path.join(extraction_dir, os.path.basename(file))
                source = zip_ref.open(file)
                with open(target_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
                source.close()
    
    def compile_and_run_code(self, file_path: str, timeout: int = 300) -> Dict:
        """
        Compile and run submitted code in an interactive pseudo-terminal
        
        :param file_path: Path to source code file
        :param timeout: Maximum execution time in seconds
        :return: Compilation and execution results
        """
        # Unique sandbox directory
        sandbox_dir = os.path.join(
            self.output_log_path, 
            f'sandbox_{uuid.uuid4().hex}'
        )
        os.makedirs(sandbox_dir, exist_ok=True)
        
        try:
            # Copy file to sandbox
            shutil.copy(file_path, sandbox_dir)
            
            # Compile (for C/C++)
            if file_path.endswith(('.cpp', '.c')):
                compile_command = f'g++ -std=c++11 -o {sandbox_dir}/program {file_path}'
                compile_result = subprocess.run(
                    compile_command, 
                    shell=True, 
                    capture_output=True, 
                    text=True
                )
                
                if compile_result.returncode != 0:
                    print("Compilation Error:")
                    print(compile_result.stderr)
                    return {
                        'compiled': False,
                        'compile_error_summary': compile_result.stderr[:500]  # Truncate error message
                    }
                
                # Run compiled program using pseudo-terminal
                run_command = f'{sandbox_dir}/program'
            else:
                return {'error': 'Unsupported file type'}
            
            # Create a pseudo-terminal for interactive communication
            master, slave = pty.openpty()
            
            # Set raw mode on the slave terminal
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setraw(sys.stdin.fileno())
                
                # Start the process
                process = subprocess.Popen(
                    run_command, 
                    shell=True,
                    stdin=slave,
                    stdout=slave,
                    stderr=slave,
                    close_fds=True
                )
                
                # Close the slave descriptor
                os.close(slave)
                
                # Interaction and output capture
                output_summary = ""
                while True:
                    try:
                        # Wait for data or timeout
                        rlist, _, _ = select.select([master], [], [], timeout)
                        
                        if not rlist:
                            print("\nExecution timed out")
                            process.terminate()
                            break
                        
                        # Read available data
                        data = os.read(master, 1024)
                        if not data:
                            break

                        # Decode and print output
                        decoded_data = data.decode('utf-8', errors='replace')
                        print(decoded_data, end='', flush=True)
                        
                        # Limit output summary
                        output_summary += decoded_data
                        if len(output_summary) > 1000:
                            output_summary = output_summary[-1000:]
                        
                        # Check if user input is required
                        if select.select([sys.stdin], [], [], 0)[0]:
                            user_input = sys.stdin.read(1)
                            os.write(master, user_input.encode())
                    
                    except (OSError, ValueError):
                        break
                
                # Wait for process to complete
                process.wait(timeout=5)
                
                return {
                    'compiled': True,
                    'output_summary': output_summary,
                    'return_code': process.returncode
                }
            
            finally:
                # Restore terminal settings
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
        except Exception as e:
            print(f"Execution Error: {e}")
            return {'error': str(e)[:500]}  # Truncate error message
        
        finally:
            # Clean up sandbox
            shutil.rmtree(sandbox_dir, ignore_errors=True)
    
    def evaluate_submission(self, roll_number: str, question: str):
        """
        Evaluate submission for a specific student
        
        :param roll_number: Student's roll number
        :param question: Question to evaluate
        """
        if not self.validate_roll_number(roll_number):
            print(f"Invalid roll number: {roll_number}")
            return
        
        # Find student's zip file
        student_zip = None
        for file in os.listdir(self.submissions_path):
            if roll_number in file and file.endswith('.zip'):
                student_zip = os.path.join(self.submissions_path, file)
                break
        
        if not student_zip:
            print(f"No submission found for {roll_number}")
            return
        
        # Create temporary extraction directory
        temp_extract_dir = os.path.join(
            self.output_log_path, 
            f'extract_{roll_number}'
        )
        os.makedirs(temp_extract_dir, exist_ok=True)
        
        try:
            # Extract submission
            self.extract_submission(student_zip, temp_extract_dir)
            
            # Find matching file
            matching_files = [
                f for f in os.listdir(temp_extract_dir) 
                if f.startswith(f'Q{question}') and f.endswith(('.cpp', '.c'))
            ]
            
            if not matching_files:
                print(f"No file found for Q{question}")
                return
            
            # Run first matching file
            file_path = os.path.join(temp_extract_dir, matching_files[0])
            print(f"\n--- Evaluating Q{question} for {roll_number} ---")
            run_result = self.compile_and_run_code(file_path)
            
            # Initialize student log if not exists
            if roll_number not in self.student_logs:
                self.student_logs[roll_number] = {
                    'roll_number': roll_number,
                    'submissions': {},
                    'evaluated_at': datetime.now().isoformat()
                }
            
            # Log results for this question
            self.student_logs[roll_number]['submissions'][question] = {
                'timestamp': datetime.now().isoformat(),
                'status': self.determine_question_status(run_result),
                'details': {
                    k: v for k, v in run_result.items() 
                    if k not in ['output_summary']
                }
            }
            
            # Save comprehensive student log
            self.save_student_log(roll_number)
        
        except Exception as e:
            print(f"Evaluation Error: {e}")
        
        finally:
            # Clean up extracted files
            shutil.rmtree(temp_extract_dir, ignore_errors=True)
    
    def save_student_log(self, roll_number):
        """
        Save log for a specific student
        
        :param roll_number: Student's roll number
        """
        if roll_number in self.student_logs:
            log_path = os.path.join(
                self.output_log_path, 
                f'{roll_number}_evaluation_log.json'
            )
            with open(log_path, 'w') as f:
                json.dump(self.student_logs[roll_number], f, indent=2)
    
    def generate_summary_report(self):
        """
        Generate a comprehensive evaluation summary
        """
        # Aggregate status across all students
        summary = {
            'total_students': len(self.student_logs),
            'students_summary': {}
        }
        
        for roll_number, student_log in self.student_logs.items():
            student_status = self.determine_student_status(student_log)
            summary['students_summary'][roll_number] = {
                'overall_status': student_status,
                'total_questions': len(student_log['submissions'])
            }
        
        # Save summary report
        summary_path = os.path.join(
            self.output_log_path, 
            'evaluation_summary.json'
        )
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
    
    def determine_question_status(self, run_result):
        """
        Determine status of a single question
        
        :param run_result: Result of code execution
        :return: Status string
        """
        if not run_result.get('compiled', False):
            return 'failed_compilation'
        if run_result.get('error'):
            return 'runtime_error'
        return 'compiled_successfully'
    
    def determine_student_status(self, student_log):
        """
        Determine overall status for a student
        
        :param student_log: Log for a specific student
        :return: Overall status string
        """
        statuses = student_log['submissions'].values()
        
        # Check if any question failed compilation
        if any(status['status'] == 'failed_compilation' for status in statuses):
            return 'partial_submission'
        
        # Check if all questions compiled successfully
        if all(status['status'] == 'compiled_successfully' for status in statuses):
            return 'full_submission'
        
        return 'incomplete_submission'

def main():
    # Example usage
    evaluator = AssignmentEvaluator(
        submissions_path='./submissions',
        output_log_path='./logs'
    )
    
    while True:
        roll_number = input("Enter student roll number (or 'q' to exit): ")
    
        if roll_number.lower() == 'q':
            break

        # Interactive evaluation loop
        while True:
            question = input("Enter question number (or '-1' for next student): ")
            if question.lower() == '-1':
                break
            evaluator.evaluate_submission(roll_number, question)

        # Generate final summary
        summary = evaluator.generate_summary_report()
        print("Evaluation Summary:", json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()