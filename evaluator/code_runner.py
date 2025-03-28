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
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel

class CodeRunner:
    def __init__(self, output_log_path: str):
        """
        Initialize the Code Runner
        
        :param output_log_path: Path to store temporary files and logs
        """
        self.output_log_path = output_log_path
        # Create a rich console with custom theme
        custom_theme = Theme({
            "info": "cyan",
            "warning": "yellow",
            "error": "bold red",
            "success": "bold green",
            "boundary": "blue",
            "execution": "bold white"
        })
        self.console = Console(theme=custom_theme)
    
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
                    self.console.print(Panel(
                        f"[bold red]✗ Compilation Error[/bold red]",
                        border_style="red",
                    ))
                    self.console.print(compile_result.stderr, style="error")
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
            self.console.print(f"Execution Error: {e}", style="error")
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
            self.console.rule(style="boundary")
            self.console.print(" PROGRAM EXECUTION START ", style="execution", justify="center")
            self.console.rule(style="boundary")
            
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
                try:
                    rlist, _, _ = select.select([master, sys.stdin], [], [], timeout)
                    
                    if not rlist:
                        self.console.print("\nExecution timed out", style="warning")
                        output_summary += "\n[SYSTEM] Execution timed out after {} seconds".format(timeout)
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
                                print(decoded_data, end='', flush=True)  # Keep this as is for real-time output
                                
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
                                # Check for Ctrl+C (ASCII value 3)
                                if user_input == b'\x03':
                                    self.console.print("\n[SYSTEM] Execution stopped by user (Ctrl+C)", style="warning")
                                    output_summary += "\n[SYSTEM] Execution stopped by user (Ctrl+C)"
                                    running = False
                                    break
                                os.write(master, user_input)
                            except (OSError, ValueError):
                                pass
                                
                except KeyboardInterrupt:
                    self.console.print("\n[SYSTEM] Execution stopped by user (KeyboardInterrupt)", style="warning")
                    output_summary += "\n[SYSTEM] Execution stopped by user (KeyboardInterrupt)"
                    running = False
            
            # Check if process is still running
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    output_summary += "\n[SYSTEM] Process had to be forcibly terminated"
            
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_stdin_settings)
            
            # Print a clear boundary after execution
            self.console.line(1)
            self.console.rule(style="boundary")
            self.console.print(" PROGRAM EXECUTION END ", style="execution", justify="center")
            self.console.rule(style="boundary")
            
            execution_status = "Completed" if process.returncode == 0 else f"Terminated with code {process.returncode}"
            status_style = "success" if process.returncode == 0 else "error"
            self.console.print(Panel(
                f"[{status_style}]Execution status: {execution_status}[/{status_style}]",
                border_style=("green" if process.returncode == 0 else "red"),
                title="System"
            ))
            return {
                'compiled': True,
                'output_summary': output_summary,
                'return_code': process.returncode,
                'execution_status': execution_status
            }
        
        except Exception as e:
            self.console.print(f"\n[SYSTEM ERROR] {str(e)}", style="error")
            return {
                'compiled': True,
                'output_summary': f"[SYSTEM ERROR] Unexpected error during execution: {str(e)}",
                'return_code': -1,
                'execution_status': 'System Error'
            }
            
        finally:
            # Always restore terminal settings
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_stdin_settings)
            except:
                pass
            
            # Close file descriptors
            try:
                os.close(master)
            except:
                pass