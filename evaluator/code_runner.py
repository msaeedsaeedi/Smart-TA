import os
import sys
import pty
import select
import termios
import tty
import uuid
import shutil
import subprocess
from typing import Dict

class CodeRunner:
    def __init__(self, output_log_path: str):
        """
        Initialize the Code Runner
        
        :param output_log_path: Path to store temporary files and logs
        """
        self.output_log_path = output_log_path
    
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
            
            return self._run_in_pty(run_command, timeout)
        
        except Exception as e:
            print(f"Execution Error: {e}")
            return {'error': str(e)[:500]}  # Truncate error message
        
        finally:
            # Clean up sandbox
            shutil.rmtree(sandbox_dir, ignore_errors=True)
    
    def _run_in_pty(self, command: str, timeout: int) -> Dict:
        """
        Run a command in a pseudo-terminal
        
        :param command: Command to run
        :param timeout: Maximum execution time in seconds
        :return: Execution results
        """
        # Create a pseudo-terminal for interactive communication
        master, slave = pty.openpty()
        
        # Save original terminal settings
        old_stdin_settings = termios.tcgetattr(sys.stdin)
        
        try:
            # Print a clear boundary before execution
            boundary_line = "=" * 60
            print(f"\n{boundary_line}")
            print(" PROGRAM EXECUTION START ".center(60, "="))
            print(f"{boundary_line}\n")
            
            # Start the process
            process = subprocess.Popen(
                command, 
                shell=True,
                stdin=slave,
                stdout=slave,
                stderr=slave,
                close_fds=True
            )
            
            # Close the slave descriptor
            os.close(slave)
            
            # Set stdin to non-blocking mode
            tty.setraw(sys.stdin.fileno())
            
            # Interaction and output capture
            output_summary = ""
            running = True
            
            while running:
                # Wait for data from either the process or user input
                rlist, _, _ = select.select([master, sys.stdin], [], [], timeout)
                
                if not rlist:
                    print("\nExecution timed out")
                    process.terminate()
                    break
                
                for ready_fd in rlist:
                    if ready_fd == master:
                        # Process output available
                        try:
                            data = os.read(master, 1024)
                            if not data:
                                running = False
                                break
                                
                            # Decode and print output
                            decoded_data = data.decode('utf-8', errors='replace')
                            print(decoded_data, end='', flush=True)
                            
                            # Limit output summary
                            output_summary += decoded_data
                            if len(output_summary) > 1000:
                                output_summary = output_summary[-1000:]
                        except (OSError, ValueError):
                            running = False
                            break
                    
                    elif ready_fd == sys.stdin:
                        # User input available
                        try:
                            user_input = os.read(sys.stdin.fileno(), 1)
                            os.write(master, user_input)
                        except (OSError, ValueError):
                            pass
            
            # Check if process is still running
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_stdin_settings)
            
            # Print a clear boundary after execution
            print(f"\n{boundary_line}")
            print(" PROGRAM EXECUTION END ".center(60, "="))
            print(f"{boundary_line}\n")
            
            return {
                'compiled': True,
                'output_summary': output_summary,
                'return_code': process.returncode
            }
        
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_stdin_settings)