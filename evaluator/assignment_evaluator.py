import json
import os
import re
import shutil
from typing import Dict, List, Tuple
from datetime import datetime
from rich.prompt import Prompt, Confirm
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from utils.file_utils import find_student_zip
from utils.config_handler import ConfigHandler
from evaluator.submission_processor import SubmissionProcessor
from evaluator.code_runner import CodeRunner

class AssignmentEvaluator:
    def __init__(self, submissions_path, output_log_path, config_path="config.json"):
        """
        Initialize the Assignment Evaluator
        
        :param submissions_path: Path to folder containing zipped student submissions
        :param output_log_path: Path to store evaluation logs
        :param config_path: Path to the configuration file
        """
        self.submissions_path = submissions_path
        self.output_log_path = output_log_path
        self.student_logs = {}

        # Validate and create paths
        os.makedirs(self.output_log_path, exist_ok=True)
        
        # Initialize configuration handler
        self.config_handler = ConfigHandler(config_path)
        
        # Use regex pattern from config for roll number validation
        roll_number_pattern = self.config_handler.config.get("Submission Guidelines", {}).get("File Name", "^[a-z]\\d{6}$")
        self.roll_number_pattern = re.compile(roll_number_pattern)
        
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
        return self.config_handler.validate_roll_number_format(roll_number)
    
    def find_student_zip(self, roll_number: str) -> str:
        """
        Find the zip file for a student's submission
        
        :param roll_number: Student's roll number
        :return: Path to zip file or None if not found
        """
        zip_file = find_student_zip(self.submissions_path, roll_number)
        if zip_file and not self.config_handler.validate_file_format(zip_file):
            self.console.print(f"[bold yellow]Warning:[/bold yellow] Submission file '{os.path.basename(zip_file)}' does not match required format '{self.config_handler.config.get('Submission Guidelines', {}).get('Format', 'ZIP')}'")
        return zip_file

    def evaluate_submission(self, roll_number: str, question: str = None):
        """
        Evaluate submission for a specific student
        
        :param roll_number: Student's roll number
        :param question: Specific question to evaluate (or None for all questions)
        """
        student_zip = self.find_student_zip(roll_number)
        if not student_zip:
            self.console.print(f"[bold red]No submission ZIP found for {roll_number}[/bold red]")
            return
            
        # Extract the submission
        try:
            extraction_dir = os.path.join(self.output_log_path, roll_number)
            self.submission_processor.extract_submission(student_zip, self.output_log_path)
            
            # Get all configured questions
            marks_distribution = self.config_handler.get_marks_distribution()
            question_keys = []
            
            for key in marks_distribution.keys():
                # Extract question number from "Question X" format
                if key.startswith("Question "):
                    q_num = key.split(" ")[1]
                    question_keys.append(q_num)
                else:
                    # If it's already just the question number
                    question_keys.append(key)
            
            # If a specific question is provided, only evaluate that one
            if question:
                if question in question_keys:
                    self._evaluate_single_question(roll_number, question, extraction_dir)
                else:
                    self.console.print(f"[bold red]Question {question} is not defined in the marks distribution[/bold red]")
            else:
                # Evaluate all questions
                self.console.print(Panel(
                    f"Evaluating submission for [bold]{roll_number}[/bold]",
                    border_style="cyan"
                ))
                
                for q_num in question_keys:
                    self._evaluate_single_question(roll_number, q_num, extraction_dir)

        except Exception as e:
            self.console.print(f"[bold red]Evaluation Error: {str(e)}[/bold red]")
            
        finally:
            # Clean up extracted files
            shutil.rmtree(extraction_dir, ignore_errors=True)

    def _evaluate_single_question(self, roll_number: str, question: str, extraction_dir: str):
        """
        Evaluate a single question for a student
        
        :param roll_number: Student's roll number
        :param question: Question number to evaluate
        :param extraction_dir: Directory with extracted files
        """
        # Validate question number against config
        valid, max_marks = self.config_handler.validate_question_number(question)
        if not valid:
            self.console.print(f"[bold red]Question {question} is not defined in the marks distribution[/bold red]")
            return
            
        # Find matching file
        matching_files = [
            f for f in os.listdir(extraction_dir) 
            if f.startswith(f'Q{question}') and f.endswith(('.cpp', '.c'))
        ]

        if not matching_files:
            self.console.print(Panel(
                f"No submission file found for Question {question}",
                title="[bold yellow]Missing Submission[/bold yellow]",
                border_style="yellow"
            ))
            
            # Mark as missing with 0 marks
            if Confirm.ask(
                f"[yellow]Would you like to mark Question {question} as missing (0/{max_marks} marks)?[/yellow]",
                default=True
            ):
                self._log_evaluation_result(
                    roll_number, 
                    question, 
                    {'compiled': False, 'missing': True}, 
                    0, 
                    "Question not attempted"
                )
            self.console.print(
                f"[bold green]✓[/bold green] [yellow]Question {question} has been marked as missing[/yellow]"
            )
            return

        # Process the submission
        file_path = os.path.join(extraction_dir, matching_files[0])
        self.console.print(f"[bold blue]Evaluating Question {question}[/bold blue] - File: {matching_files[0]}")
        
        run_result = self.code_runner.compile_and_run_code(file_path)

        # Ask for evaluation
        while True:
            marks = Prompt.ask(f"[bold blue]Enter marks (0-{max_marks}) [/bold blue]")
            try:
                float_marks = float(marks)
                if 0 <= float_marks <= max_marks:
                    break
                self.console.print(f"[bold red]Marks must be between 0 and {max_marks}[/bold red]")
            except ValueError:
                self.console.print("[bold red]Please enter a valid number[/bold red]")
        
        # Ask for feedback
        feedback = Prompt.ask(
            "[bold cyan]Additional feedback (optional)[/bold cyan]",
            default=""
        )
        
        # Log the results
        self._log_evaluation_result(
            roll_number, 
            question, 
            run_result, 
            float_marks, 
            feedback,
        )
        self.console.print(f"[bold green]✓ Question {question}: Marks ({float_marks}/{max_marks}) and feedback saved[/bold green]")

    def _log_evaluation_result(self, roll_number: str, question: str, 
                              run_result: Dict, marks: float, feedback: str):
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
                'assignment': self.config_handler.get_assignment_name(),
                'evaluator': self.config_handler.get_evaluator_name(),
                'submissions': {},
            }
        
        # Log results for this question
        self.student_logs[roll_number]['submissions'][question] = {
            'timestamp': datetime.now().isoformat(),
            'details': {
                k: v for k, v in run_result.items() 
                if k not in ['output_summary']
            },
            'max_marks': self.config_handler.validate_question_number(question)[1],
            'awarded_marks': marks,
            'feedback': feedback
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