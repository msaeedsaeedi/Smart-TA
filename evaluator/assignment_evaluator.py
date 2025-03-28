import json
import os
import re
import shutil
from typing import Dict
from datetime import datetime
from rich.prompt import Prompt
from rich.console import Console

from utils.file_utils import find_student_zip
from evaluator.submission_processor import SubmissionProcessor
from evaluator.code_runner import CodeRunner

class AssignmentEvaluator:
    def __init__(self, submissions_path, output_log_path):
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
        
        # Initialize components
        self.submission_processor = SubmissionProcessor()
        self.code_runner = CodeRunner(self.output_log_path)
        self.console = Console()

    def validate_roll_number(self, roll_number: str) -> bool:
        """
        Validate student roll number
        
        :param roll_number: Student's roll number
        :return: Boolean indicating validity
        """
        return bool(self.roll_number_pattern.match(roll_number))
    
    def find_student_zip(self, roll_number: str) -> str:
        """
        Find the zip file for a student's submission
        
        :param roll_number: Student's roll number
        :return: Path to zip file or None if not found
        """
        return find_student_zip(self.submissions_path, roll_number)

    def evaluate_submission(self, roll_number: str, question: str):
        """
        Evaluate submission for a specific student
        
        :param roll_number: Student's roll number
        :param question: Question to evaluate
        """
        student_zip = self.find_student_zip(roll_number)
        try:
            self.submission_processor.extract_submission(student_zip, self.output_log_path)

            # Find matching file
            matching_files = [
                f for f in os.listdir(os.path.join(self.output_log_path, roll_number)) 
                if f.startswith(f'Q{question}') and f.endswith(('.cpp', '.c'))
            ]

            if not matching_files:
                raise FileNotFoundError(f"No matching file found for question {question} in {student_zip}")

            # Process the submission
            file_path = os.path.join(self.output_log_path, roll_number, matching_files[0])
            run_result = self.code_runner.compile_and_run_code(file_path)

            # Ask for evaluation
            while True:
                marks = Prompt.ask("[bold blue]Enter marks [/bold blue]")
                try:
                    float_marks = float(marks)
                    if float_marks >= 0:
                        break
                    self.console.print("[bold red]Marks must be non-negative[/bold red]")
                except ValueError:
                    self.console.print("[bold red]Please enter a valid number[/bold red]")
            
            # Ask for feedback
            feedback = Prompt.ask(
                "[bold cyan]Additional feedback (optional)[/bold cyan]",
                default=""
            )
            
            # Log the results
            self._log_evaluation_result(roll_number, question, run_result, marks, feedback)
            self.console.print(f"[bold green]✓ Marks ({marks}) and feedback saved[/bold green]")

        except Exception as e:
            raise Exception(f"(Evaluation Error) {e}")
        
        finally:
            shutil.rmtree(os.path.join(self.output_log_path, roll_number), ignore_errors=True)

    def _log_evaluation_result(self, roll_number: str, question: str, run_result: Dict, marks: str, feedback: str):
        """
        Log the results of an evaluation
        
        :param roll_number: Student's roll number
        :param question: Question being evaluated
        :param run_result: Result of running the code
        :param marks: Marks awarded
        :param feedback: Additional feedback
        """
        # Initialize student log if not exists
        if roll_number not in self.student_logs:
            self.student_logs[roll_number] = {
                'roll_number': roll_number,
                'submissions': {},
            }
        
        # Log results for this question
        self.student_logs[roll_number]['submissions'][question] = {
            'timestamp': datetime.now().isoformat(),
            'details': {
                k: v for k, v in run_result.items() 
                if k not in ['output_summary']
            },
            'marks': marks,
            'feedback': feedback,
        }
        
        # Save comprehensive student log
        self.save_student_log(roll_number)
        
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
    